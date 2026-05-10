"""Coarse PA regime / Always-In router columns (integer enums)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.build_types import PaFeatureConfig
from src.features.build_features import build_basic_features
from src.features.pa_brooks_enums import (
    PA_ALWAYS_IN_LONG,
    PA_ALWAYS_IN_NEUTRAL,
    PA_ALWAYS_IN_SHORT,
)


def _raw() -> pd.DataFrame:
    ny = "America/New_York"
    ts = pd.date_range("2026-01-05 09:30", periods=120, freq="1min", tz=ny)
    r = np.arange(120, dtype=float)
    return pd.DataFrame(
        {
            "ts_utc": ts.tz_convert("UTC"),
            "open": 100 + r * 0.01,
            "high": 100.6 + r * 0.01,
            "low": 99.4 + r * 0.01,
            "close": 100 + r * 0.02,
            "volume": 1000 + r,
        }
    )


def test_router_columns_exist() -> None:
    raw = _raw()
    base = build_basic_features(
        raw, vol_windows=(5, 15, 20, 30), pa=PaFeatureConfig(), copy=True
    )
    for c in (
        "pa_always_in_side_30",
        "pa_regime_label_30",
        "pa_trade_mode_30",
        "pa_late_trend_score_30",
        "pa_trend_to_tr_transition_score_30",
        "pa_limit_order_market_score_30",
    ):
        assert c in base.columns


def test_always_in_values_are_enum_subset() -> None:
    raw = _raw()
    base = build_basic_features(raw, vol_windows=(5, 15, 20, 30), copy=True)
    s = base["pa_always_in_side_30"].dropna().unique()
    for v in s:
        assert int(v) in (
            PA_ALWAYS_IN_SHORT,
            PA_ALWAYS_IN_NEUTRAL,
            PA_ALWAYS_IN_LONG,
        )


def test_regime_label_is_finite_int() -> None:
    raw = _raw()
    base = build_basic_features(raw, vol_windows=(5, 15, 20, 30), copy=True)
    lab = base["pa_regime_label_30"]
    assert np.isfinite(lab.astype(float)).all()
