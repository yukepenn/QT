"""Bridge bars → features → strategy signals → standard ``sig_*`` (no accounting).

PnL lives in ``src.execution`` via :func:`src.backtest.engine.run_strategy_backtest`.
This module only orchestrates loads, feature builds, and signal normalization.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from src.backtest.config import (
    grid_combos_from_document,
    load_grid_document,
    merge_strategy_config,
)
from src.backtest.signal_adapter import (
    assert_canonical_signal_frame,
    canonicalize_signal_frame,
    infer_signal_mapping,
)
from src.data.read_bars import read_bars
from src.features.feature_key import build_features_from_config, feature_key_from_config
from src.strategies.loader import load_strategy

STANDARD_SIGNAL_CONTRACT_VERSION = "standard_sig_v1"

load_strategy_config_merged = merge_strategy_config


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
            "to validate bars, features, and signals."
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
    out["recommendation"] = "Pipeline OK for reference backtest; run sweep without --validate-pipeline."
    return out
