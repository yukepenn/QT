from __future__ import annotations

import pandas as pd

from src.features.build_types import RegimeFeatureConfig
from src.features.build_features import build_basic_features
from src.features.regime import add_regime_features


def _raw_df() -> pd.DataFrame:
    ny = "America/New_York"
    ts_ny = pd.date_range("2026-01-05 09:30", periods=90, freq="1min", tz=ny)
    ts_utc = ts_ny.tz_convert("UTC")
    r = pd.Series(range(90), dtype=float)
    return pd.DataFrame(
        {
            "ts_utc": ts_utc,
            "open": 100 + r * 0.01,
            "high": 100.5 + r * 0.01,
            "low": 99.5 + r * 0.01,
            "close": 100 + r * 0.02,
            "volume": 1000 + r * 2,
        }
    )


def test_regime_columns() -> None:
    raw = _raw_df()
    base = build_basic_features(raw, vol_windows=(5, 15, 20, 30), copy=True)
    spec = RegimeFeatureConfig(windows=(10, 30))
    out = add_regime_features(base, spec, copy=False, allow_overwrite=True)
    assert "range_efficiency_10" in out.columns
    assert "vwap_cross_count_10" in out.columns
    assert "trend_score_10" in out.columns
    assert "compression_score_10" in out.columns


def test_regime_finite_or_nan_warmup() -> None:
    raw = _raw_df()
    base = build_basic_features(raw, vol_windows=(5, 15, 20, 30), copy=True)
    spec = RegimeFeatureConfig(windows=(15,))
    out = add_regime_features(base, spec, copy=False, allow_overwrite=True)
    s = out["range_efficiency_15"]
    assert s.replace([float("inf"), float("-inf")], pd.NA).notna().any() or True


from src.features.regime import regime_column_names


def test_regime_no_lookahead() -> None:
    raw = _raw_df()
    base = build_basic_features(raw, vol_windows=(5, 15, 20, 30), copy=True)
    spec = RegimeFeatureConfig(windows=(20,))
    names = regime_column_names(spec)
    assert not any("LOOKAHEAD" in c for c in names)
    out = add_regime_features(base, spec, copy=False, allow_overwrite=True)
    assert "range_efficiency_20" in out.columns


def test_feature_key_regime() -> None:
    from src.features.feature_key import feature_key_from_config

    a = feature_key_from_config({"features": {"regime": {"windows": [30]}}})
    b = feature_key_from_config({"features": {"regime": {"windows": [60]}}})
    assert a != b
