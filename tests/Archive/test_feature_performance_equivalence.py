"""Session / column invariants for feature build after concat-style refactors."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pytest

from src.features.build_features import build_basic_features
from src.features.feature_key import build_features_from_config, feature_key_from_config
from src.strategies.loader import load_strategy_config


def _raw_two_sessions(*, n_per: int = 12) -> pd.DataFrame:
    ny = "America/New_York"
    s1 = pd.date_range("2026-01-05 09:30", periods=n_per, freq="1min", tz=ny)
    s2 = pd.date_range("2026-01-06 09:30", periods=n_per, freq="1min", tz=ny)
    ts_ny = pd.DatetimeIndex([*s1, *s2])
    ts_utc = ts_ny.tz_convert("UTC")
    n = len(ts_utc)
    high = list(range(100, 100 + n))
    low = [h - 2 for h in high]
    close = [h - 1 for h in high]
    open_ = [c - 0.1 for c in close]
    volume = [1000 + i for i in range(n)]
    return pd.DataFrame(
        {
            "ts_utc": ts_utc,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


def test_build_basic_features_no_duplicate_columns() -> None:
    raw = _raw_two_sessions()
    feat = build_basic_features(raw, copy=True, allow_overwrite=False)
    dup = feat.columns[feat.columns.duplicated()].tolist()
    assert dup == [], f"duplicate columns: {dup}"


def test_volume_ma_prior_first_bar_nan_per_session() -> None:
    raw = _raw_two_sessions()
    feat = build_basic_features(raw, copy=True, allow_overwrite=False)
    vma = feat["volume_ma_20_prior"]
    first_idx = feat.groupby("session_date", sort=False).head(1).index
    assert vma.loc[first_idx].isna().all()


def test_ret_1m_first_bar_nan_per_session() -> None:
    raw = _raw_two_sessions()
    feat = build_basic_features(raw, copy=True, allow_overwrite=False)
    r = feat["ret_1m"]
    first_idx = feat.groupby("session_date", sort=False).head(1).index
    assert r.loc[first_idx].isna().all()


def test_vwap_first_bar_equals_typical_price() -> None:
    raw = _raw_two_sessions()
    feat = build_basic_features(raw, copy=True, allow_overwrite=False)
    first = feat.groupby("session_date", sort=False).head(1)
    tp = (first["high"] + first["low"] + first["close"]) / 3.0
    np.testing.assert_allclose(
        first["vwap"].astype(float).to_numpy(),
        tp.astype(float).to_numpy(),
        rtol=1e-9,
        atol=1e-9,
    )


def test_rolling_high_3_prior_second_bar_matches_first_high() -> None:
    raw = _raw_two_sessions()
    feat = build_basic_features(raw, copy=True, allow_overwrite=False)
    for _, sub in feat.groupby("session_date", sort=False):
        sub = sub.sort_values("ts_utc")
        if len(sub) < 2:
            continue
        assert sub.iloc[1]["rolling_high_3_prior"] == sub.iloc[0]["high"]


def test_vwap_persistence_shifted_not_current() -> None:
    raw = _raw_two_sessions()
    feat = build_basic_features(raw, copy=True, allow_overwrite=False)
    col = "vwap_persistence_above_10"
    assert col in feat.columns
    first_idx = feat.groupby("session_date", sort=False).head(1).index
    assert feat.loc[first_idx, col].isna().all()


def test_orb_known_nan_until_after_orb() -> None:
    raw = _raw_two_sessions()
    feat = build_basic_features(raw, copy=True, allow_overwrite=False, orb_open_minutes=5)
    m = ~feat["after_orb"].astype(bool)
    assert feat.loc[m, "orb_high_known"].isna().all()


def test_feature_key_stable_pa_buy_sell_close_trend() -> None:
    cfg = load_strategy_config("pa_buy_sell_close_trend")
    k1 = feature_key_from_config(cfg)
    k2 = feature_key_from_config(cfg)
    assert k1 == k2


def test_pa_required_features_no_lookahead_token() -> None:
    from src.strategies.loader import load_strategy

    strat = load_strategy("pa_buy_sell_close_trend")
    req = strat.required_features()
    for f in req:
        assert "LOOKAHEAD" not in f, f"unexpected LOOKAHEAD in {f!r}"


def test_no_fragmentation_warning_optimized_modules() -> None:
    raw = _raw_two_sessions()
    cfg = load_strategy_config("pa_buy_sell_close_trend")
    targets = ("volume.py", "volatility.py", "vwap.py", "price_action.py")
    with warnings.catch_warnings(record=True) as wrec:
        warnings.simplefilter("always")
        build_features_from_config(raw, cfg)
    frag = []
    for w in wrec:
        if not issubclass(w.category, pd.errors.PerformanceWarning):
            continue
        if "fragmented" not in str(w.message).lower():
            continue
        loc = getattr(w, "filename", None) or ""
        if any(t in str(loc) for t in targets):
            frag.append(str(w.message))
    assert not frag, frag


def test_sorted_ts_output() -> None:
    raw = _raw_two_sessions()
    cfg = load_strategy_config("pa_buy_sell_close_trend")
    feat = build_features_from_config(raw, cfg).sort_values("ts_utc", ignore_index=True)
    assert feat["ts_utc"].is_monotonic_increasing
    assert len(feat) == len(raw)
