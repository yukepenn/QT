"""Tests for Layer 1 v2 completion runner helpers."""

from src.research.run_layer1_v2_completion import grid_cap_policy, recommend_max_combos


def test_grid_cap_policy_small_full_grid() -> None:
    capped, mx, reason = grid_cap_policy(64)
    assert not capped
    assert mx is None
    assert "1500" in reason


def test_grid_cap_policy_mid_cap() -> None:
    capped, mx, reason = grid_cap_policy(2000)
    assert capped
    assert mx == 750
    assert "750" in reason


def test_grid_cap_policy_large_cap() -> None:
    capped, mx, reason = grid_cap_policy(6000)
    assert capped
    assert mx == 500


def test_recommend_max_combos_none_when_full() -> None:
    assert recommend_max_combos(100) is None
