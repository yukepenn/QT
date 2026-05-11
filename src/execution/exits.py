from __future__ import annotations

from src.execution.types import AmbiguityPolicy, ExitReason, Side


def intrabar_stop_target_hit(
    *,
    side: int,
    high: float,
    low: float,
    stop: float,
    target: float,
    ambiguity: AmbiguityPolicy,
) -> tuple[bool, bool]:
    """Return (stop_hit, target_hit). ambiguity reserved for extensions."""
    _ = ambiguity
    if side == Side.LONG:
        stop_hit = low <= stop
        target_hit = high >= target
    elif side == Side.SHORT:
        stop_hit = high >= stop
        target_hit = low <= target
    else:
        raise ValueError("invalid side")
    return stop_hit, target_hit


def resolve_stop_target_order(
    stop_hit: bool, target_hit: bool, policy: AmbiguityPolicy
) -> ExitReason | None:
    if stop_hit and target_hit:
        if policy == AmbiguityPolicy.STOP_FIRST:
            return ExitReason.STOP
        return ExitReason.TARGET
    if stop_hit:
        return ExitReason.STOP
    if target_hit:
        return ExitReason.TARGET
    return None
