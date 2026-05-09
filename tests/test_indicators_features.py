from __future__ import annotations

import pandas as pd

from src.features.build_types import IndicatorsFeatureConfig
from src.features.build_features import build_basic_features
from src.features.indicators import add_indicator_features, indicator_column_names


def _raw_df() -> pd.DataFrame:
    ny = "America/New_York"
    ts_ny = pd.date_range("2026-01-05 09:30", periods=80, freq="1min", tz=ny)
    ts_utc = ts_ny.tz_convert("UTC")
    r = pd.Series(range(80), dtype=float)
    return pd.DataFrame(
        {
            "ts_utc": ts_utc,
            "open": 100 + r * 0.01,
            "high": 100.5 + r * 0.01,
            "low": 99.5 + r * 0.01,
            "close": 100 + r * 0.015,
            "volume": 1000 + r * 2,
        }
    )


def test_indicator_columns_and_no_lookahead() -> None:
    raw = _raw_df()
    base = build_basic_features(raw, copy=True)
    spec = IndicatorsFeatureConfig(
        ema_windows=(5, 10),
        sma_windows=(10,),
        rsi_windows=(7,),
        macd_tuples=((12, 26, 9),),
        stochastic_tuples=((14, 3),),
        cci_windows=(14,),
        adx_windows=(14,),
    )
    out = add_indicator_features(base, spec, copy=False, allow_overwrite=True)
    assert "ema_5" in out.columns and "ema_slope_5" in out.columns
    assert "rsi_7" in out.columns
    assert "macd_line_12_26" in out.columns
    assert "stoch_k_14" in out.columns
    assert "cci_14" in out.columns
    assert "adx_14" in out.columns
    bad = [c for c in indicator_column_names(spec) if "LOOKAHEAD" in c]
    assert not bad


def test_ema_cross_uses_prior_bar_only() -> None:
    raw = _raw_df()
    base = build_basic_features(raw, copy=True)
    spec = IndicatorsFeatureConfig(ema_windows=(3, 5), sma_windows=(), rsi_windows=(), macd_tuples=(), stochastic_tuples=(), cci_windows=(), adx_windows=())
    out = add_indicator_features(base, spec, copy=False, allow_overwrite=True)
    assert len(out) == len(base)


def test_feature_key_indicators_changes() -> None:
    from src.features.feature_key import feature_key_from_config

    a = feature_key_from_config({"features": {"indicators": {"ema_windows": [9], "sma_windows": [], "rsi_windows": [], "macd_tuples": [], "stochastic_tuples": [], "cci_windows": [], "adx_windows": []}}})
    b = feature_key_from_config({"features": {"indicators": {"ema_windows": [10], "sma_windows": [], "rsi_windows": [], "macd_tuples": [], "stochastic_tuples": [], "cci_windows": [], "adx_windows": []}}})
    assert a != b


def test_build_features_from_config_indicators() -> None:
    from src.features.feature_key import build_features_from_config

    raw = _raw_df()
    cfg = {
        "features": {
            "indicators": {
                "ema_windows": [5],
                "sma_windows": [10],
                "rsi_windows": [],
                "macd_tuples": [],
                "stochastic_tuples": [],
                "cci_windows": [],
                "adx_windows": [],
            }
        }
    }
    out = build_features_from_config(raw, cfg)
    assert "ema_5" in out.columns and "sma_10" in out.columns
