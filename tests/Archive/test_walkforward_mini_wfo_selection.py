"""Train-only system selection rules for mini-WFO."""

from __future__ import annotations

import json

import pandas as pd

from src.walkforward.mini_wfo_selection import (
    filter_eligible_train_systems,
    frozen_system_yaml_schema_keys,
    pick_best_row,
    selection_sort_score,
)


def test_primary_candidate_set_scores_higher_at_same_combiner_score() -> None:
    row_primary = pd.Series(
        {
            "combiner_score": 1.0,
            "total_r": 10.0,
            "max_drawdown_r": -10.0,
            "max_trades_per_day": 1,
            "candidate_set": "failed_gap",
            "candidate_ids_json": json.dumps(["A", "B"]),
        }
    )
    row_diag = pd.Series(
        {
            "combiner_score": 1.0,
            "total_r": 10.0,
            "max_drawdown_r": -10.0,
            "max_trades_per_day": 1,
            "candidate_set": "failed_gap_with_prior_day_diagnostic",
            "candidate_ids_json": json.dumps(["A", "B"]),
        }
    )
    sp = selection_sort_score(
        row_primary,
        primary_sets={"failed_gap"},
        diagnostic_sets={"failed_gap_with_prior_day_diagnostic"},
        penalize_relaxed=False,
        warnings_by_candidate={},
        slip002_total_r=1.0,
    )
    sd = selection_sort_score(
        row_diag,
        primary_sets={"failed_gap"},
        diagnostic_sets={"failed_gap_with_prior_day_diagnostic"},
        penalize_relaxed=False,
        warnings_by_candidate={},
        slip002_total_r=1.0,
    )
    assert sp > sd


def test_pick_best_prefers_primary_when_metrics_close() -> None:
    df = pd.DataFrame(
        [
            {
                "unique_rank": 1,
                "candidate_set": "failed_only",
                "combiner_score": 5.0,
                "total_r": 12.0,
                "profit_factor_r": 1.2,
                "max_drawdown_r": -10.0,
                "trades": 120,
                "candidate_ids_json": json.dumps(["X"]),
            },
            {
                "unique_rank": 2,
                "candidate_set": "failed_gap_with_prior_day_diagnostic",
                "combiner_score": 5.2,
                "total_r": 13.0,
                "profit_factor_r": 1.2,
                "max_drawdown_r": -10.0,
                "trades": 120,
                "candidate_ids_json": json.dumps(["X"]),
            },
        ]
    )
    cost_df = pd.DataFrame(
        [
            {"unique_rank": 1, "slippage_per_share": 0.02, "total_r": 2.0},
            {"unique_rank": 2, "slippage_per_share": 0.02, "total_r": 2.5},
        ]
    )
    sel = {
        "require_min_trades": 80,
        "require_positive_total_r": True,
        "require_pf_r_above_1": True,
        "require_cost_0_02_positive": True,
        "max_drawdown_r_floor": -50.0,
        "penalize_relaxed_candidates": False,
    }
    best, audit = pick_best_row(
        df,
        primary_sets=["failed_only", "gap_only", "failed_gap"],
        diagnostic_sets=["failed_gap_with_prior_day_diagnostic"],
        sel=sel,
        warnings_by_candidate={},
        cost_df=cost_df,
    )
    assert best is not None
    assert best["candidate_set"] == "failed_only"
    assert audit["after_hard_filters"] == 2


def test_empty_candidates_fail_filter() -> None:
    empty = filter_eligible_train_systems(
        pd.DataFrame(),
        sel={"require_min_trades": 80},
        cost_slip_002_by_unique_rank=None,
        warnings_by_candidate={},
    )
    assert len(empty) == 0


def test_frozen_schema_keys_stable() -> None:
    assert "candidate_ids" in frozen_system_yaml_schema_keys()
    assert "live_ready" in frozen_system_yaml_schema_keys()
