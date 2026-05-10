"""Prior-exclusive PA swing primitives (pa_swings extensions)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.build_types import PaFeatureConfig
from src.features.pa_swings import add_pa_swing_features
from src.features.price_action import add_price_action_features


def _base() -> pd.DataFrame:
    ny = "America/New_York"
    ts = pd.date_range("2026-01-05 09:30", periods=50, freq="1min", tz=ny)
    return pd.DataFrame(
        {
            "session_date": ts.normalize(),
            "open": 100 + np.arange(50) * 0.01,
            "high": 101 + np.arange(50) * 0.01,
            "low": 99 + np.arange(50) * 0.01,
            "close": 100 + np.arange(50) * 0.015,
            "atr_like_20": np.full(50, 0.5),
        }
    )


def test_swing_extension_columns_exist() -> None:
    out = add_price_action_features(_base(), copy=True)
    out = add_pa_swing_features(out, PaFeatureConfig(swing_windows=(10,)), copy=False)
    for c in (
        "pa_pullback_bar_count_10",
        "pa_two_leg_pullback_down_10",
        "pa_second_entry_buy_proxy_10",
        "pa_failed_breakout_age_10",
        "pa_breakout_attempt_count_up_10",
        "pa_trapped_bears_score_10",
    ):
        assert c in out.columns


def test_no_lookahead_in_column_names() -> None:
    spec = PaFeatureConfig(swing_windows=(10,))
    from src.features.pa_swings import pa_swing_column_names

    assert not any("LOOKAHEAD" in x for x in pa_swing_column_names(spec))
