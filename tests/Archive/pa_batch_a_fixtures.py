"""Synthetic QQQ-like raw bars + feature build helpers for PA Batch A tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from src.features.feature_key import build_features_from_config
from src.strategies.loader import apply_overrides, load_strategy_config, strategy_root


def synthetic_qqq_raw(*, n: int = 220) -> pd.DataFrame:
    ny = "America/New_York"
    ts_ny = pd.date_range("2026-01-05 09:30", periods=n, freq="1min", tz=ny)
    ts_utc = ts_ny.tz_convert("UTC")
    r = pd.Series(np.arange(n, dtype=float))
    return pd.DataFrame(
        {
            "ts_utc": ts_utc,
            "open": 100.0 + r * 0.01,
            "high": 100.55 + r * 0.01,
            "low": 99.45 + r * 0.01,
            "close": 100.0 + r * 0.012,
            "volume": 1000.0 + r * 2.0,
            "asset": "equity",
            "symbol": "QQQ",
            "root": None,
            "contract": None,
            "average": np.nan,
            "barCount": np.nan,
            "source": "test",
            "useRTH": True,
            "bar_size": "1 min",
        }
    )


def build_pa_features(strategy_name: str, raw: pd.DataFrame | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    raw = raw if raw is not None else synthetic_qqq_raw()
    cfg = load_strategy_config(strategy_name)
    return build_features_from_config(raw, cfg), cfg


def merged_focused_config(strategy_name: str) -> dict[str, Any]:
    base = load_strategy_config(strategy_name)
    path = strategy_root() / "testing_parameters" / f"{strategy_name}_focused.yaml"
    tcfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    fixed = tcfg.get("fixed") or {}
    return apply_overrides(base, fixed)
