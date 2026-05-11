"""Tests for walkforward aggregation metrics."""

from __future__ import annotations

import pandas as pd
import pytest

from src.walkforward.metrics import (
    compute_fold_concentration,
    compute_positive_fold_rate,
    compute_worst_fold_r,
    interpretation_flags,
    summarize_system_across_folds,
)


def test_positive_fold_rate():
    df = pd.DataFrame({"total_r": [1.0, -1.0, 2.0]})
    assert compute_positive_fold_rate(df) == pytest.approx(2 / 3)


def test_worst_fold_r():
    df = pd.DataFrame({"total_r": [1.0, -5.0, 2.0]})
    assert compute_worst_fold_r(df) == pytest.approx(-5.0)


def test_fold_concentration():
    df = pd.DataFrame({"total_r": [10.0, -2.0, 3.0]})
    c = compute_fold_concentration(df)
    assert c == pytest.approx(10.0 / 15.0)


def test_trade_2_positive_flag():
    df = pd.DataFrame(
        {
            "total_r": [1.0],
            "trade_2_total_r": [0.5],
            "profit_factor": [1.2],
            "profit_factor_r": [1.1],
            "slip_0_02_total_r": [0.5],
            "slip_0_02_pf": [1.1],
            "slip_0_03_total_r": [0.3],
            "slip_0_03_pf": [1.05],
        }
    )
    flags = interpretation_flags(df)
    assert flags["trade_2_positive"] is True


def test_system_summary_smoke():
    df = pd.DataFrame(
        [
            {
                "system_id": "s",
                "fold_id": "a",
                "total_r": 2.0,
                "profit_factor": 1.5,
                "profit_factor_r": 1.4,
                "max_drawdown_r": -3.0,
                "trades": 10,
                "slip_0_02_total_r": 1.0,
                "slip_0_02_pf": 1.2,
                "slip_0_03_total_r": 0.5,
                "slip_0_03_pf": 1.05,
            },
            {
                "system_id": "s",
                "fold_id": "b",
                "total_r": -1.0,
                "profit_factor": 0.9,
                "profit_factor_r": 0.85,
                "max_drawdown_r": -4.0,
                "trades": 5,
                "slip_0_02_total_r": -0.5,
                "slip_0_02_pf": 0.95,
                "slip_0_03_total_r": -1.0,
                "slip_0_03_pf": 0.9,
            },
        ]
    )
    out = summarize_system_across_folds(df)
    assert len(out) == 1
    assert out.iloc[0]["stitched_total_r"] == pytest.approx(1.0)
    assert out.iloc[0]["mean_fold_pf"] == pytest.approx(out.iloc[0]["stitched_pf"])
    assert out.iloc[0]["mean_fold_pf_r"] == pytest.approx(out.iloc[0]["stitched_pf_r"])
