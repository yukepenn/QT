"""Bridge bars → features → strategy signals → standard ``sig_*`` (no accounting).

PnL lives in ``src.execution`` via :func:`src.backtest.engine.run_strategy_backtest`.
This module only orchestrates loads, feature builds, and signal normalization.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

import pandas as pd
import yaml

from src.backtest.signal_adapter import (
    assert_canonical_signal_frame,
    canonicalize_signal_frame,
    infer_signal_mapping,
)
from src.data.read_bars import read_bars
from src.features.feature_key import build_features_from_config, feature_key_from_config
from src.strategies.loader import (
    apply_overrides,
    deep_update,
    expand_grid,
    get_nested,
    load_strategy,
    load_strategy_config,
    set_nested,
)

STANDARD_SIGNAL_CONTRACT_VERSION = "standard_sig_v1"

_TESTING_DOC_RESERVED_TOP_KEYS = frozenset({"strategy", "notes", "description", "fixed", "grid"})


def normalize_override_mapping(obj: Any, *, prefix: str = "") -> dict[str, Any]:
    """Flatten nested override dicts to dotted keys for :func:`apply_overrides`.

    - Nested dicts become ``section.subkey`` paths.
    - Lists, tuples, scalars, and ``None`` are leaves (not expanded into index keys).
    - Keys that already contain ``.`` are still valid leaf paths when the value is not
      a non-empty dict (YAML may use ``risk.min_risk_per_share: 0.03`` at a nesting level).
    """
    if obj is None:
        return {}
    if not isinstance(obj, dict):
        raise TypeError(f"override mapping must be a dict, got {type(obj).__name__}")
    out: dict[str, Any] = {}
    for k, v in obj.items():
        if not isinstance(k, str):
            raise TypeError(f"override keys must be str, got {type(k).__name__}")
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict) and v and "." not in k:
            out.update(normalize_override_mapping(v, prefix=path))
        elif isinstance(v, dict) and not v:
            continue
        elif isinstance(v, dict) and "." in k:
            raise ValueError(f"cannot nest dict under dotted key {path!r}; use nested mapping or a flat key")
        else:
            out[path] = v
    return out


def _overlap_error(fixed_keys: set[str], grid_keys: set[str]) -> ValueError:
    inter = sorted(fixed_keys & grid_keys)
    return ValueError(f"testing YAML `fixed` and `grid` both set keys {inter!r}; keys must be disjoint")


def grid_combos_from_document(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolved override combos: ``base + fixed + one grid branch`` per row.

    Contract:
    - ``fixed:`` is merged into every combo first (dotted keys).
    - ``grid:`` expands a Cartesian product; each branch must not overlap ``fixed`` keys.
    - Legacy top-level lists (excluding reserved keys) are still supported when no
      ``grid:`` section exists.
    - If only ``fixed`` is present, returns a single combo.
    - If neither ``fixed`` nor grid content exists, returns ``[{}]``.
    """
    fixed_flat = normalize_override_mapping(doc.get("fixed") or {})

    if "grid" in doc and isinstance(doc["grid"], dict):
        grid_branches = expand_grid({"grid": doc["grid"]})
        if not grid_branches:
            return [dict(fixed_flat)] if fixed_flat else [{}]
        merged: list[dict[str, Any]] = []
        for combo in grid_branches:
            gkeys = set(combo.keys())
            if gkeys & set(fixed_flat.keys()):
                raise _overlap_error(set(fixed_flat.keys()), gkeys)
            row = dict(fixed_flat)
            row.update(combo)
            merged.append(row)
        return merged

    inner = {k: v for k, v in doc.items() if k not in _TESTING_DOC_RESERVED_TOP_KEYS}
    if not inner:
        return [dict(fixed_flat)] if fixed_flat else [{}]

    keys = list(inner.keys())
    vals: list[list[Any]] = []
    for k in keys:
        v = inner[k]
        if isinstance(v, (list, tuple)):
            vals.append(list(v))
        else:
            vals.append([v])
    merged_legacy: list[dict[str, Any]] = []
    for combo in itertools.product(*vals):
        grid_row = dict(zip(keys, combo))
        gkeys = set(grid_row.keys())
        if gkeys & set(fixed_flat.keys()):
            raise _overlap_error(set(fixed_flat.keys()), gkeys)
        row = dict(fixed_flat)
        row.update(grid_row)
        merged_legacy.append(row)
    return merged_legacy


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


load_strategy_config_merged = merge_strategy_config


def load_grid_document(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    raw = load_yaml_or_json(p)
    if not isinstance(raw, dict):
        raise ValueError(f"grid file {p} must contain a JSON/YAML object at root")
    return raw


def apply_combo_overrides(base_cfg: dict[str, Any], combo: dict[str, Any]) -> dict[str, Any]:
    return apply_overrides(base_cfg, combo)


def validate_grid_document(strategy: str, testing: dict[str, Any]) -> None:
    """Validate every combo from a testing_parameters-style document."""
    validate_testing_grid_for_strategy(strategy, testing)


def finalize_backtest_config(cfg: dict[str, Any]) -> None:
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
    out: dict[str, Any] = {}
    for section in ("features", "signal", "risk", "backtest"):
        out.update(_flatten_config_section(section, doc.get(section) or {}))
    return out


def validate_testing_grid_for_strategy(strategy: str, testing: dict[str, Any]) -> None:
    strat = load_strategy(strategy)
    base = load_strategy_config(strategy)
    resolved = grid_combos_from_document(testing)
    for i, combo_flat in enumerate(resolved):
        cfg = apply_overrides(base, combo_flat)
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


def feature_config_fingerprint(cfg: dict[str, Any]) -> str:
    fk = feature_key_from_config(cfg)
    blob = json.dumps(fk, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def resolve_required_features(strategy: Any, cfg: dict[str, Any]) -> list[str]:
    del cfg
    return list(strategy.required_features())


def build_features_for_strategy(
    bars: pd.DataFrame,
    strategy: Any,
    cfg: dict[str, Any],
    *,
    asset: str,
    symbol: str,
    start: str,
    end: str,
    data_root: str | Path | None = None,
) -> pd.DataFrame:
    del asset, symbol, start, end, data_root, strategy
    return build_features_from_config(bars, cfg)


def generate_strategy_signals(strategy: Any, feature_df: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    return strategy.generate_signals(feature_df, cfg)


def prepare_canonical_signals(
    strategy_name: str,
    raw_signals: pd.DataFrame,
    metadata: Mapping[str, Any] | None = None,
) -> pd.DataFrame:
    m = infer_signal_mapping(strategy_name, metadata)
    out = canonicalize_signal_frame(raw_signals, m, copy=True)
    assert_canonical_signal_frame(out)
    return out


def assert_required_feature_columns(df: pd.DataFrame, required: list[str]) -> None:
    miss = [c for c in required if c not in df.columns]
    if miss:
        raise ValueError(f"missing required feature columns for strategy: {miss}")


def run_strategy_pipeline(
    *,
    strategy_name: str,
    cfg: dict[str, Any],
    bars: pd.DataFrame,
    asset: str,
    symbol: str,
    start: str,
    end: str,
    data_root: str | Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build features and standard signal frame (full width = features + ``sig_*``)."""
    strat = load_strategy(strategy_name)
    feat = build_features_for_strategy(
        bars, strat, cfg, asset=asset, symbol=symbol, start=start, end=end, data_root=data_root
    )
    assert_required_feature_columns(feat, resolve_required_features(strat, cfg))
    raw = generate_strategy_signals(strat, feat, cfg)
    canon = prepare_canonical_signals(strategy_name, raw, metadata=None)
    return feat, canon


class FeatureFrameCache:
    """Reuse feature DataFrames keyed by :func:`feature_config_fingerprint`."""

    def __init__(self, bars: pd.DataFrame) -> None:
        self._bars = bars
        self._feat: dict[str, pd.DataFrame] = {}
        self.hits = 0
        self.misses = 0
        self.signal_count = 0
        self.combo_count = 0

    def build_signals(
        self,
        strategy_name: str,
        cfg: dict[str, Any],
        asset: str,
        symbol: str,
        start: str,
        end: str,
        data_root: str | Path | None,
    ) -> tuple[str, pd.DataFrame]:
        self.combo_count += 1
        key = feature_config_fingerprint(cfg)
        strat = load_strategy(strategy_name)
        req = resolve_required_features(strat, cfg)
        if key in self._feat:
            self.hits += 1
            feat = self._feat[key]
        else:
            self.misses += 1
            feat = build_features_for_strategy(
                self._bars, strat, cfg, asset=asset, symbol=symbol, start=start, end=end, data_root=data_root
            )
            self._feat[key] = feat
        assert_required_feature_columns(feat, req)
        raw = generate_strategy_signals(strat, feat, cfg)
        self.signal_count += 1
        canon = prepare_canonical_signals(strategy_name, raw, metadata=None)
        return key, canon


def validate_pipeline(
    *,
    strategy_name: str,
    cfg: dict[str, Any],
    asset: str,
    symbol: str,
    start: str,
    end: str,
    data_dir: str | Path,
    with_data: bool,
) -> dict[str, Any]:
    """Dry diagnostics for ``--validate-pipeline`` (never runs ``run_strategy_backtest``)."""
    out: dict[str, Any] = {
        "strategy": strategy_name,
        "strategy_loads": False,
        "metadata_found": False,
        "required_features_known": False,
        "pipeline_signal_ready": False,
        "blockers": [],
        "recommendation": "",
    }
    try:
        strat = load_strategy(strategy_name)
        out["strategy_loads"] = True
    except Exception as e:
        out["blockers"].append(f"strategy_load: {e}")
        out["recommendation"] = "Fix strategy name or imports."
        return out

    from src.strategies.metadata import get_strategy_metadata

    meta = get_strategy_metadata(strategy_name)
    out["metadata_found"] = bool(meta)
    req = resolve_required_features(strat, cfg)
    out["required_features"] = req
    out["required_features_known"] = len(req) > 0 or True

    mapping = infer_signal_mapping(strategy_name)
    out["signal_mapping_keys"] = len(mapping)

    if not with_data:
        out["recommendation"] = (
            "Metadata-only check passed. Re-run with --symbol/--start/--end/--data-root "
            "to validate bars, features, and signals."
        )
        out["pipeline_signal_ready"] = len(out["blockers"]) == 0
        return out

    try:
        bars = read_bars(
            asset=asset,
            symbol=symbol,
            start=start,
            end=end,
            data_dir=data_dir,
        )
    except Exception as e:
        out["blockers"].append(f"read_bars: {e}")
        out["recommendation"] = "Fix data path, date range, or IBKR parquet layout."
        return out

    if bars is None or len(bars) == 0:
        out["blockers"].append("read_bars returned zero rows (missing parquet partitions?)")
        out["recommendation"] = "Ensure local data exists under data_dir for the requested window."
        return out

    try:
        feat, canon = run_strategy_pipeline(
            strategy_name=strategy_name,
            cfg=cfg,
            bars=bars,
            asset=asset,
            symbol=symbol,
            start=start,
            end=end,
            data_root=data_dir,
        )
    except Exception as e:
        out["blockers"].append(f"pipeline: {e}")
        out["recommendation"] = "Inspect feature requirements vs bar columns; check strategy config."
        return out

    out["rows_bars"] = int(len(bars))
    out["rows_features"] = int(len(feat))
    out["rows_signals"] = int(len(canon))
    out["pipeline_signal_ready"] = True
    out["recommendation"] = "Pipeline OK for reference backtest; run sweep without --validate-pipeline."
    return out


validate_canonical_pipeline = validate_pipeline
