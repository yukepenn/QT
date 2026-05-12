"""Metrics aggregation does not recompute trade R."""

import pandas as pd
import pytest

from src.backtest.metrics import summarize_trades


def test_summarize_uses_r_multiple_and_total_gross_r():
    df = pd.DataFrame(
        {
            "net_pnl": [1.0, -0.5],
            "r_multiple": [0.9, -0.4],
            "gross_r_multiple": [1.0, -0.4],
            "bars_held": [3, 2],
            "exit_reason": ["target", "stop"],
            "risk_per_share": [1.0, 1.0],
            "session_date": ["2024-01-01", "2024-01-01"],
        }
    )
    s = summarize_trades(df)
    assert s["total_r"] == pytest.approx(0.5)
    assert s["total_gross_r"] == pytest.approx(0.6)
