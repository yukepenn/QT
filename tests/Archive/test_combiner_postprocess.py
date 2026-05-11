"""Postprocess helpers: config dedupe, behavior dedupe."""

from __future__ import annotations

import pandas as pd

from src.combiner.behavior import dedupe_behavior_rows
from src.combiner.postprocess import dedupe_sweep_from_results


def test_dedupe_behavior_rows_keeps_best_score():
    df = pd.DataFrame(
        {
            "behavior_hash": ["x", "x"],
            "combiner_score": [5.0, 4.0],
            "total_r": [10.0, 99.0],
            "profit_factor_r": [1.0, 2.0],
        }
    )
    out = dedupe_behavior_rows(df)
    assert len(out) == 1
    assert float(out.iloc[0]["combiner_score"]) == 5.0


def test_dedupe_behavior_rows_distinct_hashes_preserved():
    df = pd.DataFrame(
        {
            "behavior_hash": ["x", "y"],
            "combiner_score": [1.0, 2.0],
            "total_r": [1.0, 2.0],
        }
    )
    out = dedupe_behavior_rows(df)
    assert len(out) == 2


def test_dedupe_sweep_from_results_key():
    df = pd.DataFrame(
        [
            {
                "candidate_set": "a",
                "top_per_strategy": 1,
                "max_trades_per_day": 2,
                "daily_max_loss_r": -2.0,
                "cooldown_after_loss_minutes": 0,
                "priority_policy": "metadata_priority",
                "candidate_ids_json": '["c1"]',
                "combiner_score": 10.0,
                "profit_factor": 2.0,
                "total_r": 5.0,
            },
            {
                "candidate_set": "a",
                "top_per_strategy": 1,
                "max_trades_per_day": 2,
                "daily_max_loss_r": -2.0,
                "cooldown_after_loss_minutes": 0,
                "priority_policy": "metadata_priority",
                "candidate_ids_json": '["c1"]',
                "combiner_score": 20.0,
                "profit_factor": 3.0,
                "total_r": 9.0,
            },
            {
                "candidate_set": "b",
                "top_per_strategy": 1,
                "max_trades_per_day": 2,
                "daily_max_loss_r": -2.0,
                "cooldown_after_loss_minutes": 0,
                "priority_policy": "metadata_priority",
                "candidate_ids_json": '["c1"]',
                "combiner_score": 1.0,
                "profit_factor": 1.5,
                "total_r": 1.0,
            },
        ]
    )
    out = dedupe_sweep_from_results(df)
    assert len(out) == 2
