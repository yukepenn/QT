"""PnL and R-multiple helpers (no bar loop).

Commission is modeled as **one round-trip charge per trade**, divided evenly
across ``intent.qty`` shares for reporting ``net_pnl_per_share``. Partial legs
do **not** each pay full commission again; see ``docs/EXECUTION_SEMANTICS.md``.
"""

from __future__ import annotations

import math
from typing import Iterable

from src.execution.types import FillLeg, Side


def leg_r(side: int, entry: float, exit_px: float, risk: float) -> float:
    """R multiple for a single leg using **initial** risk per share."""
    if not (math.isfinite(entry) and math.isfinite(exit_px) and math.isfinite(risk)) or risk <= 0:
        return float("nan")
    if side == Side.LONG:
        return (exit_px - entry) / risk
    if side == Side.SHORT:
        return (entry - exit_px) / risk
    return float("nan")


def weighted_r(legs: Iterable[FillLeg]) -> float:
    """Total R = Σ ``qty_frac × leg_r`` (initial risk denominator)."""
    legs = tuple(legs)
    if not legs:
        return 0.0
    return float(sum(leg.qty_frac * leg.r_multiple for leg in legs))


def gross_pnl_per_share(*, side: int, entry: float, exit_px: float) -> float:
    """Signed gross PnL per share for a full exit (no partial weighting)."""
    if side == Side.LONG:
        return float(exit_px) - float(entry)
    if side == Side.SHORT:
        return float(entry) - float(exit_px)
    return float("nan")


def net_pnl_per_share_from_gross(
    gross_pnl_per_share: float, commission_per_trade: float, qty: float
) -> float:
    """Subtract allocated commission / ``qty`` from gross PnL/share."""
    return apply_commission_per_share(gross_pnl_per_share, commission_per_trade, qty)


def apply_commission_per_share(
    gross_pnl_per_share: float, commission_per_trade: float, qty: float
) -> float:
    if not math.isfinite(gross_pnl_per_share):
        return float("nan")
    if qty <= 0 or not math.isfinite(qty):
        return float("nan")
    return float(gross_pnl_per_share) - float(commission_per_trade) / float(qty)


def cost_as_r(commission_per_trade: float, qty: float, risk_per_share: float) -> float:
    if qty <= 0 or risk_per_share <= 0:
        return float("nan")
    return (commission_per_trade / qty) / risk_per_share


def net_r_multiple_from_net_pnl(net_pnl_per_share: float, risk_per_share: float) -> float:
    """Net R = net PnL/share ÷ initial risk (commission reflected in net PnL)."""
    if not math.isfinite(net_pnl_per_share) or not math.isfinite(risk_per_share) or risk_per_share <= 0:
        return float("nan")
    return float(net_pnl_per_share) / float(risk_per_share)
