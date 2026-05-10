"""PA magnet / measured-move proximity columns (skip-safe)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.build_types import PaFeatureConfig
from src.features.build_features import build_basic_features


def _raw() -> pd.DataFrame:
    ny = "America/New_York"
    ts = pd.date_range("2026-01-05 09:30", periods=80, freq="1min", tz=ny)
    r = np.arange(80, dtype=float)
    return pd.DataFrame(
        {
            "ts_utc": ts.tz_convert("UTC"),
            "open": 100 + r * 0.01,
            "high": 100.5 + r * 0.01,
            "low": 99.5 + r * 0.01,
            "close": 100 + r * 0.015,
            "volume": 1000 + r,
        }
    )


def test_magnet_columns_when_inputs_exist() -> None:
    raw = _raw()
    out = build_basic_features(
        raw, vol_windows=(5, 15, 20, 30), pa=PaFeatureConfig(), copy=True
    )
    assert "near_orb_high_known_atr" in out.columns
    assert "near_vwap_upper_1_atr" in out.columns
    assert "pa_mm_range_up_10" in out.columns
