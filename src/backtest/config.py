"""YAML/JSON grid helpers and backtest config finalization (mainline, no archive imports)."""

from __future__ import annotations

import itertools
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from src.strategies.loader import (
    apply_overrides,
    deep_update,
    expand_grid,
    get_nested,
    load_strategy,
    load_strategy_config,
    set_nested,
)


def load_yaml_or_json(path: str | Path) -> Any:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    suf = p.suffix.lower()
    if suf in (".json",):
        return json.loads(text)
    return yaml.safe_load(text)


def merge_strategy_config(
    strategy_name: str,
    config_path: str | Path | None,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load base YAML/JSON from path or ``parameters/<strategy>.yaml``, then ``deep_update`` overrides."""
    if config_path:
        p = Path(config_path)
        raw = load_yaml_or_json(p)
        if not isinstance(raw, dict):
            raise ValueError(f"config file {p} must contain a JSON/YAML object")
        cfg = deepcopy(raw)
    else:
        cfg = load_strategy_config(strategy_name)
    if overrides:
        cfg = deep_update(cfg, dict(overrides))
    sid = cfg.get("strategy")
    if sid is not None and str(sid) != str(strategy_name):
        raise ValueError(f"config strategy={sid!r} does not match strategy {strategy_name!r}")
    if "strategy" not in cfg:
        cfg = deepcopy(cfg)
        cfg["strategy"] = strategy_name
    return cfg


def load_grid_document(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    raw = load_yaml_or_json(p)
    if not isinstance(raw, dict):
        raise ValueError(f"grid file {p} must contain a JSON/YAML object at root")
    return raw


def grid_combos_from_document(doc: dict[str, Any]) -> list[dict[str, Any]]:
    if "grid" in doc and isinstance(doc["grid"], dict):
        return expand_grid({"grid": doc["grid"]})
    inner = {k: v for k, v in doc.items() if k not in ("strategy", "notes", "description")}
    if not inner:
        return [{}]
    keys = list(inner.keys())
    vals: list[list[Any]] = []
    for k in keys:
        v = inner[k]
        if isinstance(v, (list, tuple)):
            vals.append(list(v))
        else:
            vals.append([v])
    return [dict(zip(keys, combo)) for combo in itertools.product(*vals)]


def apply_combo_overrides(base_cfg: dict[str, Any], combo: dict[str, Any]) -> dict[str, Any]:
    return apply_overrides(base_cfg, combo)


def finalize_backtest_config(cfg: dict[str, Any]) -> None:
    """In-place defaults so strategies that expect ORB-derived entry start stay consistent."""
    est = get_nested(cfg, "signal.entry_start_minute")
    if est is None:
        orb_m = int(get_nested(cfg, "features.orb_open_minutes", 15))
        set_nested(cfg, "signal.entry_start_minute", orb_m)


def _flatten_config_section(prefix: str, obj: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if not isinstance(obj, dict):
        return out
    for k, v in obj.items():
        key = f"{prefix}.{k}"
        if isinstance(v, dict):
            out.update(_flatten_config_section(key, v))
        elif isinstance(v, (list, tuple)):
            out[key] = json.dumps(list(v), default=str)
        elif isinstance(v, set):
            out[key] = json.dumps(sorted(v, key=str), default=str)
        else:
            out[key] = v
    return out


def flatten_grid_document(doc: dict[str, Any]) -> dict[str, Any]:
    """Flatten features/signal/risk/backtest sections to dotted keys (for manifests)."""
    out: dict[str, Any] = {}
    for section in ("features", "signal", "risk", "backtest"):
        out.update(_flatten_config_section(section, doc.get(section) or {}))
    return out


def validate_grid_document(strategy: str, testing: dict[str, Any]) -> None:
    """Validate every combo from a testing_parameters-style document."""
    validate_testing_grid_for_strategy(strategy, testing)


def validate_testing_grid_for_strategy(strategy: str, testing: dict[str, Any]) -> None:
    strat = load_strategy(strategy)
    base = load_strategy_config(strategy)
    grid_list = expand_grid(testing)
    fixed = testing.get("fixed") or {}
    for i, combo_flat in enumerate(grid_list):
        cfg = apply_overrides(base, combo_flat)
        cfg = apply_overrides(cfg, fixed)
        finalize_backtest_config(cfg)
        try:
            strat.validate_config(cfg)
        except Exception as e:
            raise ValueError(f"{strategy} testing grid combo[{i}] {combo_flat!r}: {e}") from e


def load_testing_yaml(path: Path, *, expected_strategy: str) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"invalid testing YAML: {path}")
    gs = data.get("strategy")
    if gs != expected_strategy:
        raise ValueError(
            f"testing YAML strategy field is {gs!r}, expected {expected_strategy!r} ({path})"
        )
    return data


def sweep_metrics_row(
    *,
    strategy: str,
    asset: str,
    symbol: str | None,
    root: str | None,
    contract: str | None,
    start: str,
    end: str,
    cfg: dict[str, Any],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    flat_params = flatten_grid_document(cfg)
    row: dict[str, Any] = {
        "strategy": strategy,
        "asset": asset,
        "symbol": symbol or "",
        "root": root or "",
        "contract": contract or "",
        "start": start,
        "end": end,
        "params_json": json.dumps(flat_params, default=str, sort_keys=True),
    }
    row.update(flat_params)
    row.update(metrics)
    return row
