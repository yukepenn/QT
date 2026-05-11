from __future__ import annotations

import pandas as pd

from src.research.audit_l2_candidates_oow_report import robust_core_dry_run_decision
from src.research.audit_l2_candidates_oow_lib import policy_action_for_label


def test_robust_core_rejects_small_pool():
    labels = pd.DataFrame(
        [
            {
                "candidate_id": "X1",
                "audit_family": "indicator",
                "policy_action": "KEEP_CORE_CANDIDATE",
                "total_r_early_oow": 1.0,
                "total_r_late_oow": 1.0,
            },
            {
                "candidate_id": "X2",
                "audit_family": "indicator",
                "policy_action": "KEEP_CORE_CANDIDATE",
                "total_r_early_oow": 2.0,
                "total_r_late_oow": 2.0,
            },
        ]
    )
    ok, reason, _ = robust_core_dry_run_decision(labels, min_candidates=6)
    assert ok is False
    assert "KEEP_CORE count" in reason


def test_high_turnover_maps_to_watchlist():
    assert policy_action_for_label("HIGH_TURNOVER_FRAGILE") == "WATCHLIST_DIAGNOSTIC"


def test_oow_negative_watchlist_not_drop():
    assert policy_action_for_label("OOW_NEGATIVE") == "WATCHLIST_DIAGNOSTIC"


def test_robust_core_accepts_diverse_pool():
    rows = []
    for i in range(4):
        rows.append(
            {
                "candidate_id": f"GAP_{i}",
                "audit_family": "opening_trap",
                "policy_action": "KEEP_CORE_CANDIDATE",
                "total_r_early_oow": 5.0,
                "total_r_late_oow": 5.0,
            }
        )
    for i in range(4):
        rows.append(
            {
                "candidate_id": f"PA_{i}",
                "audit_family": "pa",
                "policy_action": "KEEP_CORE_CANDIDATE",
                "total_r_early_oow": 10.0,
                "total_r_late_oow": 3.0,
            }
        )
    rows.append(
        {
            "candidate_id": "CCI_1",
            "audit_family": "indicator",
            "policy_action": "KEEP_CORE_CANDIDATE",
            "total_r_early_oow": 2.0,
            "total_r_late_oow": 2.0,
        }
    )
    rows.append(
        {
            "candidate_id": "CCI_2",
            "audit_family": "indicator",
            "policy_action": "KEEP_CORE_CANDIDATE",
            "total_r_early_oow": 1.0,
            "total_r_late_oow": 4.0,
        }
    )
    labels = pd.DataFrame(rows)
    ok, reason, keep = robust_core_dry_run_decision(labels, min_candidates=6, min_families=2, max_family_share=0.55)
    assert ok is True
    assert "thresholds" in reason
    assert len(keep) == 10
