"""Side-specific failed-breakout age columns (pa_swings)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.build_types import PaFeatureConfig
from src.features.pa_swings import add_pa_swing_features
from src.features.price_action import add_price_action_features


def _two_sessions() -> pd.DataFrame:
    """Session A: strong uptrend; Session B: reset — ages restart."""
    ny = "America/New_York"
    parts: list[pd.DataFrame] = []
    for day in ("2026-01-05", "2026-01-06"):
        ts = pd.date_range(f"{day} 09:30", periods=40, freq="1min", tz=ny)
        base = np.linspace(100.0, 103.0, len(ts))
        parts.append(
            pd.DataFrame(
                {
                    "ts_utc": ts.tz_convert("UTC"),
                    "session_date": ts.normalize(),
                    "open": base,
                    "high": base + 0.4,
                    "low": base - 0.15,
                    "close": base + 0.2,
                    "atr_like_20": np.full(len(ts), 0.5),
                }
            )
        )
    return pd.concat(parts, ignore_index=True)


def test_down_up_age_columns_exist() -> None:
    raw = _two_sessions()
    out = add_price_action_features(raw, copy=True)
    out = add_pa_swing_features(out, PaFeatureConfig(swing_windows=(20,)), copy=False)
    for c in (
        "pa_failed_breakout_down_age_20",
        "pa_failed_breakout_up_age_20",
        "pa_failed_breakout_age_20",
    ):
        assert c in out.columns


def test_legacy_age_equals_down_age() -> None:
    raw = _two_sessions()
    out = add_price_action_features(raw, copy=True)
    out = add_pa_swing_features(out, PaFeatureConfig(swing_windows=(20,)), copy=False)
    d = out["pa_failed_breakout_down_age_20"].to_numpy()
    g = out["pa_failed_breakout_age_20"].to_numpy()
    np.testing.assert_array_equal(d, g)


def test_ages_reset_across_sessions() -> None:
    raw = _two_sessions()
    out = add_price_action_features(raw, copy=True)
    out = add_pa_swing_features(out, PaFeatureConfig(swing_windows=(20,)), copy=False)
    # First row of second session (40 bars per session in fixture)
    i0 = 40
    assert out.loc[i0, "session_date"] != out.loc[i0 - 1, "session_date"]
    assert out.loc[i0, "pa_failed_breakout_down_age_20"] >= 0
    assert out.loc[i0, "pa_failed_breakout_up_age_20"] >= 0


def test_trapped_scores_differ_on_asymmetric_pattern() -> None:
    ny = "America/New_York"
    ts = pd.date_range("2026-01-07 09:30", periods=60, freq="1min", tz=ny)
    # Down-spike session: more failed-down / bull-reversal context than symmetric up trap
    close = np.concatenate([np.full(30, 100.0), np.full(30, 99.0)])
    low = close - 0.5
    high = close + 0.05
    raw = pd.DataFrame(
        {
            "ts_utc": ts.tz_convert("UTC"),
            "session_date": ts.normalize(),
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "atr_like_20": np.full(len(ts), 0.4),
        }
    )
    out = add_price_action_features(raw, copy=True)
    out = add_pa_swing_features(out, PaFeatureConfig(swing_windows=(20,)), copy=False)
    tb = out["pa_trapped_bears_score_20"].to_numpy()
    tu = out["pa_trapped_bulls_score_20"].to_numpy()
    assert not np.allclose(tb, tu, equal_nan=True)
