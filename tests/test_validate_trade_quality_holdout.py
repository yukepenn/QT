"""Tests for calendar holdout helpers (synthetic scores; no heavy trade files)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.research.validate_trade_quality_holdout import (
    eval_split,
    subset_metrics,
    top_fraction_threshold,
    trade_two_stability,
)


def test_top_fraction_threshold_quantile() -> None:
    ts = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    thr = top_fraction_threshold(ts, 0.8)
    assert thr == float(np.quantile(ts, 0.2))


def test_eval_split_no_leakage_train_threshold() -> None:
    df = pd.DataFrame(
        {
            "session_date": ["2023-06-01", "2023-07-01", "2024-01-01", "2024-02-01"],
            "r_multiple": [1.0, -0.5, 0.5, 2.0],
            "trade_quality_score": [80.0, 40.0, 50.0, 90.0],
            "exit_reason": ["target", "stop", "target", "target"],
        }
    )
    y = pd.to_datetime(df["session_date"]).dt.year
    rows = eval_split(df, y == 2023, y == 2024, "test_split")
    subs = {r["subset"]: r for r in rows}
    thr = subs["test_split__test_top80_thr_train"]["train_score_threshold"]
    exp = float(np.quantile(np.array([40.0, 80.0]), 0.2))  # bottom 20% cutoff for "top 80%"
    assert thr == exp
    picked = df.loc[y == 2024].loc[df.loc[y == 2024, "trade_quality_score"] >= thr]
    assert len(picked) == 2  # both 2024 rows meet train-derived cutoff here


def test_subset_metrics_empty_and_flags() -> None:
    m = subset_metrics(pd.DataFrame(), "empty")
    assert m["trades"] == 0
    assert m["low_sample_warning"] is True


def test_trade_two_stability_writes(tmp_path) -> None:
    df = pd.DataFrame(
        {
            "session_date": ["2023-01-02", "2024-01-02"],
            "r_multiple": [0.5, 1.0],
            "entry_trade_number_of_day": [2, 2],
            "exit_reason": ["target", "target"],
        }
    )
    trade_two_stability(df, tmp_path)
    assert (tmp_path / "vwap_trade_number_stability.md").exists()
    assert (tmp_path / "vwap_trade_number_by_year_t2.csv").exists()


def test_taxonomy_load_for_add_scores(tmp_path) -> None:
    from src.research.validate_trade_quality_holdout import add_scores

    tax = Path(__file__).resolve().parents[1] / "src/research/results/trade_quality_router_v1/setup_taxonomy_v1.csv"
    if not tax.exists():
        # minimal taxonomy for CI machines without full results tree
        tax = tmp_path / "tax.csv"
        tax.write_text("family,setup_type,broader_class,example_strategies,likely_affinity_regimes,likely_avoid_regimes,notes\nvwap,x,y,z,a,b,c\n", encoding="utf-8")
    df = pd.DataFrame(
        {
            "session_date": ["2023-01-01"],
            "r_multiple": [1.0],
            "entry_regime_label": ["regime_unknown"],
            "entry_family": ["vwap"],
            "exit_reason": ["target"],
        }
    )
    out = add_scores(df, tax, None)
    assert "trade_quality_score" in out.columns
    assert 0 <= float(out["trade_quality_score"].iloc[0]) <= 100
