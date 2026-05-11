from __future__ import annotations

from src.execution.types import ExitReason, Side
from src.execution.types import AmbiguityPolicy


def entry_fill_price(open_price: float, side: int, slip: float) -> float:
    if side == Side.LONG:
        return float(open_price) + float(slip)
    if side == Side.SHORT:
        return float(open_price) - float(slip)
    raise ValueError("side must be ±1")


def exit_fill_price(raw_exit_price: float, side: int, reason: ExitReason, slip: float) -> float:
    _ = reason  # reserved for asymmetric slip models
    if side == Side.LONG:
        return float(raw_exit_price) - float(slip)
    if side == Side.SHORT:
        return float(raw_exit_price) + float(slip)
    raise ValueError("side must be ±1")
