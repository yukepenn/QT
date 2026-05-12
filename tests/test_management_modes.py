"""Exit plans produced by management templates."""

from src.execution.types import ExitPlan
from src.management.modes import ManagementMode, exit_plan_for_mode


def _assert_plan(p: ExitPlan) -> None:
    assert isinstance(p, ExitPlan)


def test_fixed_r_plan():
    p = exit_plan_for_mode(ManagementMode.FIXED_R)
    _assert_plan(p)
    assert p.scale_outs == ()
    assert p.trailing is None


def test_scalp_tighter_cap_and_nft():
    p = exit_plan_for_mode(ManagementMode.SCALP)
    _assert_plan(p)
    assert p.max_hold_bars_cap == 12
    assert p.no_followthrough_bars == 3


def test_swing_plan():
    p = exit_plan_for_mode(ManagementMode.SWING)
    _assert_plan(p)


def test_runner_partial_and_trail():
    p = exit_plan_for_mode(ManagementMode.RUNNER)
    _assert_plan(p)
    assert len(p.scale_outs) == 1
    assert p.trailing is not None


def test_reversal_nft():
    p = exit_plan_for_mode(ManagementMode.REVERSAL)
    _assert_plan(p)
    assert p.no_followthrough_bars == 4
