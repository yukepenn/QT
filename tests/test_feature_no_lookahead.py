from __future__ import annotations

import pandas as pd

from src.features.build_features import build_basic_features
from src.strategies.loader import available_strategies, load_strategy


def _make_raw_two_sessions() -> pd.DataFrame:
    ny = "America/New_York"
    # Session 1: 5 minutes from 09:30
    s1 = pd.date_range("2026-01-05 09:30", periods=5, freq="1min", tz=ny)
    # Session 2: next day, same minutes
    s2 = pd.date_range("2026-01-06 09:30", periods=5, freq="1min", tz=ny)
    ts_ny = s1.append(s2)
    ts_utc = ts_ny.tz_convert("UTC")

    n = len(ts_utc)
    # Construct obvious highs/lows per session.
    high = [10, 11, 12, 13, 14, 20, 21, 22, 23, 24]
    low = [9, 8, 7, 6, 5, 19, 18, 17, 16, 15]
    close = [9.5, 10.5, 11.5, 12.5, 13.5, 19.5, 20.5, 21.5, 22.5, 23.5]
    open_ = [9.4] * n
    volume = [100] * n

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


def test_levels_lookahead_columns_are_renamed_and_intraday_so_far_is_safe() -> None:
    raw = _make_raw_two_sessions()
    feat = build_basic_features(raw, orb_open_minutes=2, copy=True, allow_overwrite=False)

    # Old unsafe names should not exist.
    assert "session_high" not in feat.columns
    assert "session_low" not in feat.columns
    assert "session_close" not in feat.columns

    # New explicit lookahead names should exist.
    assert "full_session_high_LOOKAHEAD" in feat.columns
    assert "full_session_low_LOOKAHEAD" in feat.columns
    assert "full_session_close_LOOKAHEAD" in feat.columns

    # Intraday so-far columns should exist and be cumulative within each session.
    assert "intraday_high_so_far" in feat.columns
    assert "intraday_low_so_far" in feat.columns

    # Session 1: cumulative max/min must match progressive extremes.
    s1 = feat[feat["session_date"] == "2026-01-05"].reset_index(drop=True)
    assert s1["intraday_high_so_far"].tolist() == [10, 11, 12, 13, 14]
    assert s1["intraday_low_so_far"].tolist() == [9, 8, 7, 6, 5]


def test_orb_known_columns_are_nan_or_false_before_after_orb() -> None:
    raw = _make_raw_two_sessions()
    feat = build_basic_features(raw, orb_open_minutes=2, copy=True, allow_overwrite=False)

    assert "after_orb" in feat.columns
    assert "orb_high_known" in feat.columns
    assert "orb_low_known" in feat.columns
    assert "orb_mid_known" in feat.columns
    assert "orb_width_pct_known" in feat.columns
    assert "above_orb_high_known" in feat.columns
    assert "below_orb_low_known" in feat.columns

    s1 = feat[feat["session_date"] == "2026-01-05"].reset_index(drop=True)
    # open_minutes=2 => after_orb is True from minute_from_open >= 2 (i.e., rows 2..)
    assert s1["after_orb"].tolist() == [False, False, True, True, True]

    # Before ORB completion: known anchors NaN, known booleans False.
    assert pd.isna(s1.loc[0, "orb_high_known"])
    assert pd.isna(s1.loc[1, "orb_low_known"])
    assert bool(s1.loc[0, "above_orb_high_known"]) is False
    assert bool(s1.loc[1, "below_orb_low_known"]) is False

    # After ORB completion: known anchors equal broadcast anchors.
    for i in [2, 3, 4]:
        assert float(s1.loc[i, "orb_high_known"]) == float(s1.loc[i, "orb_high"])
        assert float(s1.loc[i, "orb_low_known"]) == float(s1.loc[i, "orb_low"])


def test_no_strategy_requires_lookahead_features() -> None:
    for name in available_strategies():
        s = load_strategy(name)
        req = s.required_features()
        assert all("LOOKAHEAD" not in c for c in req), (name, [c for c in req if "LOOKAHEAD" in c])

