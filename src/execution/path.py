"""Reference trade simulator (single position, multi-leg capable).

This module is the **canonical** bar-path engine. It:

- Validates policy, bars, and intent
- Applies **one** entry fill at ``entry_idx`` open
- Walks forward bar by bar without lookahead
- Uses the exit order documented in ``docs/EXECUTION_SEMANTICS.md``

Trailing semantics (conservative default): the stop price checked on bar ``t``
is the level computed from price action **through bar ``t-1``** only. After all
non-exit outcomes for bar ``t``, the trail level ratchets using bar ``t``'s
range so it can trigger **starting next bar**, not as a same-bar lookahead.
"""

from __future__ import annotations

import math
from typing import Callable

import numpy as np
import pandas as pd

from src.execution import exits as ex
from src.execution import fill as fl
from src.execution import pnl as pnl_mod
from src.execution.types import (
    ExecutionPolicy,
    ExitPlan,
    ExitReason,
    FillLeg,
    Side,
    TradeIntent,
    TradeResult,
)
from src.execution.validators import (
    bars_to_arrays,
    validate_bars,
    validate_execution_policy,
    validate_trade_intent,
)


def _effective_max_hold(intent: TradeIntent, plan: ExitPlan) -> int | None:
    a = intent.max_hold_bars
    b = plan.max_hold_bars_cap
    if a is not None and b is not None:
        return min(int(a), int(b))
    if a is not None:
        return int(a)
    if b is not None:
        return int(b)
    return None


def _update_mfe_mae(
    *,
    side: int,
    entry_px: float,
    risk: float,
    hi: float,
    lo: float,
    best_hi: float,
    best_lo: float,
    mfe_r: float,
    mae_r: float,
) -> tuple[float, float, float, float]:
    """Return updated ``(best_hi, best_lo, mfe_r, mae_r)``."""
    if side == Side.LONG:
        best_hi = max(best_hi, hi)
        best_lo = min(best_lo, lo)
        mfe_r = max(mfe_r, (best_hi - entry_px) / risk)
        mae_r = max(mae_r, (entry_px - best_lo) / risk)
    else:
        best_lo = min(best_lo, lo)
        best_hi = max(best_hi, hi)
        mfe_r = max(mfe_r, (entry_px - best_lo) / risk)
        mae_r = max(mae_r, (best_hi - entry_px) / risk)
    return best_hi, best_lo, mfe_r, mae_r


def _maybe_exit_stop_target(
    *,
    side: int,
    hi: float,
    lo: float,
    stop: float,
    target: float,
    policy: ExecutionPolicy,
    push_exit: Callable[..., None],
    qty_rem: float,
) -> ExitReason | None:
    st_hit, tg_hit = ex.intrabar_stop_target_hit(
        side=side,
        high=hi,
        low=lo,
        stop=stop,
        target=target,
        ambiguity=policy.same_bar_policy,
    )
    first = ex.resolve_stop_target_order(st_hit, tg_hit, policy.same_bar_policy)
    if first is None:
        return None
    raw = stop if first == ExitReason.STOP else target
    push_exit(qty_rem, raw, first)
    return first


def _maybe_exit_trailing_prior(
    *,
    side: int,
    hi: float,
    lo: float,
    trail_level: float,
    policy: ExecutionPolicy,
    exit_plan: ExitPlan,
    push_exit: Callable[..., None],
    qty_rem: float,
) -> ExitReason | None:
    if not (policy.allow_trailing and exit_plan.trailing is not None):
        return None
    if qty_rem <= 1e-12:
        return None
    if side == Side.LONG and ex.trailing_hit_long(lo, trail_level):
        push_exit(qty_rem, trail_level, ExitReason.TRAILING)
        return ExitReason.TRAILING
    if side == Side.SHORT and ex.trailing_hit_short(hi, trail_level):
        push_exit(qty_rem, trail_level, ExitReason.TRAILING)
        return ExitReason.TRAILING
    return None


def _maybe_scale_out(
    *,
    side: int,
    entry_px: float,
    hi: float,
    low: float,
    close: float,
    risk: float,
    qty: float,
    qty_rem: float,
    slip: float,
    policy: ExecutionPolicy,
    exit_plan: ExitPlan,
    scale_idx: int,
    push_exit: Callable[..., None],
) -> tuple[ExitReason | None, int]:
    """Touch trigger, fill at **close** for the partial (documented)."""
    if not (policy.allow_partial_exits and exit_plan.scale_outs and qty_rem > 1e-12):
        return None, scale_idx
    if scale_idx >= len(exit_plan.scale_outs):
        return None, scale_idx
    rule = exit_plan.scale_outs[scale_idx]
    if not ex.scale_out_triggered_touch(
        side=side,
        entry=entry_px,
        high=hi,
        low=low,
        risk=risk,
        trigger_r=float(rule.trigger_r),
    ):
        return None, scale_idx
    qty_part = qty * float(rule.exit_fraction)
    push_exit(qty_part, close, ExitReason.SCALE_OUT)
    return ExitReason.SCALE_OUT, scale_idx + 1


def _update_trailing_for_next_bar(
    *,
    side: int,
    hi: float,
    lo: float,
    risk: float,
    trail_rule_distance_r: float,
    best_hi: float,
    best_lo: float,
    trail_long: float,
    trail_short: float,
) -> tuple[float, float, float, float]:
    """Ratchet trailing **stop price** for the next bar (no same-bar trigger)."""
    dist = float(trail_rule_distance_r) * risk
    if side == Side.LONG:
        best_hi = max(best_hi, hi)
        cand = best_hi - dist
        if not math.isfinite(trail_long):
            trail_long = cand
        else:
            trail_long = max(trail_long, cand)
    else:
        best_lo = min(best_lo, lo)
        cand = best_lo + dist
        if not math.isfinite(trail_short):
            trail_short = cand
        else:
            trail_short = min(trail_short, cand)
    return best_hi, best_lo, trail_long, trail_short


def _maybe_no_followthrough(
    *,
    side: int,
    entry_px: float,
    close: float,
    risk: float,
    slip: float,
    entry_bar_idx: int,
    current_bar_idx: int,
    exit_plan: ExitPlan,
    push_exit: Callable[..., None],
    qty_rem: float,
) -> ExitReason | None:
    if exit_plan.no_followthrough_bars is None or exit_plan.no_followthrough_min_r is None:
        return None
    if qty_rem <= 1e-12:
        return None
    held = current_bar_idx - entry_bar_idx + 1
    if held < int(exit_plan.no_followthrough_bars):
        return None
    ex_close = fl.exit_fill_price(close, side, ExitReason.NO_FOLLOWTHROUGH, slip)
    unreal = pnl_mod.leg_r(side, entry_px, ex_close, risk)
    if unreal < float(exit_plan.no_followthrough_min_r):
        push_exit(qty_rem, close, ExitReason.NO_FOLLOWTHROUGH)
        return ExitReason.NO_FOLLOWTHROUGH
    return None


def _maybe_max_hold(
    *,
    side: int,
    close: float,
    slip: float,
    entry_bar_idx: int,
    current_bar_idx: int,
    max_hold: int | None,
    push_exit: Callable[..., None],
    qty_rem: float,
) -> ExitReason | None:
    if max_hold is None or qty_rem <= 1e-12:
        return None
    if ex.max_hold_exceeded(
        entry_bar_idx=entry_bar_idx,
        current_bar_idx=current_bar_idx,
        max_hold_bars=int(max_hold),
    ):
        push_exit(qty_rem, close, ExitReason.MAX_HOLD)
        return ExitReason.MAX_HOLD
    return None


def _maybe_eod(
    *,
    side: int,
    close: float,
    slip: float,
    minute: int,
    policy: ExecutionPolicy,
    push_exit: Callable[..., None],
    qty_rem: float,
) -> ExitReason | None:
    if qty_rem <= 1e-12:
        return None
    if ex.eod_triggered(minute, policy.eod_exit_minute):
        push_exit(qty_rem, close, ExitReason.EOD)
        return ExitReason.EOD
    return None


def simulate_trade_path(
    bars: pd.DataFrame,
    intent: TradeIntent,
    policy: ExecutionPolicy,
    exit_plan: ExitPlan | None = None,
) -> TradeResult:
    """Simulate one trade from ``entry_idx`` forward; see module docstring."""
    exit_plan = exit_plan or ExitPlan()

    ok, msg = validate_execution_policy(policy)
    if not ok:
        return TradeResult(False, msg, exit_reason=ExitReason.REJECTED)

    cols = ("open", "high", "low", "close")
    okb, msgb = validate_bars(bars, required=cols)
    if not okb:
        return TradeResult(False, msgb, exit_reason=ExitReason.REJECTED)

    ar = bars_to_arrays(bars)
    o = ar["open"]
    h = ar["high"]
    l = ar["low"]
    c = ar["close"]
    minute = ar.get("minute", np.zeros(len(o), dtype=np.int32))
    n = len(o)

    oki, msgi = validate_trade_intent(intent, policy, n)
    if not oki:
        return TradeResult(False, msgi, exit_reason=ExitReason.REJECTED)

    side = int(intent.side)
    slip = float(policy.slippage_per_share)
    j = int(intent.entry_idx)
    entry_px = fl.entry_fill_price(float(o[j]), side, slip)
    stop = float(intent.stop_price)
    target = float(intent.target_price)
    risk = float(intent.risk_per_share)
    qty = float(intent.qty)
    qty_rem = qty
    legs: list[FillLeg] = []

    def push_exit(qty_close: float, raw_px: float, reason: ExitReason) -> None:
        nonlocal qty_rem
        if qty_close <= 0 or qty_rem <= 0:
            return
        q_take = min(qty_close, qty_rem)
        q_frac = q_take / qty
        ex_px = fl.exit_fill_price(float(raw_px), side, reason, slip)
        rmul = pnl_mod.leg_r(side, entry_px, ex_px, risk)
        legs.append(
            FillLeg(
                qty_frac=q_frac,
                entry_price=entry_px,
                exit_price=ex_px,
                r_multiple=float(rmul),
                reason=reason,
            )
        )
        qty_rem -= q_take

    mfe_r = 0.0
    mae_r = 0.0
    best_hi = float("-inf")
    best_lo = float("inf")
    trail_long = float("-inf")
    trail_short = float("inf")
    scale_idx = 0
    exit_reason: ExitReason | None = None
    final_exit_px = float("nan")
    last_idx = j
    max_hold_eff = _effective_max_hold(intent, exit_plan)

    for idx in range(j, n):
        last_idx = idx
        hi = float(h[idx])
        lo = float(l[idx])
        cl = float(c[idx])
        mi = int(minute[idx])

        best_hi, best_lo, mfe_r, mae_r = _update_mfe_mae(
            side=side,
            entry_px=entry_px,
            risk=risk,
            hi=hi,
            lo=lo,
            best_hi=best_hi,
            best_lo=best_lo,
            mfe_r=mfe_r,
            mae_r=mae_r,
        )

        er = _maybe_exit_stop_target(
            side=side,
            hi=hi,
            lo=lo,
            stop=stop,
            target=target,
            policy=policy,
            push_exit=push_exit,
            qty_rem=qty_rem,
        )
        if er is not None:
            exit_reason = er
            final_exit_px = legs[-1].exit_price
            break

        er = _maybe_exit_trailing_prior(
            side=side,
            hi=hi,
            lo=lo,
            trail_level=trail_long if side == Side.LONG else trail_short,
            policy=policy,
            exit_plan=exit_plan,
            push_exit=push_exit,
            qty_rem=qty_rem,
        )
        if er is not None:
            exit_reason = er
            final_exit_px = legs[-1].exit_price
            break

        so_reason, scale_idx = _maybe_scale_out(
            side=side,
            entry_px=entry_px,
            hi=hi,
            low=lo,
            close=cl,
            risk=risk,
            qty=qty,
            qty_rem=qty_rem,
            slip=slip,
            policy=policy,
            exit_plan=exit_plan,
            scale_idx=scale_idx,
            push_exit=push_exit,
        )
        if so_reason is not None and qty_rem <= 1e-12:
            exit_reason = so_reason
            final_exit_px = legs[-1].exit_price
            break

        er = _maybe_no_followthrough(
            side=side,
            entry_px=entry_px,
            close=cl,
            risk=risk,
            slip=slip,
            entry_bar_idx=j,
            current_bar_idx=idx,
            exit_plan=exit_plan,
            push_exit=push_exit,
            qty_rem=qty_rem,
        )
        if er is not None:
            exit_reason = er
            final_exit_px = legs[-1].exit_price
            break

        er = _maybe_max_hold(
            side=side,
            close=cl,
            slip=slip,
            entry_bar_idx=j,
            current_bar_idx=idx,
            max_hold=max_hold_eff,
            push_exit=push_exit,
            qty_rem=qty_rem,
        )
        if er is not None:
            exit_reason = er
            final_exit_px = legs[-1].exit_price
            break

        er = _maybe_eod(
            side=side,
            close=cl,
            slip=slip,
            minute=mi,
            policy=policy,
            push_exit=push_exit,
            qty_rem=qty_rem,
        )
        if er is not None:
            exit_reason = er
            final_exit_px = legs[-1].exit_price
            break

        if exit_plan.trailing is not None and policy.allow_trailing:
            best_hi, best_lo, trail_long, trail_short = _update_trailing_for_next_bar(
                side=side,
                hi=hi,
                lo=lo,
                risk=risk,
                trail_rule_distance_r=float(exit_plan.trailing.distance_r),
                best_hi=best_hi,
                best_lo=best_lo,
                trail_long=trail_long,
                trail_short=trail_short,
            )

    if exit_reason is None and qty_rem > 1e-12:
        push_exit(qty_rem, float(c[n - 1]), ExitReason.END_DATA)
        exit_reason = ExitReason.END_DATA
        final_exit_px = legs[-1].exit_price

    if not legs:
        return TradeResult(False, "no_fill", mfe_R=mfe_r, mae_R=mae_r, exit_reason=ExitReason.REJECTED)

    gross = 0.0
    for leg in legs:
        gross += leg.qty_frac * pnl_mod.gross_pnl_per_share(
            side=side, entry=leg.entry_price, exit_px=leg.exit_price
        )
    net = pnl_mod.net_pnl_per_share_from_gross(gross, float(policy.commission_per_trade), qty)
    r_weighted = pnl_mod.weighted_r(legs)
    bars_held = last_idx - j + 1

    return TradeResult(
        ok=True,
        reject_reason="ok",
        legs=tuple(legs),
        gross_pnl_per_share=gross,
        net_pnl_per_share=net,
        r_multiple=r_weighted,
        mfe_R=mfe_r,
        mae_R=mae_r,
        bars_held=bars_held,
        exit_reason=exit_reason,
        entry_price=entry_px,
        exit_price=final_exit_px,
    )
