from __future__ import annotations

import math

from src.execution.types import ExitReason, Side


def leg_r(side: int, entry: float, exit_px: float, risk: float) -> float:
    if not (math.isfinite(entry) and math.isfinite(exit_px) and math.isfinite(risk)) or risk <= 0:
        return float("nan")
    if side == Side.LONG:
        return (exit_px - entry) / risk
    if side == Side.SHORT:
        return (entry - exit_px) / risk
    return float("nan")


def weighted_r(legs) -> float:
    if not legs:
        return 0.0
    return sum(l.qty_frac * l.r_multiple for l in legs)


def apply_commission_per_share(
    gross_pnl_per_share: float, commission_per_trade: float, qty: float
) -> float:
    if not math.isfinite(gross_pnl_per_share):
        return float("nan")
    if qty <= 0 or not math.isfinite(qty):
        return float("nan")
    return gross_pnl_per_share - float(commission_per_trade) / float(qty)


def cost_as_r(commission_per_trade: float, qty: float, risk_per_share: float) -> float:
    if qty <= 0 or risk_per_share <= 0:
        return float("nan")
    return (commission_per_trade / qty) / risk_per_share
