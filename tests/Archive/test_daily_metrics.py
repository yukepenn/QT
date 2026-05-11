"""Daily aggregation and daily_trade_number profiles."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from src.backtest.metrics import summarize_daily
from src.combiner.metrics import summarize_combiner


def test_summarize_daily_two_days():
    df = pd.DataFrame(
        {
            "session_date": pd.to_datetime(["2020-01-02", "2020-01-02", "2020-01-03", "2020-01-03"]),
            "r_multiple": [1.0, -0.5, -1.0, -1.0],
            "net_pnl": [1.0, -1.0, -1.0, -1.0],
            "exit_reason": ["target", "stop", "stop", "stop"],
            "bars_held": [1, 2, 3, 4],
        }
    )
    d = summarize_daily(df)
    assert d["active_days"] == 2
    assert d["positive_day_rate"] == pytest.approx(0.5)
    assert d["worst_day_r"] == pytest.approx(-2.0)


def test_daily_trade_number_breakdown_in_summarize_combiner():
    df = pd.DataFrame(
        {
            "strategy": ["s"] * 4,
            "net_pnl": [1.0, -1.0, 1.0, -2.0],
            "r_multiple": [0.5, -0.5, 0.25, -1.0],
            "exit_reason": ["t", "s", "t", "s"],
            "bars_held": [1, 1, 1, 1],
            "daily_trade_number": [1, 1, 2, 2],
        }
    )
    m = summarize_combiner(df, pd.DataFrame(), pd.DataFrame())
    j = json.loads(m["trades_by_daily_trade_number_json"])
    assert j["1"] == 2
    assert j["2"] == 2
    rj = json.loads(m["r_by_daily_trade_number_json"])
    assert rj["1"] == pytest.approx(0.0)
    assert rj["2"] == pytest.approx(-0.75)
