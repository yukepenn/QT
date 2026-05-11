"""Layer 2 combiner: Numba simulation + Python wrappers for logs/metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import math

import numpy as np
import pandas as pd
from numba import njit

from src.backtest.legacy.execution_legacy import validate_trade_setup
from src.combiner.candidate import Candidate

# Rejection reason codes (signal evaluation)
REJ_NONE = 0
REJ_WRONG_TIME_WINDOW = 1
REJ_EXISTING_POSITION = 2
REJ_DAILY_LOSS_LIMIT = 3
REJ_MAX_TRADES_REACHED = 4
REJ_COOLDOWN_AFTER_LOSS = 5
REJ_NO_NEW_AFTER = 6
REJ_RISK_TOO_SMALL = 7
REJ_LOWER_PRIORITY_CONFLICT = 8
REJ_DISABLED_CANDIDATE = 9
REJ_LAST_BAR_NO_ENTRY = 10
REJ_SESSION_BOUNDARY_NO_ENTRY = 11
REJ_OPPOSITE_DIRECTION_CONFLICT = 12
REJ_INVALID_STOP_SIDE = 13
REJ_INVALID_TARGET_SIDE = 14
REJ_INVALID_TARGET_R = 15
REJ_INVALID_PRICE_NAN = 16

# Exit reason codes
EX_STOP = 1
EX_TARGET = 2
EX_MAX_HOLD = 3
EX_EOD = 4
EX_END_SESSION = 5
EX_END_DATA = 6

EXIT_NAMES = {
    EX_STOP: "stop",
    EX_TARGET: "target",
    EX_MAX_HOLD: "max_hold",
    EX_EOD: "eod",
    EX_END_SESSION: "end_of_session",
    EX_END_DATA: "end_of_data",
}

REJ_NAMES: dict[int, str] = {
    REJ_WRONG_TIME_WINDOW: "wrong_time_window",
    REJ_EXISTING_POSITION: "existing_position",
    REJ_DAILY_LOSS_LIMIT: "daily_loss_limit",
    REJ_MAX_TRADES_REACHED: "max_trades_reached",
    REJ_COOLDOWN_AFTER_LOSS: "cooldown_after_loss",
    REJ_NO_NEW_AFTER: "no_new_after",
    REJ_RISK_TOO_SMALL: "risk_too_small",
    REJ_LOWER_PRIORITY_CONFLICT: "lower_priority_conflict",
    REJ_DISABLED_CANDIDATE: "disabled_candidate",
    REJ_LAST_BAR_NO_ENTRY: "last_bar_no_entry",
    REJ_SESSION_BOUNDARY_NO_ENTRY: "session_boundary_no_entry",
    REJ_OPPOSITE_DIRECTION_CONFLICT: "opposite_direction_conflict",
    REJ_INVALID_STOP_SIDE: "invalid_stop_side",
    REJ_INVALID_TARGET_SIDE: "invalid_target_side",
    REJ_INVALID_TARGET_R: "invalid_target_r",
    REJ_INVALID_PRICE_NAN: "invalid_price_nan",
}

PRIORITY_METADATA_ONLY = 1
PRIORITY_SCORE_ADJUSTED = 2


def _py_exit_price(side: int, raw_ex: float, slip: float) -> float:
    if side == 1:
        return raw_ex - slip
    return raw_ex + slip


@dataclass
class CombinerConfig:
    max_open_positions: int = 1
    max_trades_per_day: int = 2
    daily_max_loss_r: float = -2.0
    no_new_after_minute: int = 360
    eod_exit_minute: int = 389
    commission_per_trade: float = 0.0
    slippage_per_share: float = 0.01
    cooldown_after_loss_minutes: int = 0
    allow_same_bar_multiple_candidates: bool = False
    priority_policy: str = "metadata_priority"
    opposite_direction_skip_all: bool = False
    min_risk_per_share: float = 0.0


@njit(cache=True)
def _clip_score_adj(x: float) -> float:
    v = x * 5.0
    if v < -5.0:
        return -5.0
    if v > 5.0:
        return 5.0
    return v


@njit(cache=True)
def _numba_exit_px(side: int, raw_ex: float, slip: float) -> float:
    if side == 1:
        return raw_ex - slip
    return raw_ex + slip


@njit(cache=True)
def _simulate_combiner_numba(
    o: np.ndarray,
    h: np.ndarray,
    l: np.ndarray,
    c: np.ndarray,
    minute: np.ndarray,
    sess: np.ndarray,
    side_m: np.ndarray,
    valid_m: np.ndarray,
    stop_m: np.ndarray,
    tp_m: np.ndarray,
    tmc_m: np.ndarray,
    tr_m: np.ndarray,
    priority: np.ndarray,
    score: np.ndarray,
    rank: np.ndarray,
    active_start: np.ndarray,
    active_end: np.ndarray,
    enabled: np.ndarray,
    max_hold: np.ndarray,
    recomp_flag: np.ndarray,
    qty_c: np.ndarray,
    min_risk_c: np.ndarray,
    slip: float,
    comm: float,
    eod_m: int,
    no_new_m: int,
    max_daily_trades: int,
    daily_loss_lim: float,
    cooldown_min: int,
    priority_policy: int,
    opposite_skip: int,
    n: int,
    nc: int,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    max_tr = n
    t_sig = np.empty(max_tr, dtype=np.int32)
    t_ent = np.empty(max_tr, dtype=np.int32)
    t_ex = np.empty(max_tr, dtype=np.int32)
    t_ci = np.empty(max_tr, dtype=np.int32)
    t_side = np.empty(max_tr, dtype=np.int8)
    t_ep = np.empty(max_tr, dtype=np.float64)
    t_xp = np.empty(max_tr, dtype=np.float64)
    t_sp = np.empty(max_tr, dtype=np.float64)
    t_tg = np.empty(max_tr, dtype=np.float64)
    t_risk = np.empty(max_tr, dtype=np.float64)
    t_net = np.empty(max_tr, dtype=np.float64)
    t_r = np.empty(max_tr, dtype=np.float64)
    t_bh = np.empty(max_tr, dtype=np.int32)
    t_exr = np.empty(max_tr, dtype=np.int32)
    t_dtn = np.empty(max_tr, dtype=np.int32)
    tc = 0

    rej = np.zeros(32, dtype=np.int64)

    in_pos = 0
    entry_idx = -1
    sig_idx = -1
    sel_ci = -1
    side = 0
    stop_px = 0.0
    tgt_px = 0.0
    act_risk = 0.0
    ent_price = 0.0
    qty = 1.0
    max_hold_m = -1
    daily_trades = 0
    daily_r = 0.0
    prev_sess = -999999
    cooldown_until = -1
    cur_dtn = 0

    i = 0
    while i < n:
        sid = int(sess[i])
        if prev_sess == -999999 or sid != prev_sess:
            daily_trades = 0
            daily_r = 0.0
            cooldown_until = -1
            prev_sess = sid

        m = int(minute[i])

        if in_pos == 0:
            if i >= n - 1:
                i += 1
                continue

            if i < cooldown_until:
                i += 1
                continue

            if daily_r <= daily_loss_lim:
                i += 1
                continue

            if daily_trades >= max_daily_trades:
                i += 1
                continue

            best_ci = -1
            best_eff = -1e30
            best_sc = -1e30
            best_rank = 2147483647
            n_elig = 0

            raw_idx = np.empty(nc, dtype=np.int32)
            ne = 0
            for ci in range(nc):
                if int(enabled[ci]) == 0:
                    continue
                if not valid_m[ci, i]:
                    continue
                if side_m[ci, i] == 0:
                    continue
                raw_idx[ne] = ci
                ne += 1

            if ne == 0:
                i += 1
                continue

            sides_diff = 0
            if opposite_skip != 0:
                s0 = int(side_m[raw_idx[0], i])
                for t in range(1, ne):
                    if int(side_m[raw_idx[t], i]) != s0:
                        sides_diff = 1
                        break

            if opposite_skip != 0 and sides_diff != 0:
                rej[REJ_OPPOSITE_DIRECTION_CONFLICT] += ne
                i += 1
                continue

            elig_idx = np.empty(nc, dtype=np.int32)
            elig_n = 0
            for t in range(ne):
                ci = int(raw_idx[t])
                rr = REJ_NONE
                if not (active_start[ci] <= m <= active_end[ci]):
                    rr = REJ_WRONG_TIME_WINDOW
                elif m >= no_new_m:
                    rr = REJ_NO_NEW_AFTER
                elif i + 1 >= n or int(sess[i + 1]) != int(sess[i]):
                    rr = REJ_SESSION_BOUNDARY_NO_ENTRY

                if rr != REJ_NONE:
                    rej[rr] += 1
                    continue
                elig_idx[elig_n] = ci
                elig_n += 1

                if priority_policy == PRIORITY_SCORE_ADJUSTED:
                    eff = float(priority[ci]) + _clip_score_adj(float(score[ci]))
                else:
                    eff = float(priority[ci])
                sc = float(score[ci])
                rk = int(rank[ci])

                n_elig += 1
                pick = 0
                if best_ci < 0:
                    pick = 1
                elif eff > best_eff:
                    pick = 1
                elif eff == best_eff:
                    if sc > best_sc:
                        pick = 1
                    elif sc == best_sc:
                        if rk < best_rank:
                            pick = 1
                        elif rk == best_rank:
                            if ci < best_ci:
                                pick = 1

                if pick != 0:
                    best_ci = ci
                    best_eff = eff
                    best_sc = sc
                    best_rank = rk

            if n_elig == 0 or best_ci < 0:
                i += 1
                continue

            ci = best_ci
            sd = int(side_m[ci, i])
            ent_raw = float(o[i + 1])
            stop_px = float(stop_m[ci, i])
            if sd == 1:
                ent_price = ent_raw + slip
            else:
                ent_price = ent_raw - slip
            tm = int(tmc_m[ci, i])
            trv = float(tr_m[ci, i])
            tprev = float(tp_m[ci, i])
            tgt_px = 0.0
            bad_code = 0
            act_risk = 0.0
            if not (np.isfinite(ent_price) and np.isfinite(stop_px)):
                bad_code = REJ_INVALID_PRICE_NAN
            else:
                if sd == 1:
                    if not (stop_px < ent_price):
                        bad_code = REJ_INVALID_STOP_SIDE
                    else:
                        act_risk = ent_price - stop_px
                else:
                    if not (stop_px > ent_price):
                        bad_code = REJ_INVALID_STOP_SIDE
                    else:
                        act_risk = stop_px - ent_price
            if bad_code == 0 and (not np.isfinite(act_risk) or act_risk <= 0.0):
                bad_code = REJ_INVALID_PRICE_NAN
            if bad_code == 0 and (tm != 1 and tm != 2):
                bad_code = REJ_INVALID_PRICE_NAN
            if bad_code == 0:
                if tm == 1:
                    if not (np.isfinite(trv) and trv > 0.0):
                        bad_code = REJ_INVALID_TARGET_R
                    else:
                        if int(recomp_flag[ci]) != 0:
                            tgt_px = (
                                ent_price + trv * act_risk
                                if sd == 1
                                else ent_price - trv * act_risk
                            )
                        else:
                            tgt_px = tprev
                else:
                    tgt_px = tprev
            if bad_code == 0 and (not np.isfinite(tgt_px)):
                bad_code = REJ_INVALID_PRICE_NAN
            if bad_code == 0 and tm == 2:
                if sd == 1:
                    if not (tgt_px > ent_price):
                        bad_code = REJ_INVALID_TARGET_SIDE
                else:
                    if not (tgt_px < ent_price):
                        bad_code = REJ_INVALID_TARGET_SIDE

            mr = float(min_risk_c[ci])
            risk_small = (bad_code == 0) and mr > 0.0 and act_risk < mr

            if bad_code != 0 or risk_small:
                if risk_small:
                    rej[REJ_RISK_TOO_SMALL] += 1
                else:
                    rej[bad_code] += 1
                i += 1
                continue

            # Count rejections for non-selected eligible candidates.
            for t in range(elig_n):
                cj = int(elig_idx[t])
                if cj == ci:
                    continue
                if int(side_m[cj, i]) != sd:
                    rej[REJ_OPPOSITE_DIRECTION_CONFLICT] += 1
                else:
                    rej[REJ_LOWER_PRIORITY_CONFLICT] += 1

            in_pos = 1
            entry_idx = i + 1
            sig_idx = i
            sel_ci = ci
            side = sd
            qty = float(qty_c[ci])
            mh = int(max_hold[ci])
            max_hold_m = mh if mh > 0 else -1
            daily_trades += 1
            cur_dtn = daily_trades
            i = entry_idx
            continue

        open_cid = 1
        for ci in range(nc):
            if ci == sel_ci:
                continue
            if int(enabled[ci]) != 0 and valid_m[ci, i] and side_m[ci, i] != 0:
                rej[REJ_EXISTING_POSITION] += 1

        hi = float(h[i])
        lw = float(l[i])
        clo = float(c[i])

        exr = 0
        raw_ex = 0.0
        ex_price = 0.0

        if i >= entry_idx:
            if side == 1:
                hit_stop = lw <= stop_px
                hit_tgt = hi >= tgt_px
                if hit_stop and hit_tgt:
                    exr = EX_STOP
                    raw_ex = stop_px
                    ex_price = _numba_exit_px(side, raw_ex, slip)
                elif hit_stop:
                    exr = EX_STOP
                    raw_ex = stop_px
                    ex_price = _numba_exit_px(side, raw_ex, slip)
                elif hit_tgt:
                    exr = EX_TARGET
                    raw_ex = tgt_px
                    ex_price = _numba_exit_px(side, raw_ex, slip)
            else:
                hit_stop = hi >= stop_px
                hit_tgt = lw <= tgt_px
                if hit_stop and hit_tgt:
                    exr = EX_STOP
                    raw_ex = stop_px
                    ex_price = _numba_exit_px(side, raw_ex, slip)
                elif hit_stop:
                    exr = EX_STOP
                    raw_ex = stop_px
                    ex_price = _numba_exit_px(side, raw_ex, slip)
                elif hit_tgt:
                    exr = EX_TARGET
                    raw_ex = tgt_px
                    ex_price = _numba_exit_px(side, raw_ex, slip)

        if exr == 0 and max_hold_m > 0:
            bh = i - entry_idx + 1
            if bh >= max_hold_m:
                exr = EX_MAX_HOLD
                raw_ex = clo
                ex_price = _numba_exit_px(side, raw_ex, slip)

        if exr == 0 and m >= eod_m:
            exr = EX_EOD
            raw_ex = clo
            ex_price = _numba_exit_px(side, raw_ex, slip)

        if exr == 0 and i < n - 1 and int(sess[i + 1]) != int(sess[i]):
            exr = EX_END_SESSION
            raw_ex = clo
            ex_price = _numba_exit_px(side, raw_ex, slip)

        if exr == 0 and i == n - 1:
            exr = EX_END_DATA
            raw_ex = clo
            ex_price = _numba_exit_px(side, raw_ex, slip)

        if exr != 0:
            if side == 1:
                gross = ex_price - ent_price
                r_mult = (ex_price - ent_price) / act_risk if act_risk > 0 else 0.0
            else:
                gross = ent_price - ex_price
                r_mult = (ent_price - ex_price) / act_risk if act_risk > 0 else 0.0
            net = gross * qty - comm
            daily_r += float(r_mult)
            if r_mult < 0.0 and cooldown_min > 0:
                cooldown_until = i + cooldown_min

            t_sig[tc] = sig_idx
            t_ent[tc] = entry_idx
            t_ex[tc] = i
            t_ci[tc] = sel_ci
            t_side[tc] = side
            t_ep[tc] = ent_price
            t_xp[tc] = ex_price
            t_sp[tc] = stop_px
            t_tg[tc] = tgt_px
            t_risk[tc] = act_risk
            t_net[tc] = net
            t_r[tc] = r_mult
            t_bh[tc] = i - entry_idx + 1
            t_exr[tc] = exr
            t_dtn[tc] = cur_dtn
            tc += 1

            in_pos = 0
            entry_idx = -1
            sig_idx = -1
            sel_ci = -1
            i += 1
            continue

        i += 1

    return (
        t_sig[:tc],
        t_ent[:tc],
        t_ex[:tc],
        t_ci[:tc],
        t_side[:tc],
        t_ep[:tc],
        t_xp[:tc],
        t_sp[:tc],
        t_tg[:tc],
        t_risk[:tc],
        t_net[:tc],
        t_r[:tc],
        t_bh[:tc],
        t_exr[:tc],
        t_dtn[:tc],
        rej,
    )


def simulate_combiner_numba(
    *,
    backtest_arrays: dict[str, Any],
    candidate_arrays: dict[str, np.ndarray],
    candidates: list[Candidate],
    meta_arrays: dict[str, np.ndarray],
    combiner_cfg: CombinerConfig,
    enabled_mask: np.ndarray,
    max_hold_per_candidate: np.ndarray,
    recompute_target: np.ndarray,
    quantity_per_candidate: np.ndarray,
    min_risk_per_candidate: np.ndarray,
    priority_float: np.ndarray,
    score_float: np.ndarray,
    rank_int: np.ndarray,
    active_start: np.ndarray,
    active_end: np.ndarray,
) -> dict[str, Any]:
    """Fast metrics-only simulation."""
    o = backtest_arrays["open"]
    h = backtest_arrays["high"]
    lo = backtest_arrays["low"]
    c = backtest_arrays["close"]
    minute = backtest_arrays["minute"].astype(np.int32)
    sess = backtest_arrays["session_id"].astype(np.int32)
    n = int(backtest_arrays["n"])
    nc = len(candidates)

    pol = (
        PRIORITY_SCORE_ADJUSTED
        if str(combiner_cfg.priority_policy).lower() == "score_adjusted_priority"
        else PRIORITY_METADATA_ONLY
    )
    opp = 1 if combiner_cfg.opposite_direction_skip_all else 0

    side_m = candidate_arrays["side"]
    valid_m = candidate_arrays["valid"]
    stop_m = candidate_arrays["stop"]
    tp_m = candidate_arrays["target_preview"]
    tmc_m = candidate_arrays["target_mode_code"]
    tr_m = candidate_arrays["target_r"]

    (
        t_sig,
        t_ent,
        t_ex,
        t_ci,
        t_side,
        t_ep,
        t_xp,
        t_sp,
        t_tg,
        t_risk,
        t_net,
        t_r,
        t_bh,
        t_exr,
        t_dtn,
        rej,
    ) = _simulate_combiner_numba(
        o,
        h,
        lo,
        c,
        minute,
        sess,
        side_m,
        valid_m,
        stop_m,
        tp_m,
        tmc_m,
        tr_m,
        priority_float,
        score_float,
        rank_int,
        active_start,
        active_end,
        enabled_mask.astype(np.int8),
        max_hold_per_candidate.astype(np.int32),
        recompute_target.astype(np.int8),
        quantity_per_candidate,
        min_risk_per_candidate,
        float(combiner_cfg.slippage_per_share),
        float(combiner_cfg.commission_per_trade),
        int(combiner_cfg.eod_exit_minute),
        int(combiner_cfg.no_new_after_minute),
        int(combiner_cfg.max_trades_per_day),
        float(combiner_cfg.daily_max_loss_r),
        int(combiner_cfg.cooldown_after_loss_minutes),
        pol,
        opp,
        n,
        nc,
    )

    ts_utc = meta_arrays["ts_utc"]
    session_date = meta_arrays["session_date"]
    trades_rows = []
    for k in range(len(t_sig)):
        ci = int(t_ci[k])
        sp = candidates[ci]
        trades_rows.append(
            {
                "trade_id": k + 1,
                "candidate_id": sp.candidate_id,
                "strategy": sp.strategy,
                "strategy_family": sp.family,
                "symbol": sp.symbol,
                "session_date": str(session_date[int(t_sig[k])]),
                "side": int(t_side[k]),
                "signal_idx": int(t_sig[k]),
                "signal_ts_utc": pd.Timestamp(ts_utc[int(t_sig[k])]).isoformat(),
                "entry_idx": int(t_ent[k]),
                "entry_ts_utc": pd.Timestamp(ts_utc[int(t_ent[k])]).isoformat(),
                "exit_idx": int(t_ex[k]),
                "exit_ts_utc": pd.Timestamp(ts_utc[int(t_ex[k])]).isoformat(),
                "entry_price": float(t_ep[k]),
                "exit_price": float(t_xp[k]),
                "stop_price": float(t_sp[k]),
                "target_price": float(t_tg[k]),
                "risk_per_share": float(t_risk[k]),
                "target_mode_code": int(tmc_m[ci, int(t_sig[k])]),
                "target_r": float(tr_m[ci, int(t_sig[k])]),
                "net_pnl": float(t_net[k]),
                "r_multiple": float(t_r[k]),
                "exit_reason": EXIT_NAMES.get(int(t_exr[k]), str(int(t_exr[k]))),
                "bars_held": int(t_bh[k]),
                "priority": sp.default_priority,
                "daily_trade_number": int(t_dtn[k]),
            }
        )

    trades_df = pd.DataFrame(trades_rows)
    n_bars = n
    equity = np.zeros(n_bars, dtype=np.float64)
    run = 0.0
    ti = 0
    trows = trades_rows
    for bi in range(n_bars):
        while ti < len(trows) and int(trows[ti]["exit_idx"]) == bi:
            run += float(trows[ti]["net_pnl"])
            ti += 1
        equity[bi] = run
    equity_df = pd.DataFrame(
        {"bar_idx": np.arange(n_bars, dtype=np.int32), "equity": equity}
    )

    log_df = pd.DataFrame()
    rej_df = pd.DataFrame()

    return {
        "trades_df": trades_df,
        "equity_df": equity_df,
        "candidate_signal_log_df": log_df,
        "rejected_signals_df": rej_df,
        "rejection_counts": rej,
    }


def simulate_combiner_legacy_logs(
    *,
    backtest_arrays: dict[str, Any],
    candidate_arrays: dict[str, np.ndarray],
    candidate_specs: list[Candidate],
    session_date: np.ndarray,
    minute: np.ndarray,
    ts_utc: np.ndarray,
    combiner_cfg: CombinerConfig,
    opposite_direction_skip_all: bool,
    max_hold_per_candidate: np.ndarray,
    recompute_target: np.ndarray,
    quantity_per_candidate: np.ndarray,
    min_risk_per_candidate: np.ndarray,
    enabled_mask: np.ndarray | None = None,
) -> dict[str, Any]:
    """Detailed Python path with per-signal logs (slower)."""
    o = backtest_arrays["open"]
    h = backtest_arrays["high"]
    lo = backtest_arrays["low"]
    c = backtest_arrays["close"]
    sess = backtest_arrays["session_id"]
    n = int(backtest_arrays["n"])
    n_c = len(candidate_specs)
    en = (
        np.ones(n_c, dtype=np.bool_)
        if enabled_mask is None
        else np.asarray(enabled_mask, dtype=np.bool_).reshape(
            n_c,
        )
    )
    if en.shape[0] != n_c:
        raise ValueError("enabled_mask length must match candidates")

    side_m = candidate_arrays["side"]
    valid_m = candidate_arrays["valid"]
    stop_m = candidate_arrays["stop"]
    tp_m = candidate_arrays["target_preview"]
    tmc_m = candidate_arrays["target_mode_code"]
    tr_m = candidate_arrays["target_r"]

    slip = float(combiner_cfg.slippage_per_share)
    comm = float(combiner_cfg.commission_per_trade)
    eod_m = int(combiner_cfg.eod_exit_minute)
    no_new = int(combiner_cfg.no_new_after_minute)
    max_daily_trades = int(combiner_cfg.max_trades_per_day)
    daily_loss_lim = float(combiner_cfg.daily_max_loss_r)
    cooldown_min = int(combiner_cfg.cooldown_after_loss_minutes)
    pol = str(combiner_cfg.priority_policy).lower()

    logs: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []

    in_pos = False
    entry_idx = -1
    sig_idx = -1
    sel_ci = -1
    side = 0
    stop_px = 0.0
    tgt_px = 0.0
    act_risk = 0.0
    ent_price = 0.0
    qty = 1.0
    max_hold_m = -1
    daily_trades = 0
    daily_r = 0.0
    prev_sess: int | None = None
    cooldown_until = -1

    trade_id = 0
    daily_trade_number = 0

    def eff_pri(ci: int) -> float:
        sp = candidate_specs[ci]
        sc = float((sp.selection or {}).get("score", 0.0) or 0.0)
        p = float(sp.default_priority)
        if pol == "score_adjusted_policy" or pol == "score_adjusted_priority":
            adj = max(-5.0, min(5.0, sc * 5.0))
            return p + adj
        return p

    def log_sig(
        bar_i: int, ci: int, sel: bool, reason: str, sel_id: str, open_cid: str
    ) -> None:
        sp = candidate_specs[ci]
        logs.append(
            {
                "ts_utc": (
                    pd.Timestamp(ts_utc[bar_i]).isoformat()
                    if bar_i < len(ts_utc)
                    else ""
                ),
                "session_date": (
                    str(session_date[bar_i]) if bar_i < len(session_date) else ""
                ),
                "minute_from_open": int(minute[bar_i]) if bar_i < len(minute) else -1,
                "candidate_id": sp.candidate_id,
                "strategy": sp.strategy,
                "side": int(side_m[ci, bar_i]),
                "priority": sp.default_priority,
                "selected": sel,
                "rejection_reason": reason,
                "selected_candidate_id": sel_id,
                "open_position_candidate_id": open_cid,
            }
        )

    i = 0
    while i < n:
        sid = int(sess[i])
        if prev_sess is None or sid != prev_sess:
            daily_trades = 0
            daily_r = 0.0
            prev_sess = sid

        m = int(minute[i])

        if not in_pos:
            if i < cooldown_until:
                i += 1
                continue
            if i >= n - 1:
                i += 1
                continue

            if daily_r <= daily_loss_lim:
                i += 1
                continue
            if daily_trades >= max_daily_trades:
                i += 1
                continue

            raw_idx = [
                ci
                for ci in range(n_c)
                if bool(en[ci]) and bool(valid_m[ci, i]) and int(side_m[ci, i]) != 0
            ]
            open_cid = ""

            if not raw_idx:
                i += 1
                continue

            eligible: list[int] = []
            for ci in raw_idx:
                sp = candidate_specs[ci]
                rr = ""
                if not (sp.active_start_minute <= m <= sp.active_end_minute):
                    rr = "wrong_time_window"
                elif m >= no_new:
                    rr = "no_new_after"
                elif daily_r <= daily_loss_lim:
                    rr = "daily_loss_limit"
                elif daily_trades >= max_daily_trades:
                    rr = "max_trades_reached"
                elif i < cooldown_until:
                    rr = "cooldown_after_loss"
                elif i + 1 >= n or int(sess[i + 1]) != int(sess[i]):
                    rr = "session_boundary_no_entry"

                if rr:
                    log_sig(i, ci, False, rr, "", open_cid)
                else:
                    eligible.append(ci)

            if eligible:
                sides = {int(side_m[cj, i]) for cj in eligible}
                if opposite_direction_skip_all and len(sides) > 1:
                    for cj in eligible:
                        log_sig(i, cj, False, "opposite_direction_skip", "", open_cid)
                    eligible = []

            if eligible:
                eligible.sort(
                    key=lambda cj: (
                        -eff_pri(cj),
                        -float(
                            (candidate_specs[cj].selection or {}).get("score", 0.0)
                            or 0.0
                        ),
                        candidate_specs[cj].candidate_rank,
                        cj,
                    )
                )
                best = eligible[0]
                spb = candidate_specs[best]
                sd = int(side_m[best, i])
                ent_raw = float(o[i + 1])
                stop_px = float(stop_m[best, i])
                if sd == 1:
                    ent_price = ent_raw + slip
                else:
                    ent_price = ent_raw - slip
                tm = int(tmc_m[best, i])
                tr = float(tr_m[best, i])
                tprev = float(tp_m[best, i])
                rc = int(recompute_target[best])

                mr = (
                    float(min_risk_per_candidate[best])
                    if best < len(min_risk_per_candidate)
                    else 0.0
                )

                if tm == 1:
                    tmode = "fixed_r"
                elif tm == 2:
                    tmode = "fixed_price"
                else:
                    log_sig(i, best, False, "invalid_target_mode", "", open_cid)
                    i += 1
                    continue

                ok_v, reason_v, act_risk, resolved_tgt = validate_trade_setup(
                    side=sd,
                    entry=ent_price,
                    stop=stop_px,
                    target_mode=tmode,
                    target_preview=tprev,
                    target_r=tr if tm == 1 else None,
                    min_risk_per_share=mr,
                )

                tgt_px = 0.0
                if not ok_v:
                    log_sig(i, best, False, reason_v, "", open_cid)
                    i += 1
                    continue

                if tm == 1:
                    if rc != 0:
                        tgt_px = float(resolved_tgt)
                    else:
                        tgt_px = tprev
                        if not math.isfinite(tgt_px):
                            log_sig(i, best, False, "invalid_price_nan", "", open_cid)
                            i += 1
                            continue
                else:
                    tgt_px = float(resolved_tgt)

                best_id = spb.candidate_id
                for cj in eligible:
                    is_sel = cj == best
                    rr = "" if is_sel else "lower_priority_conflict"
                    log_sig(i, cj, is_sel, rr, best_id, open_cid)

                in_pos = True
                entry_idx = i + 1
                sig_idx = i
                sel_ci = best
                side = sd
                qty = float(quantity_per_candidate[best])
                mh = int(max_hold_per_candidate[best])
                max_hold_m = mh if mh > 0 else -1
                daily_trades += 1
                daily_trade_number = daily_trades
                i = entry_idx
                continue

            i += 1
            continue

        open_cid = candidate_specs[sel_ci].candidate_id if sel_ci >= 0 else ""
        for ci in range(n_c):
            if ci == sel_ci:
                continue
            if bool(en[ci]) and bool(valid_m[ci, i]) and int(side_m[ci, i]) != 0:
                log_sig(i, ci, False, "existing_position", "", open_cid)

        hi = float(h[i])
        lw = float(lo[i])
        clo = float(c[i])

        exr = 0
        raw_ex = 0.0
        ex_price = 0.0

        if i >= entry_idx:
            if side == 1:
                hit_stop = lw <= stop_px
                hit_tgt = hi >= tgt_px
                if hit_stop and hit_tgt:
                    exr = EX_STOP
                    raw_ex = stop_px
                    ex_price = _py_exit_price(side, raw_ex, slip)
                elif hit_stop:
                    exr = EX_STOP
                    raw_ex = stop_px
                    ex_price = _py_exit_price(side, raw_ex, slip)
                elif hit_tgt:
                    exr = EX_TARGET
                    raw_ex = tgt_px
                    ex_price = _py_exit_price(side, raw_ex, slip)
            else:
                hit_stop = hi >= stop_px
                hit_tgt = lw <= tgt_px
                if hit_stop and hit_tgt:
                    exr = EX_STOP
                    raw_ex = stop_px
                    ex_price = _py_exit_price(side, raw_ex, slip)
                elif hit_stop:
                    exr = EX_STOP
                    raw_ex = stop_px
                    ex_price = _py_exit_price(side, raw_ex, slip)
                elif hit_tgt:
                    exr = EX_TARGET
                    raw_ex = tgt_px
                    ex_price = _py_exit_price(side, raw_ex, slip)

        if exr == 0 and max_hold_m > 0:
            bh = i - entry_idx + 1
            if bh >= max_hold_m:
                exr = EX_MAX_HOLD
                raw_ex = clo
                ex_price = _py_exit_price(side, raw_ex, slip)

        if exr == 0 and m >= eod_m:
            exr = EX_EOD
            raw_ex = clo
            ex_price = _py_exit_price(side, raw_ex, slip)

        if exr == 0 and i < n - 1 and int(sess[i + 1]) != int(sess[i]):
            exr = EX_END_SESSION
            raw_ex = clo
            ex_price = _py_exit_price(side, raw_ex, slip)

        if exr == 0 and i == n - 1:
            exr = EX_END_DATA
            raw_ex = clo
            ex_price = _py_exit_price(side, raw_ex, slip)

        if exr != 0:
            if side == 1:
                gross = ex_price - ent_price
                r_mult = (ex_price - ent_price) / act_risk if act_risk > 0 else 0.0
            else:
                gross = ent_price - ex_price
                r_mult = (ent_price - ex_price) / act_risk if act_risk > 0 else 0.0
            net = gross * qty - comm
            daily_r += float(r_mult)
            if r_mult < 0.0 and cooldown_min > 0:
                cooldown_until = i + cooldown_min

            trade_id += 1
            sp = candidate_specs[sel_ci]
            trades.append(
                {
                    "trade_id": trade_id,
                    "candidate_id": sp.candidate_id,
                    "strategy": sp.strategy,
                    "strategy_family": sp.family,
                    "symbol": sp.symbol,
                    "session_date": str(session_date[sig_idx]),
                    "side": side,
                    "signal_idx": sig_idx,
                    "signal_ts_utc": pd.Timestamp(ts_utc[sig_idx]).isoformat(),
                    "entry_idx": entry_idx,
                    "entry_ts_utc": pd.Timestamp(ts_utc[entry_idx]).isoformat(),
                    "exit_idx": i,
                    "exit_ts_utc": pd.Timestamp(ts_utc[i]).isoformat(),
                    "entry_price": ent_price,
                    "exit_price": ex_price,
                    "stop_price": stop_px,
                    "target_price": tgt_px,
                    "risk_per_share": act_risk,
                    "target_mode_code": int(tmc_m[sel_ci, sig_idx]),
                    "target_r": float(tr_m[sel_ci, sig_idx]),
                    "net_pnl": net,
                    "r_multiple": r_mult,
                    "exit_reason": EXIT_NAMES.get(exr, str(exr)),
                    "bars_held": i - entry_idx + 1,
                    "priority": sp.default_priority,
                    "daily_trade_number": daily_trade_number,
                }
            )
            in_pos = False
            entry_idx = -1
            sig_idx = -1
            sel_ci = -1
            i += 1
            continue

        i += 1

    trades_df = pd.DataFrame(trades)
    log_df = pd.DataFrame(logs)
    n_bars = n
    equity = np.zeros(n_bars, dtype=np.float64)
    run = 0.0
    ti = 0
    trows = trades_df.to_dict("records") if len(trades_df) > 0 else []
    for bi in range(n_bars):
        while ti < len(trows) and int(trows[ti]["exit_idx"]) == bi:
            run += float(trows[ti]["net_pnl"])
            ti += 1
        equity[bi] = run
    equity_df = pd.DataFrame(
        {"bar_idx": np.arange(n_bars, dtype=np.int32), "equity": equity}
    )
    rej = log_df[
        (log_df["selected"] == False)
        & (log_df["rejection_reason"].astype(str).str.len() > 0)
    ].copy()

    return {
        "trades_df": trades_df,
        "equity_df": equity_df,
        "candidate_signal_log_df": log_df,
        "rejected_signals_df": rej,
        "rejection_counts": None,
    }


# Back-compat alias
simulate_combiner = simulate_combiner_legacy_logs
