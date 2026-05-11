"""Tests for trade quality analysis helpers."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd

from src.research.analyze_trade_quality import analyze_frame
from src.research.trade_quality_helpers import bucket_quantiles, summarize_bucket


def test_summarize_bucket_respects_min_n():
    df = pd.DataFrame({"b": ["a", "a", "b"], "r_multiple": [1.0, -0.5, 0.1], "bars_held": [2, 3, 4]})
    s = summarize_bucket(df, "b", min_n=5)
    assert s["low_sample_warning"].tolist() == [True, True]


def test_bucket_quantiles_with_nan():
    s = pd.Series([1.0, 2.0, 3.0, float("nan")])
    b = bucket_quantiles(s)
    assert "missing" in set(b.astype(str))


def test_analyze_frame_writes_outputs():
    df = pd.DataFrame(
        {
            "r_multiple": [1.0, -0.5, 0.2],
            "strategy": ["s", "s", "t"],
            "strategy_family": ["f", "f", "g"],
            "session_date": ["d1", "d1", "d2"],
            "entry_ts_utc": pd.to_datetime(
                ["2023-01-03T14:31:00Z", "2023-01-03T15:01:00Z", "2023-01-04T14:31:00Z"], utc=True
            ),
            "entry_regime_label": ["trading_range", "trading_range", "late_trend_climax"],
            "entry_minute_from_open": [10, 40, 20],
            "entry_vwap_cross_count": [1, 3, 6],
            "entry_distance_from_vwap_atr": [0.1, 0.5, 1.0],
            "entry_trend_score": [0.1, -0.2, 0.3],
            "entry_range_efficiency": [0.2, 0.4, 0.6],
            "entry_above_orb_high": [0, 1, 0],
            "entry_below_orb_low": [0, 0, 1],
            "exit_reason": ["target", "stop", "target"],
            "risk_per_share": [0.05, 0.05, 0.05],
            "bars_held": [2, 3, 4],
        }
    )
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        analyze_frame(df, p)
        assert (p / "entry_regime_label_summary.csv").exists()
