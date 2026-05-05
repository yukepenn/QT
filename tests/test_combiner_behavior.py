"""Tests for generic combiner behavior hashing (no strategy-specific logic)."""

from __future__ import annotations

import pandas as pd

from src.combiner.behavior import behavior_hash_from_trades, behavior_summary_from_trades


def _base_trades() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "candidate_id": ["a", "a"],
            "entry_idx": [10, 20],
            "exit_idx": [11, 22],
            "side": [1, 1],
            "exit_reason": ["target", "stop"],
        }
    )


def test_identical_trades_same_hash():
    df = _base_trades()
    h1 = behavior_hash_from_trades(df)
    h2 = behavior_hash_from_trades(df.copy())
    assert h1 == h2


def test_changed_exit_idx_changes_hash():
    df1 = _base_trades()
    df2 = df1.copy()
    df2.loc[0, "exit_idx"] = 99
    assert behavior_hash_from_trades(df1) != behavior_hash_from_trades(df2)


def test_changed_candidate_id_changes_hash():
    df1 = _base_trades()
    df2 = df1.copy()
    df2.loc[0, "candidate_id"] = "b"
    assert behavior_hash_from_trades(df1) != behavior_hash_from_trades(df2)


def test_empty_trades_stable_hash():
    empty = pd.DataFrame(columns=["candidate_id", "entry_idx", "exit_idx", "side", "exit_reason"])
    h = behavior_hash_from_trades(empty)
    assert len(h) == 64
    assert behavior_hash_from_trades(pd.DataFrame()) == h


def test_behavior_summary_trade_count_and_candidate_json():
    df = _base_trades()
    s = behavior_summary_from_trades(df)
    assert s["behavior_trade_count"] == 2
    assert s["behavior_hash_quality"] == "strong"
    assert "a" in (s["candidate_ids_json"] or "")
