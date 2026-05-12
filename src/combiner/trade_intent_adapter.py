"""Build :class:`TradeIntent` from combiner precompute matrices; no fill/R math here."""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd

from src.combiner.candidate import Candidate

COMBINER_ADAPTER_VERSION = "combiner_adapter_v1"
from src.execution.path import simulate_trade_path
from src.execution.policy import default_intraday_policy
from src.execution.types import (
    ExecutionPolicy,
    ExitPlan,
    ExitReason,
    TM_FIXED_PX,
    TM_FIXED_R,
    TM_NONE,
    TradeIntent,
    TradeResult,
)
from src.execution.validators import is_finite_price

TargetMode = Literal["fixed_r", "fixed_price", "none"]


def target_mode_from_code(code: int | np.integer) -> TargetMode:
    c = int(code)
    if c == int(TM_FIXED_R):
        return "fixed_r"
    if c == int(TM_FIXED_PX):
        return "fixed_price"
    return "none"


def build_trade_intent_from_candidate(
    *,
    candidate: Candidate,
    ci: int,
    signal_bar: int,
    entry_bar: int,
    side: int,
    stop_price: float,
    target_preview: float,
    target_mode_code: int,
    target_r: float,
    risk_preview: float | None,
    max_hold_bars: int | None,
    qty: float,
    management_mode: str = "none",
) -> TradeIntent:
    """Map one selected matrix row to a raw :class:`TradeIntent` for :func:`simulate_trade_path`."""
    if entry_bar <= signal_bar:
        raise ValueError("entry_bar must be > signal_bar for next-bar entry semantics")
    mode = target_mode_from_code(target_mode_code)
    tp: float | None = None
    tr: float | None = None
    if mode == "fixed_price":
        if not is_finite_price(float(target_preview)):
            raise ValueError("fixed_price requires finite target_preview")
        tp = float(target_preview)
    elif mode == "fixed_r":
        tr = float(target_r)
        if not (is_finite_price(tr) and tr > 0):
            raise ValueError("fixed_r requires target_r > 0")
    risk: float | None = None
    if risk_preview is not None and is_finite_price(float(risk_preview)) and float(risk_preview) > 0:
        risk = float(risk_preview)
    mh = max_hold_bars
    if mh is not None and int(mh) <= 0:
        mh = None
    return TradeIntent(
        candidate_id=candidate.candidate_id,
        strategy=candidate.strategy,
        side=int(side),
        signal_idx=int(signal_bar),
        entry_idx=int(entry_bar),
        stop_price=float(stop_price),
        max_hold_bars=mh,
        management_mode=str(management_mode or "none"),
        target_mode=mode,
        target_price=tp,
        target_r=tr,
        risk_per_share=risk,
        qty=float(qty),
        metadata={"combiner_adapter": COMBINER_ADAPTER_VERSION},
        family=str(candidate.family or "unknown"),
        setup_type=str((candidate.metadata or {}).get("setup_type") or "unknown"),
    )


def execution_policy_from_combiner_cfg(cfg: Any) -> ExecutionPolicy:
    return default_intraday_policy(
        slippage_per_share=float(getattr(cfg, "slippage_per_share", 0.0)),
        commission_per_trade=float(getattr(cfg, "commission_per_trade", 0.0)),
        eod_exit_minute=int(getattr(cfg, "eod_exit_minute", 389)),
    )


def exit_plan_from_max_hold(max_hold_bars: int | None) -> ExitPlan:
    if max_hold_bars is None or int(max_hold_bars) <= 0:
        return ExitPlan()
    return ExitPlan(max_hold_bars_cap=int(max_hold_bars))


def simulate_selected_trade(
    bars: pd.DataFrame,
    intent: TradeIntent,
    *,
    combiner_cfg: Any,
    max_hold_override: int | None = None,
) -> TradeResult:
    """Run :func:`simulate_trade_path` with policy derived from combiner YAML knobs."""
    pol = execution_policy_from_combiner_cfg(combiner_cfg)
    mh = max_hold_override if max_hold_override is not None else intent.max_hold_bars
    plan = exit_plan_from_max_hold(mh)
    return simulate_trade_path(bars, intent, pol, plan)


def _exit_reason_str(reason: ExitReason | None) -> str:
    if reason is None:
        return ""
    return str(reason.name).lower()


def trade_result_to_combiner_row(
    *,
    trade_id: int,
    candidate: Candidate,
    intent: TradeIntent,
    result: TradeResult,
    symbol: str,
    session_date: str,
    signal_ts_utc: str,
    entry_ts_utc: str,
    exit_ts_utc: str,
    exit_bar_idx: int,
    stop_at_signal: float,
    target_preview_at_signal: float,
    target_mode_code_at_signal: int,
    target_r_at_signal: float,
    priority: float,
    daily_trade_number: int,
    policy: ExecutionPolicy,
) -> dict[str, Any]:
    """Stable trade dict aligned with legacy combiner columns where possible."""
    return {
        "trade_id": int(trade_id),
        "candidate_id": candidate.candidate_id,
        "strategy": candidate.strategy,
        "strategy_family": candidate.family,
        "symbol": symbol,
        "session_date": session_date,
        "side": int(intent.side),
        "signal_idx": int(intent.signal_idx),
        "signal_ts_utc": signal_ts_utc,
        "entry_idx": int(intent.entry_idx),
        "entry_ts_utc": entry_ts_utc,
        "exit_idx": int(exit_bar_idx),
        "exit_ts_utc": exit_ts_utc,
        "entry_price": float(result.entry_price),
        "exit_price": float(result.exit_price),
        "stop_price": float(stop_at_signal),
        "target_price": float(target_preview_at_signal),
        "risk_per_share": float(result.risk_per_share),
        "target_mode_code": int(target_mode_code_at_signal),
        "target_r": float(target_r_at_signal),
        "net_pnl": float(result.net_pnl_per_share) * float(intent.qty),
        "r_multiple": float(result.r_multiple),
        "exit_reason": _exit_reason_str(result.exit_reason),
        "bars_held": int(result.bars_held),
        "priority": float(priority),
        "daily_trade_number": int(daily_trade_number),
        "execution_semantics_version": str(policy.semantics_version),
        "combiner_adapter_version": COMBINER_ADAPTER_VERSION,
        "result_lineage": "mainline_layer2",
    }
