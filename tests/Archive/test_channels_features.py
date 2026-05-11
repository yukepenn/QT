from __future__ import annotations

import pandas as pd

from src.features.build_types import ChannelsFeatureConfig
from src.features.build_features import build_basic_features
from src.features.channels import add_channel_features, channel_column_names


def _raw_df() -> pd.DataFrame:
    ny = "America/New_York"
    ts_ny = pd.date_range("2026-01-05 09:30", periods=120, freq="1min", tz=ny)
    ts_utc = ts_ny.tz_convert("UTC")
    rng = pd.Series(range(120), dtype=float)
    return pd.DataFrame(
        {
            "ts_utc": ts_utc,
            "open": 100 + rng * 0.01,
            "high": 100.5 + rng * 0.01,
            "low": 99.5 + rng * 0.01,
            "close": 100 + rng * 0.02,
            "volume": 1000 + rng * 5,
        }
    )


def test_bollinger_columns_present() -> None:
    raw = _raw_df()
    base = build_basic_features(raw, vol_windows=(5, 15, 20, 30), copy=True)
    spec = ChannelsFeatureConfig(
        bb_windows=(20,),
        bb_stds=(2.0,),
        bb_bandwidth_lookbacks=(30,),
        donchian_windows=(20,),
    )
    out = add_channel_features(base, spec, copy=False, allow_overwrite=True)
    assert "bb_mid_20" in out.columns
    assert "bb_upper_20_2.0" in out.columns
    assert "bb_lower_20_2.0" in out.columns
    assert "bb_width_20_2.0" in out.columns
    assert "bb_percent_b_20_2.0" in out.columns


def test_donchian_prior_exclusive() -> None:
    raw = _raw_df()
    base = build_basic_features(raw, vol_windows=(5, 15, 20, 30), copy=True)
    spec = ChannelsFeatureConfig(donchian_windows=(5,))
    out = add_channel_features(base, spec, copy=False, allow_overwrite=True)
    dh = out["donchian_high_5_prior"]
    # Bar index 6: prior-exclusive 5-bar window uses highs from bars 1..5 (indices 1-5)
    i = 6
    if i < len(out):
        past_max = float(out["high"].iloc[1:i].max())
        assert abs(float(dh.iloc[i]) - past_max) < 1e-9 or (pd.isna(dh.iloc[i]) and pd.isna(past_max))


def test_bb_width_percentile_bounded() -> None:
    raw = _raw_df()
    base = build_basic_features(raw, vol_windows=(5, 15, 20, 30), copy=True)
    spec = ChannelsFeatureConfig(
        bb_windows=(10,),
        bb_stds=(2.0,),
        bb_bandwidth_lookbacks=(20,),
        donchian_windows=(),
    )
    out = add_channel_features(base, spec, copy=False, allow_overwrite=True)
    col = "bb_width_percentile_10_2.0_20"
    assert col in out.columns
    s = out[col].dropna()
    assert s.min() >= 0.0 or len(s) == 0
    assert s.max() <= 1.0 or len(s) == 0


def test_no_lookahead_columns() -> None:
    raw = _raw_df()
    base = build_basic_features(raw, vol_windows=(5, 15, 20, 30), copy=True)
    spec = ChannelsFeatureConfig(
        bb_windows=(15,),
        bb_stds=(1.5,),
        bb_bandwidth_lookbacks=(25,),
        donchian_windows=(10,),
    )
    names = channel_column_names(spec)
    assert not any("LOOKAHEAD" in c for c in names)
    out = add_channel_features(base, spec, copy=False, allow_overwrite=True)
    assert "bb_mid_15" in out.columns


def test_feature_key_channels() -> None:
    from src.features.feature_key import feature_key_from_config

    k0 = feature_key_from_config({"features": {"channels": {"bb_windows": [20], "bb_stds": [2.0], "bb_bandwidth_lookbacks": [], "donchian_windows": []}}})
    k1 = feature_key_from_config({"features": {"channels": {"bb_windows": [30], "bb_stds": [2.0], "bb_bandwidth_lookbacks": [], "donchian_windows": []}}})
    assert k0 != k1
