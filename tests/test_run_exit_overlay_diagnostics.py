"""Tests for exit overlay diagnostics runner helpers (no heavy panel)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd

from src.research.run_exit_overlay_diagnostics import (
    _sanitize_path,
    aggregate_slice,
    attach_labels,
    choose_decision,
    main,
)


def test_sanitize_path_strips_home() -> None:
    fake = str(Path.home() / "secret" / "proj")
    s = _sanitize_path(fake)
    assert s.startswith("~")


def test_aggregate_and_labels() -> None:
    sim = pd.DataFrame(
        {
            "profile_id": ["a", "a", "a", "a"],
            "window": ["late_oow", "late_oow", "insample_ref", "insample_ref"],
            "overlay_id": ["x", "x", "x", "x"],
            "r_original": [1.0, -1.0, 0.5, 0.5],
            "r_overlay": [1.1, -0.9, 0.4, 0.6],
            "session_date": ["2024-01-02"] * 4,
            "ambiguous_bar": [False] * 4,
            "changed_exit_vs_replay": [True, False, False, False],
            "weak_period_flag": [False, False, False, False],
            "signal_ts_utc": pd.date_range("2024-01-02", periods=4, freq="h", tz="UTC"),
        }
    )
    out = attach_labels(aggregate_slice(sim, ["profile_id", "window", "overlay_id"]), sim)
    assert "label" in out.columns
    assert len(out) == 2


def test_choose_decision_replay_sanity_gate() -> None:
    df = pd.DataFrame({"window": ["early_oow"], "label": ["EXIT_OVERLAY_PROMISING"]})
    san_bad = pd.DataFrame({"mean_abs_r_diff": [0.5]})
    assert choose_decision(df, san_bad) == "RUN_EXIT_OVERLAY_DIAGNOSTICS_V2"


def test_choose_decision_router_fallback() -> None:
    df = pd.DataFrame({"window": ["full_available"], "label": ["EXIT_OVERLAY_NO_IMPROVEMENT"]})
    san_ok = pd.DataFrame({"mean_abs_r_diff": [0.01]})
    assert choose_decision(df, san_ok) == "RETURN_TO_LAYER2_ROUTER_INTEGRATION_DESIGN"


def test_main_dry_run() -> None:
    with tempfile.TemporaryDirectory() as td:
        panel = Path(td) / "panel.csv"
        panel.write_text("profile_id,window\nx,early_oow\n", encoding="utf-8")
        out = Path(td) / "out"
        code = main(
            [
                "--local-panel",
                str(panel),
                "--router-quality-root",
                "src/research/results/router_quality_refinement_v2",
                "--output-root",
                str(out),
                "--dry-run",
            ]
        )
        assert code == 0
        assert (out / "dry_run_plan.csv").is_file()
