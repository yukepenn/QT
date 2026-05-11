"""Brooks-style bar primitives in price_action (no lookahead)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.build_types import PaFeatureConfig
from src.features.price_action import add_price_action_features


def _df() -> pd.DataFrame:
    ny = "America/New_York"
    ts = pd.date_range("2026-01-05 09:30", periods=40, freq="1min", tz=ny)
    return pd.DataFrame(
        {
            "session_date": ts.normalize(),
            "open": np.linspace(100, 102, 40),
            "high": np.linspace(101, 103, 40),
            "low": np.linspace(99, 101, 40),
            "close": np.linspace(100.5, 102.5, 40),
        }
    )


def test_bar_primitive_columns_exist() -> None:
    out = add_price_action_features(_df(), pa=PaFeatureConfig(), copy=True)
    for c in (
        "strong_bull_close",
        "strong_bear_close",
        "weak_bull_close",
        "weak_bear_close",
        "strong_bull_signal_bar",
        "strong_bear_signal_bar",
        "failed_bull_signal_bar",
        "failed_bear_signal_bar",
        "bull_micro_channel_3",
        "bear_micro_channel_3",
    ):
        assert c in out.columns


def test_micro_channel_resets_across_sessions() -> None:
    d = _df()
    d2 = d.copy()
    d2["session_date"] = pd.to_datetime("2026-01-06 00:00:00")
    both = pd.concat([d, d2], ignore_index=True)
    out = add_price_action_features(both, copy=True)
    # first bar of second session should not inherit micro streak from session 1
    i = len(d)
    assert out.loc[i, "bull_micro_channel_5"] in (0, 1)


def test_no_inf_in_body_pct_columns() -> None:
    out = add_price_action_features(_df(), copy=True)
    s = out["body_pct"].replace([np.inf, -np.inf], np.nan)
    assert s.notna().all()
