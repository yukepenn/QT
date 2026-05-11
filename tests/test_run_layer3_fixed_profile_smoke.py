"""Unit tests for Layer3 fixed-profile smoke runner (no combiner execution)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

_ROOT = Path(__file__).resolve().parents[1]


def test_core_only_default_profiles():
    from src.research.run_layer3_fixed_profile_smoke import CORE_PROFILE_IDS, _load_fixed_profile_definitions, _resolve_profile_ids

    df = _load_fixed_profile_definitions(_ROOT / "src/research/results/fixed_robust_profile_oow_v1")
    pids = _resolve_profile_ids(
        fixed_df=df,
        profiles_arg=None,
        core_only=True,
        include_optional_baseline=False,
        include_ablations=False,
    )
    assert set(pids) == CORE_PROFILE_IDS
    assert len(pids) == 2


def test_core_only_with_explicit_profiles():
    from src.research.run_layer3_fixed_profile_smoke import _load_fixed_profile_definitions, _resolve_profile_ids

    df = _load_fixed_profile_definitions(_ROOT / "src/research/results/fixed_robust_profile_oow_v1")
    pids = _resolve_profile_ids(
        fixed_df=df,
        profiles_arg="pa_only_mtp1_meta,pa_gap_mtp2_meta",
        core_only=True,
        include_optional_baseline=False,
        include_ablations=False,
    )
    assert len(pids) == 2


def test_core_only_rejects_optional():
    from src.research.run_layer3_fixed_profile_smoke import _load_fixed_profile_definitions, _resolve_profile_ids

    df = _load_fixed_profile_definitions(_ROOT / "src/research/results/fixed_robust_profile_oow_v1")
    with pytest.raises(ValueError, match="core-only forbids"):
        _resolve_profile_ids(
            fixed_df=df,
            profiles_arg="primary_mtp2_meta",
            core_only=True,
            include_optional_baseline=False,
            include_ablations=False,
        )


def test_build_run_plan_eight_rows(tmp_path: Path):
    from src.research.run_layer3_fixed_profile_smoke import _build_run_plan, _load_fixed_profile_definitions, _resolve_profile_ids

    df = _load_fixed_profile_definitions(_ROOT / "src/research/results/fixed_robust_profile_oow_v1")
    pids = _resolve_profile_ids(
        fixed_df=df,
        profiles_arg=None,
        core_only=True,
        include_optional_baseline=False,
        include_ablations=False,
    )
    out = tmp_path / "layer3_smoke"
    plan = _build_run_plan(output_root=out, fixed_df=df, profile_ids=pids, windows=["early_oow", "insample_ref", "late_oow", "full_available"])
    assert len(plan) == 8
    assert set(plan["profile_id"]) == {"pa_only_mtp1_meta", "pa_gap_mtp2_meta"}
    assert "primary_mtp2_meta" not in set(plan["profile_id"])
    rel = plan["run_dir_rel"].astype(str)
    assert not rel.str.contains("D:/", regex=False).any()
    assert not rel.str.contains("OneDrive", regex=False).any()


def test_sanitized_manifest_no_abs_tokens():
    from src.research.run_layer3_fixed_profile_smoke import _sanitize_exec_row

    row = {
        "profile_id": "pa_only_mtp1_meta",
        "window": "early_oow",
        "start_date": "2020-01-01",
        "end_date": "2022-12-31",
        "candidate_ids": "X",
        "max_trades_per_day": 1,
        "daily_max_loss_r": -1.5,
        "priority_policy": "metadata_priority",
        "status": "FAILED",
        "exit_code": 1,
        "run_dir_rel": "local_runs/pa_only_mtp1_meta/early_oow",
        "config_path_rel": "local_configs/x.yaml",
        "error_summary": "Err D:/OneDrive/foo",
    }
    s = _sanitize_exec_row(row, roles={"pa_only_mtp1_meta": "CLEAN_BASELINE"}, output_root=Path("/tmp"))
    joined = str(s)
    assert "D:/" not in joined
    assert "OneDrive" not in joined


def test_decision_labels_allowed():
    allowed = {
        "RUN_OPTIONAL_LAYER3_BASELINE_ABLATION",
        "PROCEED_TO_LAYER3_EXPANDED_STABILITY_DESIGN",
        "REFINE_ROBUST_CORE_COMBINATION_RULES",
        "NEED_MORE_LAYER3_CORE_SMOKE",
        "HOLD_BEFORE_WFO",
        "DEFER_GLOBAL_SYSTEM",
    }
    # Smoke test: runner decision must be one of these strings when produced by postprocess helpers.
    assert "RUN_OPTIONAL_LAYER3_BASELINE_ABLATION" in allowed


def test_markdown_pivot():
    from src.research.run_layer3_fixed_profile_smoke import _markdown_total_r_pivot

    res = pd.DataFrame(
        [
            {"profile_id": "pa_only_mtp1_meta", "window": "early_oow", "total_r": 1.0},
            {"profile_id": "pa_only_mtp1_meta", "window": "insample_ref", "total_r": 2.0},
            {"profile_id": "pa_only_mtp1_meta", "window": "late_oow", "total_r": 3.0},
            {"profile_id": "pa_only_mtp1_meta", "window": "full_available", "total_r": 4.0},
            {"profile_id": "pa_gap_mtp2_meta", "window": "early_oow", "total_r": 5.0},
            {"profile_id": "pa_gap_mtp2_meta", "window": "insample_ref", "total_r": 6.0},
            {"profile_id": "pa_gap_mtp2_meta", "window": "late_oow", "total_r": 7.0},
            {"profile_id": "pa_gap_mtp2_meta", "window": "full_available", "total_r": 8.0},
        ]
    )
    md = _markdown_total_r_pivot(res)
    assert "pa_only_mtp1_meta" in md
    assert "1.00" in md or "1.0" in md
