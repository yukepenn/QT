"""Validate bars, policies, and intents before simulation."""

from __future__ import annotations

import math
from typing import Literal, Tuple

import numpy as np
import pandas as pd

from src.execution.types import ExecutionPolicy, Side, TradeIntent

SignalTargetMode = Literal["fixed_r", "fixed_price"]


def is_finite_price(x: float) -> bool:
    try:
        return x is not None and math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def validate_bars(df: pd.DataFrame, *, required: tuple[str, ...]) -> tuple[bool, str]:
    miss = [c for c in required if c not in df.columns]
    if miss:
        return False, f"missing_columns:{miss}"
    if df.index.has_duplicates:
        return False, "duplicate_index"
    return True, "ok"


def validate_execution_policy(p: ExecutionPolicy) -> tuple[bool, str]:
    if p.semantics_version != "1.0":
        return False, "unsupported_semantics_version"
    if not is_finite_price(p.slippage_per_share) or p.slippage_per_share < 0:
        return False, "bad_slippage"
    if not is_finite_price(p.commission_per_trade) or p.commission_per_trade < 0:
        return False, "bad_commission"
    if str(p.scale_fill_policy) not in ("close", "trigger_price"):
        return False, "bad_scale_fill_policy"
    if not is_finite_price(float(p.min_risk_per_share)) or float(p.min_risk_per_share) < 0:
        return False, "bad_min_risk"
    return True, "ok"


def validate_trade_intent(
    intent: TradeIntent, policy: ExecutionPolicy, bars_len: int
) -> tuple[bool, str]:
    if intent.side not in (Side.LONG, Side.SHORT):
        return False, "invalid_side"
    if intent.side == Side.SHORT and not policy.allow_short:
        return False, "short_disabled"
    if intent.entry_idx < 0 or intent.entry_idx >= bars_len:
        return False, "bad_entry_idx"
    if not is_finite_price(intent.stop_price):
        return False, "bad_stop"
    if intent.qty <= 0:
        return False, "bad_qty"

    mode = str(intent.target_mode or "fixed_r").strip().lower()
    if mode not in ("fixed_r", "fixed_price", "none"):
        return False, "bad_target_mode"

    if intent.risk_per_share is not None:
        if not is_finite_price(intent.risk_per_share) or float(intent.risk_per_share) <= 0:
            return False, "bad_risk_override"

    if mode == "fixed_price":
        if intent.target_price is None or not is_finite_price(intent.target_price):
            return False, "bad_target_fixed_price"
    elif mode == "fixed_r":
        tr = intent.target_r
        if tr is None or not (is_finite_price(float(tr)) and float(tr) > 0):
            return False, "bad_target_r"
    return True, "ok"


def bars_to_arrays(df: pd.DataFrame) -> dict[str, np.ndarray]:
    return {
        "open": df["open"].to_numpy(dtype=np.float64, copy=False),
        "high": df["high"].to_numpy(dtype=np.float64, copy=False),
        "low": df["low"].to_numpy(dtype=np.float64, copy=False),
        "close": df["close"].to_numpy(dtype=np.float64, copy=False),
        "minute": df["minute_from_open"].to_numpy(dtype=np.int32, copy=False)
        if "minute_from_open" in df.columns
        else np.zeros(len(df), dtype=np.int32),
    }


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


def estimate_round_trip_cost_per_share(
    slippage_per_share: float, commission_per_trade: float, quantity: float
) -> float:
    """Approximate per-share round-trip cost for cost-as-R diagnostics."""
    if not (
        is_finite_price(slippage_per_share)
        and is_finite_price(commission_per_trade)
        and is_finite_price(quantity)
    ):
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
    target_mode: SignalTargetMode,
    target_preview: float,
    target_r: float | None,
    min_risk_per_share: float = 0.0,
    recompute_target_from_entry: bool = True,
) -> Tuple[bool, str, float, float]:
    """Validate execution inputs and produce (ok, reason, risk, resolved_target)."""
    _ = recompute_target_from_entry
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
