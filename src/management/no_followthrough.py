"""No-followthrough exit presets."""

from __future__ import annotations

from src.execution.types import ExitPlan


def nft_after_bars(bars: int, min_r: float) -> ExitPlan:
    return ExitPlan(no_followthrough_bars=int(bars), no_followthrough_min_r=float(min_r))
