"""Aggregated precompute profile summary CSV."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.combiner.precompute import write_precompute_profile_summary


def test_write_precompute_profile_summary_groups_and_hit_counts(tmp_path: Path) -> None:
    p = tmp_path / "candidate_precompute_profile.csv"
    pd.DataFrame(
        [
            {
                "candidate_id": "A",
                "strategy": "s1",
                "feature_key_short": "f1",
                "strategy_context_key_short": "c1",
                "feature_cache_hit": True,
                "context_cache_hit": False,
                "feature_sec": 0.1,
                "context_sec": 0.2,
                "signal_sec": 0.3,
                "total_sec": 1.0,
                "n_signals": 10,
                "n_long_signals": 6,
                "n_short_signals": 4,
            },
            {
                "candidate_id": "B",
                "strategy": "s1",
                "feature_key_short": "f1",
                "strategy_context_key_short": "c1",
                "feature_cache_hit": False,
                "context_cache_hit": True,
                "feature_sec": 0.2,
                "context_sec": 0.1,
                "signal_sec": 0.4,
                "total_sec": 2.0,
                "n_signals": 5,
                "n_long_signals": 3,
                "n_short_signals": 2,
            },
        ]
    ).to_csv(p, index=False)
    write_precompute_profile_summary(p)
    out = pd.read_csv(p.parent / "candidate_precompute_profile_summary.csv")
    assert len(out) == 1
    row = out.iloc[0]
    assert int(row["candidate_count"]) == 2
    assert int(row["n_feature_cache_hits"]) == 1
    assert int(row["n_feature_cache_misses"]) == 1
    assert int(row["n_context_cache_hits"]) == 1
    assert int(row["n_context_cache_misses"]) == 1
    assert float(row["sum_total_sec"]) == 3.0
    assert float(row["mean_total_sec"]) == 1.5
    assert float(row["max_total_sec"]) == 2.0
    assert int(row["total_signals"]) == 15
    md = (p.parent / "candidate_precompute_profile_summary.md").read_text(encoding="utf-8")
    assert "candidate_precompute_profile.csv" in md


def test_write_precompute_profile_summary_without_optional_timing_columns(tmp_path: Path) -> None:
    p = tmp_path / "candidate_precompute_profile.csv"
    pd.DataFrame(
        [
            {
                "candidate_id": "X",
                "strategy": "sx",
                "feature_key_short": "fx",
                "strategy_context_key_short": "cx",
                "total_sec": 4.0,
                "n_signals": 3,
            },
        ]
    ).to_csv(p, index=False)
    write_precompute_profile_summary(p)
    out = pd.read_csv(p.parent / "candidate_precompute_profile_summary.csv")
    assert len(out) == 1
    assert int(out.iloc[0]["candidate_count"]) == 1
    assert float(out.iloc[0]["sum_total_sec"]) == 4.0
    assert pd.isna(out.iloc[0]["sum_feature_sec"])
