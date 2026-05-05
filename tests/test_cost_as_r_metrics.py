"""Cost-as-R and execution-cost helpers in backtest metrics."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from src.backtest.metrics import (
    add_cost_r_column,
    estimate_round_trip_cost_per_share,
    profit_factor_r,
    summarize_cost_r,
)


def test_profit_factor_r_mixed():
    r = pd.Series([1.0, -1.0, 2.0, -0.5])
    assert profit_factor_r(r) == pytest.approx(2.0)


def test_profit_factor_r_all_winners():
    r = pd.Series([1.0, 0.5])
    assert profit_factor_r(r) == float("inf")


def test_profit_factor_r_all_flat():
    r = pd.Series([0.0, 0.0])
    assert profit_factor_r(r) == 0.0


def test_cost_r_slippage_only():
    df = pd.DataFrame({"risk_per_share": [0.04]})
    out = add_cost_r_column(df, 0.01, 0.0, 1.0)
    assert out["round_trip_cost_per_share"].iloc[0] == pytest.approx(0.02)
    assert out["cost_r"].iloc[0] == pytest.approx(0.5)


def test_cost_r_lower_risk_doubles_cost_r():
    df = pd.DataFrame({"risk_per_share": [0.02]})
    out = add_cost_r_column(df, 0.01, 0.0, 1.0)
    assert out["cost_r"].iloc[0] == pytest.approx(1.0)


def test_cost_r_with_commission():
    df = pd.DataFrame({"risk_per_share": [0.05]})
    out = add_cost_r_column(df, 0.01, 0.005, 1.0)
    assert out["round_trip_cost_per_share"].iloc[0] == pytest.approx(0.025)
    assert out["cost_r"].iloc[0] == pytest.approx(0.5)


def test_missing_risk_per_share_no_crash():
    df = pd.DataFrame({"net_pnl": [1.0]})
    out = add_cost_r_column(df, 0.01, 0.0, 1.0)
    assert np.isnan(out["cost_r"].iloc[0])
    s = summarize_cost_r(df, 0.01, 0.0, 1.0)
    assert math.isnan(s["avg_cost_r"])


def test_zero_risk_nan_cost_r():
    df = pd.DataFrame({"risk_per_share": [0.0]})
    out = add_cost_r_column(df, 0.01, 0.0, 1.0)
    assert np.isnan(out["cost_r"].iloc[0])
