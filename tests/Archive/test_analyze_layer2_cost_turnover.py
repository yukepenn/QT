"""Tests for Layer 2 cost/turnover analysis helpers."""

from __future__ import annotations

import math

from src.combiner.analyze_layer2_cost_turnover import (
    cost_adjusted_objective,
    decompose_combiner_score_public_terms,
    pivot_cost_stress,
    recombiner_from_terms,
    strategy_from_candidate_id,
    stress_labels,
)
from src.combiner.metrics import combiner_score


def test_decompose_matches_combiner_score_with_full_metrics() -> None:
    m = {
        "trades": 200,
        "profit_factor": 1.2,
        "total_r": 40.0,
        "max_drawdown_r": -10.0,
        "avg_bars_held": 7.5,
        "max_hold_count": 5,
        "eod_count": 1,
        "end_of_session_count": 0,
        "end_of_data_count": 0,
    }
    score, _ = combiner_score(m)
    terms = decompose_combiner_score_public_terms(
        profit_factor=m["profit_factor"],
        total_r=m["total_r"],
        max_drawdown_r=m["max_drawdown_r"],
        avg_bars_held=m["avg_bars_held"],
        max_hold_count=m["max_hold_count"],
        eod_count=m["eod_count"],
        end_of_session_count=m["end_of_session_count"],
        end_of_data_count=m["end_of_data_count"],
        trades=m["trades"],
    )
    assert math.isclose(recombiner_from_terms(terms), score, rel_tol=0, abs_tol=1e-9)


def test_strategy_from_candidate_id() -> None:
    assert strategy_from_candidate_id("VWAP_RECLAIM_REJECT_001") == "vwap_reclaim_reject"
    assert strategy_from_candidate_id("CCI_EXTREME_SNAPBACK_004") == "cci_extreme_snapback"


def test_stress_labels_pass_fail() -> None:
    d = stress_labels(40.0, 10.0, -5.0, 1.2, 1.08, 0.95)
    assert d["PASS_0_02"] is True
    assert d["FAIL_0_03"] is True


def test_cost_adjusted_objective_monotone_in_tr_at_002() -> None:
    a = cost_adjusted_objective(
        total_r_001=40,
        pf_001=1.2,
        total_r_002=5,
        pf_002=1.06,
        total_r_003=-1,
        pf_003=0.9,
        trades=300,
        max_drawdown_r_001=-10,
        family_diversity_count=2,
    )
    b = cost_adjusted_objective(
        total_r_001=40,
        pf_001=1.2,
        total_r_002=15,
        pf_002=1.12,
        total_r_003=-1,
        pf_003=0.9,
        trades=300,
        max_drawdown_r_001=-10,
        family_diversity_count=2,
    )
    assert b > a


def test_pivot_cost_stress_roundtrip(tmp_path) -> None:
    import pandas as pd

    df = pd.DataFrame(
        [
            {"source_combo_id": 1, "slippage_per_share": 0.01, "total_r": 10.0, "profit_factor": 1.1, "max_drawdown_r": -5.0, "trades": 100},
            {"source_combo_id": 1, "slippage_per_share": 0.02, "total_r": 4.0, "profit_factor": 1.04, "max_drawdown_r": -8.0, "trades": 100},
            {"source_combo_id": 1, "slippage_per_share": 0.03, "total_r": -1.0, "profit_factor": 0.95, "max_drawdown_r": -12.0, "trades": 100},
        ]
    )
    p = tmp_path / "cost_stress_results.csv"
    df.to_csv(p, index=False)
    out = pivot_cost_stress(p)
    assert len(out) == 1
    assert math.isclose(float(out.iloc[0]["total_r_0.01"]), 10.0)
    assert math.isclose(float(out.iloc[0]["total_r_0.02"]), 4.0)
