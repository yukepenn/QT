from __future__ import annotations

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


def simulate_trade_path(
    bars: pd.DataFrame,
    intent: TradeIntent,
    policy: ExecutionPolicy,
    exit_plan: ExitPlan | None = None,
) -> TradeResult:
    """Reference trade simulator: single position with optional scale / trailing / NFT."""
    exit_plan = exit_plan or ExitPlan()

    ok, msg = validate_execution_policy(policy)
    if not ok:
        return TradeResult(False, msg)

    cols = ("open", "high", "low", "close")
    okb, msgb = validate_bars(bars, required=cols)
    if not okb:
        return TradeResult(False, msgb)

    ar = bars_to_arrays(bars)
    o, h, l, c = ar["open"], ar["high"], ar["low"], ar["close"]
    minute = ar.get("minute", np.zeros(len(o), dtype=np.int32))
    n = len(o)

    oki, msgi = validate_trade_intent(intent, policy, n)
    if not oki:
        return TradeResult(False, msgi)

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
        ex_px = fl.exit_fill_price(raw_px, side, reason, slip)
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
    best = entry_px
    worst = entry_px
    trail_on = exit_plan.trailing is not None and policy.allow_trailing
    trail_stop = float("-inf") if side == Side.LONG else float("inf")
    scale_idx = 0
    exit_reason: ExitReason | None = None
    final_exit_px = float("nan")
    last_idx = j

    def refresh_mfe_mae(idx: int) -> None:
        nonlocal mfe_r, mae_r, best, worst, trail_stop
        hi = float(h[idx])
        lo = float(l[idx])
        if side == Side.LONG:
            best = max(best, hi)
            worst = min(worst, lo)
            mfe_r = max(mfe_r, (best - entry_px) / risk)
            mae_r = max(mae_r, (entry_px - worst) / risk)
            if trail_on and exit_plan.trailing is not None:
                dist = exit_plan.trailing.distance_r * risk
                trail_stop = max(trail_stop, best - dist)
        else:
            best = min(best, lo)
            worst = max(worst, hi)
            mfe_r = max(mfe_r, (entry_px - best) / risk)
            mae_r = max(mae_r, (worst - entry_px) / risk)
            if trail_on and exit_plan.trailing is not None:
                dist = exit_plan.trailing.distance_r * risk
                trail_stop = min(trail_stop, best + dist)

    for idx in range(j, n):
        last_idx = idx
        hi, lo, cl = float(h[idx]), float(l[idx]), float(c[idx])
        refresh_mfe_mae(idx)

        # 1) stop / target
        st_hit, tg_hit = ex.intrabar_stop_target_hit(
            side=side,
            high=hi,
            low=lo,
            stop=stop,
            target=target,
            ambiguity=policy.same_bar_policy,
        )
        first = ex.resolve_stop_target_order(st_hit, tg_hit, policy.same_bar_policy)
        if first is not None:
            raw = stop if first == ExitReason.STOP else target
            push_exit(qty_rem, raw, first)
            exit_reason = first
            final_exit_px = legs[-1].exit_price
            break

        # 2) scale-outs (evaluate against close; one trigger per bar max)
        if policy.allow_partial_exits and exit_plan.scale_outs and qty_rem > 1e-12:
            ex_close = fl.exit_fill_price(cl, side, ExitReason.SCALE_OUT, slip)
            unreal_r = pnl_mod.leg_r(side, entry_px, ex_close, risk)
            if scale_idx < len(exit_plan.scale_outs):
                rule = exit_plan.scale_outs[scale_idx]
                if unreal_r >= rule.trigger_r:
                    qty_part = qty * float(rule.exit_fraction)
                    push_exit(qty_part, cl, ExitReason.SCALE_OUT)
                    scale_idx += 1
                    if qty_rem <= 1e-12:
                        exit_reason = ExitReason.SCALE_OUT
                        final_exit_px = legs[-1].exit_price
                        break

        # 3) trailing
        if trail_on and exit_plan.trailing is not None and qty_rem > 1e-12:
            if side == Side.LONG and lo <= trail_stop:
                push_exit(qty_rem, trail_stop, ExitReason.TRAILING)
                exit_reason = ExitReason.TRAILING
                final_exit_px = legs[-1].exit_price
                break
            if side == Side.SHORT and hi >= trail_stop:
                push_exit(qty_rem, trail_stop, ExitReason.TRAILING)
                exit_reason = ExitReason.TRAILING
                final_exit_px = legs[-1].exit_price
                break

        # 4) no-followthrough
        if (
            exit_plan.no_followthrough_bars is not None
            and exit_plan.no_followthrough_min_r is not None
            and qty_rem > 1e-12
        ):
            bars_held = idx - j + 1
            if bars_held >= int(exit_plan.no_followthrough_bars):
                ex_close = fl.exit_fill_price(cl, side, ExitReason.NO_FOLLOWTHROUGH, slip)
                unreal = pnl_mod.leg_r(side, entry_px, ex_close, risk)
                if unreal < float(exit_plan.no_followthrough_min_r):
                    push_exit(qty_rem, cl, ExitReason.NO_FOLLOWTHROUGH)
                    exit_reason = ExitReason.NO_FOLLOWTHROUGH
                    final_exit_px = legs[-1].exit_price
                    break

        # 5) max hold
        if intent.max_hold_bars is not None and qty_rem > 1e-12:
            if idx - j + 1 >= int(intent.max_hold_bars):
                push_exit(qty_rem, cl, ExitReason.MAX_HOLD)
                exit_reason = ExitReason.MAX_HOLD
                final_exit_px = legs[-1].exit_price
                break

        # 6) EOD
        if int(minute[idx]) >= int(policy.eod_exit_minute) and qty_rem > 1e-12:
            push_exit(qty_rem, cl, ExitReason.EOD)
            exit_reason = ExitReason.EOD
            final_exit_px = legs[-1].exit_price
            break

    if exit_reason is None and qty_rem > 1e-12:
        push_exit(qty_rem, float(c[n - 1]), ExitReason.END_DATA)
        exit_reason = ExitReason.END_DATA
        final_exit_px = legs[-1].exit_price

    if not legs:
        return TradeResult(False, "no_fill", mfe_R=mfe_r, mae_R=mae_r)

    gross = 0.0
    for leg in legs:
        if side == Side.LONG:
            gross += leg.qty_frac * (leg.exit_price - leg.entry_price)
        else:
            gross += leg.qty_frac * (leg.entry_price - leg.exit_price)
    net = gross - float(policy.commission_per_trade) / qty if qty > 0 else float("nan")
    r_weighted = sum(leg.qty_frac * leg.r_multiple for leg in legs)
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
