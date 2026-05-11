"""Tests for offline trade quality scoring."""
from __future__ import annotations

import pandas as pd

from src.research.score_trade_quality_offline import threshold_summary


def test_threshold_summary_empty_high_threshold():
    df = pd.DataFrame(
        {
            "r_multiple": [1.0, -0.5],
            "trade_quality_score": [45.0, 48.0],
            "entry_ts_utc": pd.to_datetime(
                ["2023-01-03T14:31:00Z", "2023-01-03T15:01:00Z"], utc=True
            ),
        }
    )
    t = threshold_summary(df, "x")
    ge70 = t[t["subset"] == "score_ge_70"]
    assert int(ge70.iloc[0]["trades"]) == 0


def test_threshold_summary_max_dd_ordered():
    df = pd.DataFrame(
        {
            "r_multiple": [2.0, -3.0, 1.0],
            "trade_quality_score": [40.0, 50.0, 60.0],
            "entry_ts_utc": pd.to_datetime(
                [
                    "2023-01-03T14:31:00Z",
                    "2023-01-03T15:01:00Z",
                    "2023-01-03T16:01:00Z",
                ],
                utc=True,
            ),
        }
    )
    t = threshold_summary(df, "x")
    row = t[t["subset"] == "all"].iloc[0]
    assert row["trades"] == 3
    assert row["max_dd_r_proxy"] <= 0
