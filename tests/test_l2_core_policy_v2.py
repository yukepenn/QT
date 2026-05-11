from __future__ import annotations

from src.research.audit_l2_candidates_oow_lib import policy_action_for_label


def test_high_turnover_maps_to_watchlist():
    assert policy_action_for_label("HIGH_TURNOVER_FRAGILE") == "WATCHLIST_DIAGNOSTIC"


def test_oow_negative_watchlist_not_drop():
    assert policy_action_for_label("OOW_NEGATIVE") == "WATCHLIST_DIAGNOSTIC"
