"""Entry, risk, and target materialization (canonical accounting).

Adapters must **not** compute entry fill, initial risk, or fixed-R targets.
They pass raw signal fields on :class:`TradeIntent`; this module (called from
:func:`src.execution.path.simulate_trade_path`) produces executable levels.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from src.execution import fill as fl
from src.execution.types import ExecutionPolicy, ExitPlan, Side, TradeIntent

# ``eod_exit_minute >=`` this value is treated as "EOD exit disabled" for
# **targetless** materialization checks only (typical test / long-session runs).
_TARGETLESS_EOD_DISABLED_SENTINEL = 500


@dataclass(frozen=True)
class MaterializedTrade:
    """Executable levels after materialization."""

    ok: bool
    reject_reason: str
    entry_price: float = float("nan")
    risk_per_share: float = float("nan")
    target_price: float | None = None
    target_mode: str = "fixed_r"


def materialize_entry_price(bars: pd.DataFrame, intent: TradeIntent, policy: ExecutionPolicy) -> float:
    """Entry fill at ``intent.entry_idx`` open (with slippage)."""
    j = int(intent.entry_idx)
    o = float(bars.iloc[j]["open"])
    return fl.entry_fill_price(o, int(intent.side), float(policy.slippage_per_share))


def materialize_initial_risk(entry_price: float, stop_price: float, side: int) -> float:
    """Initial risk per share (positive distance entry → stop)."""
    if side == Side.LONG:
        return float(entry_price) - float(stop_price)
    return float(stop_price) - float(entry_price)


def materialize_target_price(
    *,
    entry_price: float,
    risk_per_share: float,
    intent: TradeIntent,
) -> float | None:
    """Absolute target price, or ``None`` when ``target_mode == \"none\"``."""
    mode = str(intent.target_mode or "fixed_r").strip().lower()
    if mode == "none":
        return None
    if mode == "fixed_price":
        tp = intent.target_price
        if tp is None or not math.isfinite(float(tp)):
            return None
        return float(tp)
    if mode != "fixed_r":
        return None
    tr = intent.target_r
    if tr is None or not (math.isfinite(float(tr)) and float(tr) > 0):
        return None
    trf = float(tr)
    if int(intent.side) == Side.LONG:
        return float(entry_price) + trf * float(risk_per_share)
    return float(entry_price) - trf * float(risk_per_share)


def _targetless_has_exit_path(intent: TradeIntent, plan: ExitPlan, policy: ExecutionPolicy) -> bool:
    """Runner-style: require explicit time/management exits (not END_DATA-only).

    Scale-out legs without a trailing plan are rejected: partial de-risk alone
    is not considered a complete targetless exit path.
    """
    if plan.trailing is not None:
        return True
    if len(plan.scale_outs) > 0:
        return False
    if intent.max_hold_bars is not None or plan.max_hold_bars_cap is not None:
        return True
    if plan.no_followthrough_bars is not None and plan.no_followthrough_min_r is not None:
        return True
    eod = int(policy.eod_exit_minute)
    if eod < _TARGETLESS_EOD_DISABLED_SENTINEL:
        return True
    return False


def materialize_trade_levels(
    bars: pd.DataFrame,
    intent: TradeIntent,
    policy: ExecutionPolicy,
    exit_plan: ExitPlan | None = None,
) -> MaterializedTrade:
    """Compute entry, risk, and target from bars + raw intent."""
    exit_plan = exit_plan or ExitPlan()
    mode = str(intent.target_mode or "fixed_r").strip().lower()

    try:
        entry = materialize_entry_price(bars, intent, policy)
    except (IndexError, KeyError, TypeError, ValueError):
        return MaterializedTrade(False, "bad_bars_for_entry")

    stop = float(intent.stop_price)
    side = int(intent.side)

    if intent.risk_per_share is not None and math.isfinite(float(intent.risk_per_share)):
        risk = float(intent.risk_per_share)
    else:
        risk = materialize_initial_risk(entry, stop, side)

    if not math.isfinite(risk) or risk <= 0:
        return MaterializedTrade(False, "bad_risk", entry_price=entry)

    if side == Side.LONG and not (stop < entry):
        return MaterializedTrade(False, "invalid_stop_side_long", entry_price=entry)
    if side == Side.SHORT and not (stop > entry):
        return MaterializedTrade(False, "invalid_stop_side_short", entry_price=entry)

    tgt = materialize_target_price(entry_price=entry, risk_per_share=risk, intent=intent)

    if mode == "none":
        if not _targetless_has_exit_path(intent, exit_plan, policy):
            return MaterializedTrade(False, "targetless_no_exit_path", entry_price=entry, risk_per_share=risk)
        return MaterializedTrade(True, "ok", entry, risk, None, mode)

    if tgt is None or not math.isfinite(float(tgt)):
        return MaterializedTrade(False, "bad_target", entry_price=entry, risk_per_share=risk)

    if mode == "fixed_r":
        if side == Side.LONG and not (tgt > entry):
            return MaterializedTrade(False, "invalid_target_side_long", entry_price=entry, risk_per_share=risk)
        if side == Side.SHORT and not (tgt < entry):
            return MaterializedTrade(False, "invalid_target_side_short", entry_price=entry, risk_per_share=risk)
    else:
        if side == Side.LONG and not (tgt > entry):
            return MaterializedTrade(False, "invalid_fixed_target_long", entry_price=entry, risk_per_share=risk)
        if side == Side.SHORT and not (tgt < entry):
            return MaterializedTrade(False, "invalid_fixed_target_short", entry_price=entry, risk_per_share=risk)

    return MaterializedTrade(True, "ok", entry, risk, float(tgt), mode)
