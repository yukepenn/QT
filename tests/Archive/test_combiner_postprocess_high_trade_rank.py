"""Tests for rank_high_trade_systems postprocess output."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.combiner.postprocess import write_rank_high_trade_systems


def test_write_rank_high_trade_systems_sorts_and_caps(tmp_path: Path) -> None:
    systems = pd.DataFrame(
        {
            "combo_id": [1, 2, 3, 4],
            "candidate_set": ["a", "b", "c", "d"],
            "top_per_strategy": [1, 1, 1, 1],
            "trades": [500, 100, 450, 420],
            "total_r": [10.0, 99.0, 20.0, 25.0],
            "profit_factor": [1.1, 2.0, 1.15, 1.2],
            "max_drawdown_r": [-10.0, -5.0, -8.0, -7.0],
            "combiner_score": [1.0, 2.0, 1.5, 1.6],
        }
    )
    out = tmp_path / "out"
    write_rank_high_trade_systems(
        systems,
        out,
        min_trades_rank=400,
        rank_high_trade_top=2,
    )
    got = pd.read_csv(out / "rank_high_trade_systems.csv")
    assert len(got) == 2
    assert list(got["high_trade_rank"]) == [1, 2]
    # 450 trades, total_r=25 beats 420 trades, total_r=10; 100 trades filtered out
    assert got.iloc[0]["combo_id"] == 4
    assert got.iloc[1]["combo_id"] == 3
    assert (out / "rank_high_trade_systems.md").exists()


def test_write_rank_high_trade_systems_empty_when_below_min(tmp_path: Path) -> None:
    systems = pd.DataFrame({"combo_id": [1], "trades": [10], "total_r": [100.0]})
    out = tmp_path / "out2"
    write_rank_high_trade_systems(systems, out, min_trades_rank=400, rank_high_trade_top=30)
    got = pd.read_csv(out / "rank_high_trade_systems.csv")
    assert len(got) == 0
