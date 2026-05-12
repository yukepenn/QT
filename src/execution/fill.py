"""Entry and exit fill prices with explicit slippage direction.

Slippage is applied **once** per fill. See ``docs/EXECUTION_SEMANTICS.md``.
"""

from __future__ import annotations

from src.execution.types import ExitReason, Side


def entry_fill_price(open_price: float, side: int, slip: float) -> float:
    """Next-bar open fill with slippage (long pays up, short receives less)."""
    o = float(open_price)
    s = float(slip)
    if side == Side.LONG:
        return o + s
    if side == Side.SHORT:
        return o - s
    raise ValueError("side must be Side.LONG or Side.SHORT")


def raw_exit_price_for_reason(
    *,
    reason: ExitReason,
    stop_price: float,
    target_price: float,
    trail_price: float,
    close: float,
) -> float:
    """Price level **before** slippage for structured exits."""
    if reason in (ExitReason.STOP,):
        return float(stop_price)
    if reason in (ExitReason.TARGET,):
        return float(target_price)
    if reason in (ExitReason.TRAILING,):
        return float(trail_price)
    return float(close)


def is_price_level_exit(reason: ExitReason) -> bool:
    return reason in (ExitReason.STOP, ExitReason.TARGET, ExitReason.TRAILING)


def is_time_based_exit(reason: ExitReason) -> bool:
    """Exits that use the bar close (or end-of-data close) as raw price."""
    return reason in (
        ExitReason.MAX_HOLD,
        ExitReason.EOD,
        ExitReason.END_SESSION,
        ExitReason.END_DATA,
        ExitReason.NO_FOLLOWTHROUGH,
        ExitReason.SCALE_OUT,
    )


def exit_fill_price(raw_exit_price: float, side: int, reason: ExitReason, slip: float) -> float:
    """Apply slippage for exit. Price-level and time-based use the same sign map."""
    _ = reason
    r = float(raw_exit_price)
    s = float(slip)
    if side == Side.LONG:
        return r - s
    if side == Side.SHORT:
        return r + s
    raise ValueError("side must be Side.LONG or Side.SHORT")
