"""Tests for exit/slip attribution overlay (no heavy trade files)."""
from __future__ import annotations

import math

import pandas as pd

from src.research.analyze_exit_slip_attribution import (
    aggregate,
    compute_row_adjustments,
    marginal_r_from_slip_delta,
    summarize_system,
)


def test_marginal_r_from_slip_delta_guard() -> None:
    assert marginal_r_from_slip_delta(0.0, 0.02) == 0.0
    assert marginal_r_from_slip_delta(float("nan"), 0.02) == 0.0
    assert math.isclose(marginal_r_from_slip_delta(0.5, 0.01), -0.02, rel_tol=0.001)


def test_compute_row_adjustments_target_vs_stop() -> None:
    r = 0.25
    t = compute_row_adjustments(r, "take_profit_limit")
    s = compute_row_adjustments(r, "stop_loss")
    assert t["target_limit_stress_vs_symmetric_r"] != 0.0
    assert s["stop_only_exit_extra_r"] != 0.0


def test_aggregate_columns() -> None:
    df = pd.DataFrame(
        {
            "r_multiple": [1.0, -0.5],
            "risk_per_share": [0.5, 0.5],
            "exit_reason": ["take_profit_limit", "stop_loss"],
        }
    )
    out = aggregate(df)
    for c in (
        "symmetric_stress_extra_r",
        "target_limit_stress_vs_symmetric_r",
        "symmetric_stress_r",
        "target_limit_adjusted_stress_r",
        "stop_only_stress_r",
    ):
        assert c in out.columns


def test_summarize_system_rowcount() -> None:
    df = pd.DataFrame(
        {
            "r_multiple": [1.0, 0.5],
            "risk_per_share": [0.5, 0.5],
            "exit_reason": ["target", "stop"],
        }
    )
    df = aggregate(df)
    sm = summarize_system(df, "unit")
    assert len(sm) == 5
    assert set(sm["scenario"]) == {
        "published",
        "symmetric_stress",
        "target_limit_stress",
        "target_limit_baseline_recover",
        "stop_only_stress",
    }


def test_build_indicator_mtp_skips_missing(tmp_path, capsys) -> None:
    from src.research.build_indicator_mtp_diagnostics import main

    m1 = tmp_path / "a_enriched.csv"
    pd.DataFrame({"r_multiple": [1.0], "entry_trade_number_of_day": [1]}).to_csv(m1, index=False)
    rc = main(
        [
            "--mtp1-enriched",
            str(m1),
            "--mtp2-enriched",
            str(tmp_path / "missing.csv"),
            "--mtp3-enriched",
            str(tmp_path / "missing2.csv"),
            "--output-root",
            str(tmp_path / "out"),
        ]
    )
    assert rc == 0
    cmp_path = tmp_path / "out" / "indicator_mtp_comparison.csv"
    assert cmp_path.exists()
    cmp_df = pd.read_csv(cmp_path)
    assert len(cmp_df) == 1
    err = capsys.readouterr().err
    assert "MISSING" in err
