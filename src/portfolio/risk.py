"""Risk helpers."""

from __future__ import annotations


def r_to_dollars(r: float, risk_dollars: float) -> float:
    return float(r) * float(risk_dollars)
