"""Pure-helper tests for Layer2 candidate OOW audit lib."""
from __future__ import annotations

import pandas as pd

from src.research.audit_l2_candidates_oow_lib import (
    assign_robustness_label,
    family_label_counts,
    merge_metrics_for_labels,
    policy_action_for_label,
)


def test_assign_robustness_robust_positive():
    lab = assign_robustness_label(
        insample_r=20.0,
        early_r=2.0,
        late_r=1.0,
        insample_n=50,
        early_n=50,
        late_n=50,
        avg_r_in=0.1,
        tpd_in=0.5,
    )
    assert lab == "ROBUST_POSITIVE"


def test_assign_robustness_insample_only():
    lab = assign_robustness_label(
        insample_r=20.0,
        early_r=-10.0,
        late_r=-10.0,
        insample_n=50,
        early_n=50,
        late_n=50,
        avg_r_in=0.1,
        tpd_in=0.5,
    )
    assert lab == "INSAMPLE_ONLY"


def test_assign_robustness_too_sparse():
    lab = assign_robustness_label(
        insample_r=20.0,
        early_r=2.0,
        late_r=1.0,
        insample_n=5,
        early_n=50,
        late_n=50,
        avg_r_in=0.1,
        tpd_in=0.5,
    )
    assert lab == "TOO_SPARSE"


def test_assign_robustness_nan_r():
    x = float("nan")
    lab = assign_robustness_label(
        insample_r=x,
        early_r=2.0,
        late_r=1.0,
        insample_n=50,
        early_n=50,
        late_n=50,
        avg_r_in=0.1,
        tpd_in=0.5,
    )
    assert lab == "TOO_SPARSE"


def test_merge_metrics_for_labels_and_family_counts():
    rows = [
        {
            "candidate_id": "A",
            "window_id": "insample_ref",
            "status": "OK",
            "strategy": "vwap_reclaim_reject",
            "strategy_family": "vwap",
            "yaml_path": "p/A.yaml",
            "selection_score": 1.0,
            "warning": "",
            "side": "long",
            "audit_family": "vwap",
            "trades": 40,
            "total_r": 20.0,
            "avg_r": 0.1,
            "trades_per_day": 0.5,
        },
        {
            "candidate_id": "A",
            "window_id": "early_oow",
            "status": "OK",
            "strategy": "vwap_reclaim_reject",
            "strategy_family": "vwap",
            "yaml_path": "p/A.yaml",
            "selection_score": 1.0,
            "warning": "",
            "side": "long",
            "audit_family": "vwap",
            "trades": 40,
            "total_r": 2.0,
            "avg_r": 0.05,
            "trades_per_day": 0.5,
        },
        {
            "candidate_id": "A",
            "window_id": "late_oow",
            "status": "OK",
            "strategy": "vwap_reclaim_reject",
            "strategy_family": "vwap",
            "yaml_path": "p/A.yaml",
            "selection_score": 1.0,
            "warning": "",
            "side": "long",
            "audit_family": "vwap",
            "trades": 40,
            "total_r": 1.0,
            "avg_r": 0.05,
            "trades_per_day": 0.5,
        },
    ]
    long_df = pd.DataFrame(rows)
    wide = merge_metrics_for_labels(long_df)
    assert len(wide) == 1
    assert wide.iloc[0]["robustness_label"] == "ROBUST_POSITIVE"
    fam = family_label_counts(wide)
    assert not fam.empty
    assert fam.iloc[0]["audit_family"] == "vwap"


def test_merge_metrics_includes_candidate_with_missing_windows():
    nan = float("nan")
    rows = [
        {
            "candidate_id": "B",
            "window_id": "insample_ref",
            "status": "OK",
            "strategy": "failed_orb",
            "strategy_family": "orb",
            "yaml_path": "p/B.yaml",
            "selection_score": None,
            "warning": "",
            "side": "long",
            "audit_family": "opening_trap",
            "trades": 40,
            "total_r": 10.0,
            "avg_r": 0.1,
            "trades_per_day": 0.5,
        },
        {
            "candidate_id": "B",
            "window_id": "early_oow",
            "status": "MISSING",
            "strategy": "failed_orb",
            "strategy_family": "orb",
            "yaml_path": "p/B.yaml",
            "selection_score": None,
            "warning": "",
            "side": "long",
            "audit_family": "opening_trap",
            "trades": 0,
            "total_r": nan,
            "avg_r": nan,
            "trades_per_day": 0.0,
        },
        {
            "candidate_id": "B",
            "window_id": "late_oow",
            "status": "MISSING",
            "strategy": "failed_orb",
            "strategy_family": "orb",
            "yaml_path": "p/B.yaml",
            "selection_score": None,
            "warning": "",
            "side": "long",
            "audit_family": "opening_trap",
            "trades": 0,
            "total_r": nan,
            "avg_r": nan,
            "trades_per_day": 0.0,
        },
    ]
    long_df = pd.DataFrame(rows)
    wide = merge_metrics_for_labels(long_df)
    assert len(wide) == 1
    assert wide.iloc[0]["robustness_label"] == "TOO_SPARSE"


def test_policy_action_no_oow_tuning_leakage():
    """Policy maps labels to triage strings only (no window-specific tuning)."""
    assert policy_action_for_label("ROBUST_POSITIVE") == "KEEP_CORE_CANDIDATE"
    assert policy_action_for_label("INSAMPLE_ONLY") == "DROP_FROM_CORE"
    assert policy_action_for_label("ANTI_PREDICTIVE_CANDIDATE") == "REQUIRES_SIDE_FLIP_RESEARCH"
