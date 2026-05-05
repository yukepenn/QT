"""Shared execution-time validation helpers (pure Python).

These helpers are intentionally strategy-agnostic and can be unit-tested with
synthetic inputs (no parquet required).
"""

from __future__ import annotations

import math
from typing import Literal, Tuple

TargetMode = Literal["fixed_r", "fixed_price"]


def is_finite_price(x: float) -> bool:
    try:
        return x is not None and math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def valid_target_r(target_r: float) -> bool:
    return is_finite_price(target_r) and float(target_r) > 0.0


def valid_stop_side(side: int, entry: float, stop: float) -> bool:
    if side == 1:
        return stop < entry
    if side == -1:
        return stop > entry
    return False


def valid_fixed_price_target_side(side: int, entry: float, target: float) -> bool:
    if side == 1:
        return target > entry
    if side == -1:
        return target < entry
    return False


def actual_risk_per_share(side: int, entry: float, stop: float) -> float:
    """Return positive risk-per-share if stop side is valid; else NaN."""
    if not (is_finite_price(entry) and is_finite_price(stop)):
        return float("nan")
    e = float(entry)
    s = float(stop)
    if side == 1:
        return (e - s) if s < e else float("nan")
    if side == -1:
        return (s - e) if s > e else float("nan")
    return float("nan")


def compute_fixed_r_target(side: int, entry: float, risk: float, target_r: float) -> float:
    if side == 1:
        return float(entry) + float(target_r) * float(risk)
    if side == -1:
        return float(entry) - float(target_r) * float(risk)
    return float("nan")


def estimate_round_trip_cost_per_share(slippage_per_share: float, commission_per_trade: float, quantity: float) -> float:
    """Approximate per-share round-trip cost for cost-as-R diagnostics."""
    if not (is_finite_price(slippage_per_share) and is_finite_price(commission_per_trade) and is_finite_price(quantity)):
        return float("nan")
    q = float(quantity)
    if q <= 0:
        return float("nan")
    return 2.0 * float(slippage_per_share) + float(commission_per_trade) / q


def validate_trade_setup(
    *,
    side: int,
    entry: float,
    stop: float,
    target_mode: TargetMode,
    target_preview: float,
    target_r: float | None,
    min_risk_per_share: float = 0.0,
    recompute_target_from_entry: bool = True,
) -> Tuple[bool, str, float, float]:
    """Validate execution inputs and produce (ok, reason, risk, resolved_target).

    Reasons are stable string labels; callers may map them to rejection codes.
    """
    if side not in (1, -1):
        return False, "invalid_side", float("nan"), float("nan")

    if not is_finite_price(entry):
        return False, "invalid_price_nan", float("nan"), float("nan")
    if not is_finite_price(stop):
        return False, "invalid_price_nan", float("nan"), float("nan")
    if not valid_stop_side(side, float(entry), float(stop)):
        return False, "invalid_stop_side", float("nan"), float("nan")

    risk = actual_risk_per_share(side, float(entry), float(stop))
    if not is_finite_price(risk) or float(risk) <= 0.0:
        return False, "invalid_risk", float("nan"), float("nan")

    if is_finite_price(min_risk_per_share) and float(min_risk_per_share) > 0.0:
        if float(risk) < float(min_risk_per_share):
            return False, "risk_too_small", float(risk), float("nan")

    if target_mode == "fixed_r":
        if target_r is None or not valid_target_r(float(target_r)):
            return False, "invalid_target_r", float(risk), float("nan")
        resolved = compute_fixed_r_target(side, float(entry), float(risk), float(target_r))
        if not is_finite_price(resolved):
            return False, "invalid_price_nan", float(risk), float("nan")
        return True, "ok", float(risk), float(resolved)

    if target_mode == "fixed_price":
        if not is_finite_price(target_preview):
            return False, "invalid_price_nan", float(risk), float("nan")
        tgt = float(target_preview)
        if not valid_fixed_price_target_side(side, float(entry), tgt):
            return False, "invalid_target_side", float(risk), float("nan")
        return True, "ok", float(risk), tgt

    return False, "invalid_target_mode", float(risk), float("nan")

