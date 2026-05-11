from __future__ import annotations

import pandas as pd

from src.features.build_features import build_basic_features
from src.features.feature_key import feature_key_from_config


def _raw() -> pd.DataFrame:
    ny = "America/New_York"
    ts_ny = pd.date_range("2026-01-05 09:30", periods=100, freq="1min", tz=ny)
    ts_utc = ts_ny.tz_convert("UTC")
    r = pd.Series(range(100), dtype=float)
    return pd.DataFrame(
        {
            "ts_utc": ts_utc,
            "open": 100 + r * 0.01,
            "high": 100.5 + r * 0.01,
            "low": 99.5 + r * 0.01,
            "close": 100 + r * 0.011,
            "volume": 1000 + r * 2,
        }
    )


def test_multiday_level_columns_exist() -> None:
    raw = _raw()
    out = build_basic_features(raw, copy=True)
    for c in ("prior_3day_low", "prior_5day_low", "previous_week_low"):
        assert c in out.columns
        assert "LOOKAHEAD" not in c


def test_supertrend_feature_key_changes() -> None:
    a = feature_key_from_config(
        {
            "features": {
                "indicators": {
                    "supertrend_tuples": [[14, 2.0]],
                    "ema_windows": [],
                    "sma_windows": [],
                    "rsi_windows": [],
                    "macd_tuples": [],
                    "stochastic_tuples": [],
                    "cci_windows": [],
                    "adx_windows": [],
                },
                "vol_windows": [5, 14, 15, 30],
            }
        }
    )
    b = feature_key_from_config(
        {
            "features": {
                "indicators": {
                    "supertrend_tuples": [[14, 3.0]],
                    "ema_windows": [],
                    "sma_windows": [],
                    "rsi_windows": [],
                    "macd_tuples": [],
                    "stochastic_tuples": [],
                    "cci_windows": [],
                    "adx_windows": [],
                },
                "vol_windows": [5, 14, 15, 30],
            }
        }
    )
    assert a != b
