"""FeatureStore v1 tests (behavior-preserving feature reuse)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.features.feature_key import build_features_from_config
from src.features.feature_store import FeatureStore


def _tiny_raw_df() -> pd.DataFrame:
    ts = pd.to_datetime(
        [
            "2025-01-02 14:30:00+00:00",
            "2025-01-02 14:31:00+00:00",
            "2025-01-02 14:32:00+00:00",
            "2025-01-02 14:33:00+00:00",
            "2025-01-02 14:34:00+00:00",
        ]
    )
    return pd.DataFrame(
        {
            "ts_utc": ts,
            "asset": ["equity"] * len(ts),
            "symbol": ["QQQ"] * len(ts),
            "open": [100, 101, 102, 101, 100],
            "high": [101, 102, 103, 102, 101],
            "low": [99, 100, 101, 100, 99],
            "close": [100.5, 101.5, 101.8, 100.9, 100.1],
            "volume": [1000, 1200, 1100, 1500, 1300],
        }
    )


def test_feature_store_uses_provided_raw_df_no_load() -> None:
    raw = _tiny_raw_df()
    fs = FeatureStore(asset="equity", symbol="QQQ", start="2025-01-01", end="2025-01-31", raw_df=raw)
    assert fs.stats.raw_load_count == 0
    got = fs.get_raw()
    assert got is raw
    assert fs.stats.raw_load_count == 0


def test_feature_store_cache_hit_miss_counts() -> None:
    raw = _tiny_raw_df()
    fs = FeatureStore(asset="equity", symbol="QQQ", start="2025-01-01", end="2025-01-31", raw_df=raw)
    cfg = {"features": {"orb_open_minutes": 15}}
    _ = fs.get_features(cfg)
    _ = fs.get_features(cfg)
    assert fs.stats.feature_requests == 2
    assert fs.stats.feature_cache_misses == 1
    assert fs.stats.feature_cache_hits == 1


def test_feature_store_different_feature_config_misses() -> None:
    raw = _tiny_raw_df()
    fs = FeatureStore(asset="equity", symbol="QQQ", start="2025-01-01", end="2025-01-31", raw_df=raw)
    cfg1 = {"features": {"orb_open_minutes": 15}}
    cfg2 = {"features": {"orb_open_minutes": 3}}
    _ = fs.get_features(cfg1)
    _ = fs.get_features(cfg2)
    assert fs.stats.feature_cache_misses == 2
    assert fs.stats.feature_cache_hits == 0


def test_feature_store_output_equals_build_features_from_config() -> None:
    raw = _tiny_raw_df()
    cfg = {
        "features": {
            "orb_open_minutes": 15,
            "vwap_bands": [1.0, 2.0],
            "vol_windows": [5, 15, 30],
        }
    }
    direct = build_features_from_config(raw, cfg).sort_values("ts_utc", ignore_index=True)
    fs = FeatureStore(asset="equity", symbol="QQQ", start="2025-01-01", end="2025-01-31", raw_df=raw)
    via = fs.get_features(cfg)
    assert list(direct.columns) == list(via.columns)
    assert len(direct) == len(via)
    for c in ("ts_utc", "open", "close", "volume", "minute_from_open", "vwap", "orb_high", "orb_low"):
        if c not in direct.columns:
            continue
        a = direct[c].to_numpy()
        b = via[c].to_numpy()
        if np.issubdtype(a.dtype, np.number):
            np.testing.assert_allclose(a.astype(float), b.astype(float), rtol=0, atol=0)
        else:
            assert pd.Series(a).equals(pd.Series(b))

