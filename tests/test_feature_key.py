from __future__ import annotations

import pandas as pd

from src.features.feature_key import build_features_from_config, feature_key_from_config


def _raw_one_session() -> pd.DataFrame:
    ny = "America/New_York"
    ts_ny = pd.date_range("2026-01-05 09:30", periods=5, freq="1min", tz=ny)
    ts_utc = ts_ny.tz_convert("UTC")
    return pd.DataFrame(
        {
            "ts_utc": ts_utc,
            "open": [10, 10, 10, 10, 10],
            "high": [10, 11, 12, 13, 14],
            "low": [9, 9, 9, 9, 9],
            "close": [10, 10.5, 11, 12, 13],
            "volume": [100, 110, 120, 130, 140],
        }
    )


def test_feature_key_changes_when_knobs_change() -> None:
    base = {"features": {}}
    k0 = feature_key_from_config(base)
    k1 = feature_key_from_config({"features": {"orb_open_minutes": 10}})
    assert k0 != k1

    k2 = feature_key_from_config({"features": {"vwap_bands": [1.0, 3.0]}})
    assert k0 != k2

    k3 = feature_key_from_config({"features": {"vol_windows": [5, 20]}})
    assert k0 != k3

    k4 = feature_key_from_config({"features": {"price_action_windows": [7]}})
    assert k0 != k4

    k5 = feature_key_from_config({"features": {"volume_windows": [13]}})
    assert k0 != k5


def test_feature_key_is_stable_for_list_vs_tuple_inputs() -> None:
    k_list = feature_key_from_config({"features": {"vwap_bands": [1.0, 2.0], "vol_windows": [5, 15, 30]}})
    k_tup = feature_key_from_config({"features": {"vwap_bands": (1.0, 2.0), "vol_windows": (5, 15, 30)}})
    assert k_list == k_tup


def test_build_features_from_config_uses_defaults_and_custom_knobs() -> None:
    raw = _raw_one_session()
    # Defaults
    feat0 = build_features_from_config(raw, {"features": {}})
    assert "orb_high" in feat0.columns
    assert "volume_ratio_20" in feat0.columns

    # Custom windows should yield expected columns.
    cfg = {"features": {"price_action_windows": [7], "volume_windows": [13]}}
    feat1 = build_features_from_config(raw, cfg)
    assert "rolling_high_7_prior" in feat1.columns
    assert "rolling_low_7_prior" in feat1.columns
    assert "volume_ma_13_prior" in feat1.columns
    assert "volume_ratio_13" in feat1.columns

