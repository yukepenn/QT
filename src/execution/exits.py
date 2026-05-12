"""Intrabar exit detection helpers (no simulation loop).

Used by :mod:`src.execution.path` to keep the main loop readable.
"""

from __future__ import annotations

import math

from src.execution.types import AmbiguityPolicy, ExitReason, Side


def intrabar_stop_target_hit(
    *,
    side: int,
    high: float,
    low: float,
    stop: float,
    target: float | None,
    ambiguity: AmbiguityPolicy,
) -> tuple[bool, bool]:
    """Return ``(stop_hit, target_hit)`` for this bar's range.

    If ``target`` is ``None`` or non-finite, ``target_hit`` is ``False``.
    """
    del ambiguity
    if side == Side.LONG:
        stop_hit = low <= stop
        if target is None or not math.isfinite(float(target)):
            target_hit = False
        else:
            target_hit = high >= float(target)
    elif side == Side.SHORT:
        stop_hit = high >= stop
        if target is None or not math.isfinite(float(target)):
            target_hit = False
        else:
            target_hit = low <= float(target)
    else:
        raise ValueError("invalid side")
    return stop_hit, target_hit


def resolve_stop_target_order(
    stop_hit: bool, target_hit: bool, policy: AmbiguityPolicy
) -> ExitReason | None:
    """Pick stop vs target when both paths trade in the same bar."""
    if stop_hit and target_hit:
        if policy == AmbiguityPolicy.STOP_FIRST:
            return ExitReason.STOP
        return ExitReason.TARGET
    if stop_hit:
        return ExitReason.STOP
    if target_hit:
        return ExitReason.TARGET
    return None


def unrealized_r_touch_long(entry: float, high: float, risk: float) -> float:
    """Long: best-case R achievable if the bar touched ``high``."""
    if not (math.isfinite(entry) and math.isfinite(high) and math.isfinite(risk)) or risk <= 0:
        return float("nan")
    return (high - entry) / risk


def unrealized_r_touch_short(entry: float, low: float, risk: float) -> float:
    """Short: best-case R if the bar touched ``low``."""
    if not (math.isfinite(entry) and math.isfinite(low) and math.isfinite(risk)) or risk <= 0:
        return float("nan")
    return (entry - low) / risk


def scale_out_triggered_touch(
    *,
    side: int,
    entry: float,
    high: float,
    low: float,
    risk: float,
    trigger_r: float,
) -> bool:
    """Whether ``trigger_r`` is met on an intrabar *touch* (favorable extreme)."""
    if side == Side.LONG:
        return unrealized_r_touch_long(entry, high, risk) >= trigger_r
    if side == Side.SHORT:
        return unrealized_r_touch_short(entry, low, risk) >= trigger_r
    return False


def scale_out_trigger_price(*, side: int, entry: float, risk: float, trigger_r: float) -> float:
    """Price level at ``+trigger_r`` R (before slippage) for scale fill policy."""
    if side == Side.LONG:
        return float(entry) + float(trigger_r) * float(risk)
    return float(entry) - float(trigger_r) * float(risk)


def trailing_hit_long(low: float, trail_stop: float) -> bool:
    return math.isfinite(trail_stop) and low <= trail_stop


def trailing_hit_short(high: float, trail_stop: float) -> bool:
    return math.isfinite(trail_stop) and high >= trail_stop


def max_hold_exceeded(*, entry_bar_idx: int, current_bar_idx: int, max_hold_bars: int) -> bool:
    """Bars held inclusive of entry bar == ``current - entry + 1``."""
    return current_bar_idx - entry_bar_idx + 1 >= int(max_hold_bars)


def eod_triggered(minute: int, eod_exit_minute: int) -> bool:
    return int(minute) >= int(eod_exit_minute)
