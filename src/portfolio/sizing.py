"""Position sizing helpers (generic)."""

from __future__ import annotations


def shares_for_fixed_risk(equity: float, risk_frac: float, risk_per_share: float) -> float:
    if risk_per_share <= 0 or equity <= 0 or risk_frac <= 0:
        return 0.0
    dollars = float(equity) * float(risk_frac)
    return dollars / float(risk_per_share)
