"""Exit management templates (not router logic)."""

from __future__ import annotations

from enum import Enum

from src.execution.types import ExitPlan, ScaleOutRule, TrailingRule


class ManagementMode(str, Enum):
    FIXED_R = "fixed_r"
    SCALP = "scalp"
    SWING = "swing"
    RUNNER = "runner"
    REVERSAL = "reversal"


def exit_plan_for_mode(mode: ManagementMode) -> ExitPlan:
    """Return a conservative default plan per mode (tunable later)."""
    if mode == ManagementMode.FIXED_R:
        return ExitPlan()
    if mode == ManagementMode.SCALP:
        return ExitPlan(no_followthrough_bars=3, no_followthrough_min_r=0.0)
    if mode == ManagementMode.SWING:
        return ExitPlan()
    if mode == ManagementMode.RUNNER:
        return ExitPlan(
            scale_outs=(ScaleOutRule(trigger_r=1.0, exit_fraction=0.5),),
            trailing=TrailingRule(distance_r=0.5),
        )
    if mode == ManagementMode.REVERSAL:
        return ExitPlan(no_followthrough_bars=4, no_followthrough_min_r=-0.25)
    return ExitPlan()
