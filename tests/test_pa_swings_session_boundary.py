"""Session-boundary regression tests for pa_swings.close-back-inside flags."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.build_types import PaFeatureConfig
from src.features.pa_swings import add_pa_swing_features


def _sess_day(name: str) -> pd.Timestamp:
    return pd.Timestamp(f"{name}T14:30:00", tz="America/New_York")


def test_close_back_inside_no_cross_session_leak_for_two_sessions():
    """Last bar of session A breaks out; first bar of session B must not tag close-back-inside."""
    n = 6
    ts = pd.date_range(
        _sess_day("2025-01-02"),
        periods=n,
        freq="1min",
        tz="America/New_York",
    )
    day_a = pd.Timestamp("2025-01-02").date()
    day_b = pd.Timestamp("2025-01-03").date()
    session_date = np.array([day_a] * 3 + [day_b] * 3, dtype=object)

    rh_val = 100.0
    rl_val = 99.0
    open_ = np.full(n, 99.5)
    high = np.array([99.8, 99.9, 101.0, 99.7, 99.8, 99.85])
    low = np.array([99.7, 99.8, 100.9, 99.6, 99.7, 99.80])
    close = np.array([99.85, 99.85, 100.95, 99.75, 99.85, 99.82])

    df = pd.DataFrame(
        {
            "ts_ny": ts,
            "session_date": session_date,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "atr_like_20": np.full(n, 0.5),
        }
    )

    spec = PaFeatureConfig(swing_windows=[60])
    out = add_pa_swing_features(df, spec, copy=True)

    col = "pa_close_back_inside_60"
    assert col in out.columns
    # First bar of session B is index 3 — must not inherit outside_prev from session A.
    assert int(out[col].iloc[3]) == 0


def test_prior_high_low_remain_session_scoped():
    """Rolling prior high/low columns reset across sessions (no foreign session bars)."""
    n = 5
    ts = pd.date_range(
        _sess_day("2025-01-03"),
        periods=n,
        freq="1min",
        tz="America/New_York",
    )
    day_a = pd.Timestamp("2025-01-03").date()
    day_b = pd.Timestamp("2025-01-06").date()
    session_date = np.array([day_a] * 2 + [day_b] * 3, dtype=object)
    high = np.array([101.0, 102.0, 100.0, 101.5, 101.6])
    low = np.array([100.0, 101.0, 99.5, 101.0, 101.2])
    close = (high + low) / 2.0
    df = pd.DataFrame(
        {
            "ts_ny": ts,
            "session_date": session_date,
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "atr_like_20": np.full(n, 0.5),
        }
    )
    spec = PaFeatureConfig(swing_windows=[2])
    out = add_pa_swing_features(df, spec, copy=True)
    ph = np.asarray(out["pa_prior_high_2"], dtype=float)
    # Start of session B: prior_exclusive rolling has no prior rows → NaN (not session A's peak).
    assert np.isnan(ph[2])
