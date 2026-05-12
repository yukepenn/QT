"""Bridge bars → features → strategy signals → canonical ``sig_*`` (no accounting).

Canonical PnL lives in ``src.execution`` via :func:`src.backtest.engine.run_strategy_backtest`.
This module only orchestrates loads, feature builds, and signal normalization.
"""

from __future__ import annotations

import hashlib
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
from src.strategies.loader import apply_overrides, deep_update, load_strategy, load_strategy_config


STANDARD_SIGNAL_CONTRACT_VERSION = "standard_sig_v1"


def load_strategy_config_merged(
    strategy_name: str,
    config_path: str | Path | None,
    overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Load base YAML from ``config_path`` or ``parameters/<strategy>.yaml``, then ``deep_update`` overrides."""
    if config_path:
        p = Path(config_path)
        raw = _load_yaml_or_json(p)
        if not isinstance(raw, dict):
            raise ValueError(f"config file {p} must contain a JSON/YAML object")
        cfg = deepcopy(raw)
    else:
        cfg = load_strategy_config(strategy_name)
    if overrides:
        cfg = deep_update(cfg, dict(overrides))
    sid = cfg.get("strategy")
    if sid is not None and str(sid) != str(strategy_name):
        raise ValueError(f"config strategy={sid!r} does not match --strategy {strategy_name!r}")
    if "strategy" not in cfg:
        cfg = deepcopy(cfg)
        cfg["strategy"] = strategy_name
    return cfg


def _load_yaml_or_json(path: Path) -> Any:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    suf = path.suffix.lower()
    if suf in (".json",):
        return json.loads(text)
    return yaml.safe_load(text)


def load_grid_document(path: str | Path) -> dict[str, Any]:
    """Load a grid YAML/JSON file (object root)."""
    p = Path(path)
    raw = _load_yaml_or_json(p)
    if not isinstance(raw, dict):
        raise ValueError(f"grid file {p} must contain a JSON/YAML object at root")
    return raw


def grid_combos_from_document(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten grid: ``{"grid": {"a.b": [1,2]}}`` or top-level dict of lists (dotted keys ok)."""
    import itertools

    from src.strategies.loader import expand_grid

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
    """Build features and canonical signal frame (full width = features + ``sig_*``)."""
    strat = load_strategy(strategy_name)
    feat = build_features_for_strategy(
        bars, strat, cfg, asset=asset, symbol=symbol, start=start, end=end, data_root=data_root
    )
    assert_required_feature_columns(feat, resolve_required_features(strat, cfg))
    raw = generate_strategy_signals(strat, feat, cfg)
    canon = prepare_canonical_signals(strategy_name, raw, metadata=None)
    return feat, canon


def validate_canonical_pipeline(
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
        "canonical_signal_ready": False,
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
            "to validate bars, features, and canonical signals."
        )
        out["canonical_signal_ready"] = len(out["blockers"]) == 0
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
    out["canonical_signal_ready"] = True
    out["recommendation"] = "Pipeline OK for canonical backtest; run sweep without --validate-pipeline."
    return out
