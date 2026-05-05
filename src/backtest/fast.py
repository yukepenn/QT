"""Generic Numba-accelerated backtest from precomputed signal arrays (strategy-agnostic)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numba import njit

# target_mode_code: 0 = none, 1 = fixed_r, 2 = fixed_price
TM_NONE = np.int8(0)
TM_FIXED_R = np.int8(1)
TM_FIXED_PX = np.int8(2)

# exit_reason_code
EX_STOP = 1
EX_TARGET = 2
EX_EOD = 3
EX_END_DATA = 4
EX_MAX_HOLD = 5


@dataclass(frozen=True)
class FastBacktestConfig:
    eod_exit_minute: int = 389
    quantity: float = 1.0
    commission_per_trade: float = 0.0
    slippage_per_share: float = 0.0


def prepare_backtest_arrays(df: pd.DataFrame) -> dict[str, Any]:
    need = ["ts_utc", "ts_ny", "session_date", "minute_from_open", "open", "high", "low", "close"]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise ValueError(f"prepare_backtest_arrays missing: {miss}")
    work = df.sort_values("ts_utc").reset_index(drop=True)
    sid_codes, uniques = pd.factorize(work["session_date"], sort=False)
    return {
        "open": work["open"].to_numpy(dtype=np.float64, copy=False),
        "high": work["high"].to_numpy(dtype=np.float64, copy=False),
        "low": work["low"].to_numpy(dtype=np.float64, copy=False),
        "close": work["close"].to_numpy(dtype=np.float64, copy=False),
        "minute": work["minute_from_open"].to_numpy(dtype=np.int32, copy=False),
        "session_id": sid_codes.astype(np.int32),
        "session_dates": uniques,
        "n": len(work),
    }


@njit(cache=True)
def _simulate_numba(
    open_a: np.ndarray,
    high_a: np.ndarray,
    low_a: np.ndarray,
    close_a: np.ndarray,
    minute_a: np.ndarray,
    session_a: np.ndarray,
    side_a: np.ndarray,
    valid_a: np.ndarray,
    stop_a: np.ndarray,
    tgt_preview_a: np.ndarray,
    tgt_mode_a: np.ndarray,
    tgt_r_a: np.ndarray,
    eod_exit_minute: int,
    quantity: float,
    commission_per_trade: float,
    slippage_per_share: float,
    recompute_target_from_entry: int,
    max_hold_minutes: int,
) -> tuple[
    int,
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
    n = len(open_a)
    max_t = n
    t_sig = np.empty(max_t, dtype=np.int32)
    t_ent = np.empty(max_t, dtype=np.int32)
    t_ex = np.empty(max_t, dtype=np.int32)
    t_side = np.empty(max_t, dtype=np.int8)
    t_ep = np.empty(max_t, dtype=np.float64)
    t_xp = np.empty(max_t, dtype=np.float64)
    t_stop = np.empty(max_t, dtype=np.float64)
    t_tgt = np.empty(max_t, dtype=np.float64)
    t_risk = np.empty(max_t, dtype=np.float64)
    t_net = np.empty(max_t, dtype=np.float64)
    t_r = np.empty(max_t, dtype=np.float64)
    t_exr = np.empty(max_t, dtype=np.int32)
    t_bars = np.empty(max_t, dtype=np.int32)
    t_mfe = np.empty(max_t, dtype=np.float64)
    t_mae = np.empty(max_t, dtype=np.float64)

    tc = 0
    i = 0
    in_pos = 0
    entry_idx = -1
    side = 0
    stop_px = 0.0
    tgt_px = 0.0
    act_risk = 0.0
    ent_price = 0.0
    sig_idx = -1

    while i < n:
        if in_pos == 0:
            v = valid_a[i]
            sd = side_a[i]
            if v and sd != 0 and i + 1 < n:
                if session_a[i + 1] != session_a[i]:
                    i += 1
                    continue
                ent_raw = open_a[i + 1]
                stop_px = stop_a[i]
                if sd == 1:
                    ent_price = ent_raw + slippage_per_share
                else:
                    ent_price = ent_raw - slippage_per_share
                # Validate finite prices and correct stop side before computing risk.
                if not (np.isfinite(ent_price) and np.isfinite(stop_px)):
                    i += 1
                    continue
                if sd == 1:
                    if not (stop_px < ent_price):
                        i += 1
                        continue
                    act_risk = ent_price - stop_px
                else:
                    if not (stop_px > ent_price):
                        i += 1
                        continue
                    act_risk = stop_px - ent_price
                if not np.isfinite(act_risk) or act_risk <= 0.0:
                    i += 1
                    continue

                tm = tgt_mode_a[i]
                tr = tgt_r_a[i]
                tprev = tgt_preview_a[i]

                if tm == 1:
                    if not (np.isfinite(tr) and tr > 0.0):
                        i += 1
                        continue
                    if recompute_target_from_entry != 0:
                        if sd == 1:
                            tgt_px = ent_price + tr * act_risk
                        else:
                            tgt_px = ent_price - tr * act_risk
                    else:
                        tgt_px = tprev
                elif tm == 2:
                    tgt_px = tprev
                else:
                    i += 1
                    continue

                if not np.isfinite(tgt_px):
                    i += 1
                    continue
                # For fixed_price targets, enforce correct side vs entry.
                if tm == 2:
                    if sd == 1:
                        if not (tgt_px > ent_price):
                            i += 1
                            continue
                    else:
                        if not (tgt_px < ent_price):
                            i += 1
                            continue

                in_pos = 1
                entry_idx = i + 1
                side = sd
                sig_idx = i
                i = entry_idx
                continue
            i += 1
            continue

        hi = high_a[i]
        lo = low_a[i]
        clo = close_a[i]
        m = minute_a[i]

        ent_raw = open_a[entry_idx]
        if side == 1:
            ent_price = ent_raw + slippage_per_share
        else:
            ent_price = ent_raw - slippage_per_share

        exr = 0
        raw_ex = 0.0
        ex_price = 0.0

        if i >= entry_idx:
            if side == 1:
                hit_stop = lo <= stop_px
                hit_tgt = hi >= tgt_px
                if hit_stop and hit_tgt:
                    exr = EX_STOP
                    raw_ex = stop_px
                    ex_price = raw_ex - slippage_per_share
                elif hit_stop:
                    exr = EX_STOP
                    raw_ex = stop_px
                    ex_price = raw_ex - slippage_per_share
                elif hit_tgt:
                    exr = EX_TARGET
                    raw_ex = tgt_px
                    ex_price = raw_ex - slippage_per_share
            else:
                hit_stop = hi >= stop_px
                hit_tgt = lo <= tgt_px
                if hit_stop and hit_tgt:
                    exr = EX_STOP
                    raw_ex = stop_px
                    ex_price = raw_ex + slippage_per_share
                elif hit_stop:
                    exr = EX_STOP
                    raw_ex = stop_px
                    ex_price = raw_ex + slippage_per_share
                elif hit_tgt:
                    exr = EX_TARGET
                    raw_ex = tgt_px
                    ex_price = raw_ex + slippage_per_share

        if exr == 0 and max_hold_minutes > 0:
            bh = i - entry_idx + 1
            if bh >= max_hold_minutes:
                exr = EX_MAX_HOLD
                raw_ex = clo
                if side == 1:
                    ex_price = raw_ex - slippage_per_share
                else:
                    ex_price = raw_ex + slippage_per_share

        if exr == 0 and m >= eod_exit_minute:
            exr = EX_EOD
            raw_ex = clo
            if side == 1:
                ex_price = raw_ex - slippage_per_share
            else:
                ex_price = raw_ex + slippage_per_share

        at_end = i == n - 1
        if exr == 0 and at_end:
            exr = EX_END_DATA
            raw_ex = clo
            if side == 1:
                ex_price = raw_ex - slippage_per_share
            else:
                ex_price = raw_ex + slippage_per_share

        if exr != 0:
            if side == 1:
                gross = ex_price - ent_price
                r_mult = (ex_price - ent_price) / act_risk if act_risk > 0 else 0.0
            else:
                gross = ent_price - ex_price
                r_mult = (ent_price - ex_price) / act_risk if act_risk > 0 else 0.0
            net = gross * quantity - commission_per_trade

            mx_hi = high_a[entry_idx]
            mn_lo = low_a[entry_idx]
            for j in range(entry_idx + 1, i + 1):
                if high_a[j] > mx_hi:
                    mx_hi = high_a[j]
                if low_a[j] < mn_lo:
                    mn_lo = low_a[j]
            if side == 1:
                mfe = mx_hi - ent_price
                mae = ent_price - mn_lo
            else:
                mfe = ent_price - mn_lo
                mae = mx_hi - ent_price

            t_sig[tc] = sig_idx
            t_ent[tc] = entry_idx
            t_ex[tc] = i
            t_side[tc] = side
            t_ep[tc] = ent_price
            t_xp[tc] = ex_price
            t_stop[tc] = stop_px
            t_tgt[tc] = tgt_px
            t_risk[tc] = act_risk
            t_net[tc] = net
            t_r[tc] = r_mult
            t_exr[tc] = exr
            t_bars[tc] = i - entry_idx + 1
            t_mfe[tc] = mfe
            t_mae[tc] = mae
            tc += 1

            in_pos = 0
            entry_idx = -1
            i += 1
            continue

        i += 1

    return tc, t_sig, t_ent, t_ex, t_side, t_ep, t_xp, t_stop, t_tgt, t_risk, t_net, t_r, t_exr, t_bars, t_mfe, t_mae


def _profit_factor_numba(net: np.ndarray) -> float:
    wins = 0.0
    losses = 0.0
    for i in range(len(net)):
        v = net[i]
        if v > 0:
            wins += v
        elif v < 0:
            losses += v
    if losses == 0:
        return float("inf") if wins > 0 else 0.0
    return wins / abs(losses)


def _max_dd_numba(cum: np.ndarray) -> float:
    if len(cum) == 0:
        return 0.0
    # Drawdown is measured from an initial equity baseline of 0.0.
    peak = 0.0
    dd = 0.0
    for i in range(len(cum)):
        v = cum[i]
        if v > peak:
            peak = v
        d = v - peak
        if d < dd:
            dd = d
    return dd


def _metrics_from_trades(
    net: np.ndarray,
    r: np.ndarray,
    bars: np.ndarray,
    exr: np.ndarray,
) -> dict[str, Any]:
    nt = int(len(net))
    if nt == 0:
        return {
            "trades": 0,
            "win_rate": 0.0,
            "total_net_pnl": 0.0,
            "avg_net_pnl": 0.0,
            "total_r": 0.0,
            "avg_r": 0.0,
            "profit_factor": 0.0,
            "max_drawdown_pnl": 0.0,
            "max_drawdown_r": 0.0,
            "avg_bars_held": 0.0,
            "stop_count": 0,
            "target_count": 0,
            "eod_count": 0,
            "end_of_data_count": 0,
            "max_hold_count": 0,
        }

    wins = int(np.sum(net > 0))
    cum_p = np.cumsum(net)
    cum_r = np.cumsum(r)
    stop_c = int(np.sum(exr == EX_STOP))
    tgt_c = int(np.sum(exr == EX_TARGET))
    eod_c = int(np.sum(exr == EX_EOD))
    eod_data_c = int(np.sum(exr == EX_END_DATA))
    mh_c = int(np.sum(exr == EX_MAX_HOLD))

    return {
        "trades": nt,
        "win_rate": wins / nt,
        "total_net_pnl": float(np.sum(net)),
        "avg_net_pnl": float(np.mean(net)),
        "total_r": float(np.sum(r)),
        "avg_r": float(np.mean(r)),
        "profit_factor": _profit_factor_numba(net),
        "max_drawdown_pnl": float(_max_dd_numba(cum_p)),
        "max_drawdown_r": float(_max_dd_numba(cum_r)),
        "avg_bars_held": float(np.mean(bars)),
        "stop_count": stop_c,
        "target_count": tgt_c,
        "eod_count": eod_c,
        "end_of_data_count": eod_data_c,
        "max_hold_count": mh_c,
    }


def run_fast_backtest_from_arrays(
    arrays: dict[str, Any],
    signal_arrays: dict[str, np.ndarray],
    *,
    eod_exit_minute: int = 389,
    quantity: float = 1.0,
    commission_per_trade: float = 0.0,
    slippage_per_share: float = 0.0,
    recompute_target_from_entry: bool = True,
    max_hold_minutes: int | None = None,
) -> dict[str, Any]:
    o = arrays["open"]
    h = arrays["high"]
    lo = arrays["low"]
    c = arrays["close"]
    minute = arrays["minute"]
    sess = arrays["session_id"]

    sa = signal_arrays["side"].astype(np.int8)
    va = signal_arrays["valid"].astype(np.bool_)
    st = signal_arrays["stop"].astype(np.float64)
    tp = signal_arrays["target_preview"].astype(np.float64)
    tmc = signal_arrays["target_mode_code"].astype(np.int8)
    tr = signal_arrays["target_r"].astype(np.float64)

    reco = 1 if recompute_target_from_entry else 0
    mh = -1 if max_hold_minutes is None else int(max_hold_minutes)
    if mh == 0:
        raise ValueError("max_hold_minutes must be > 0 or None")
    if mh < 0:
        mh = -1
    tc, _, _, _, _, _, _, _, _, _, t_net, t_r, t_exr, t_bars, _, _ = _simulate_numba(
        o,
        h,
        lo,
        c,
        minute,
        sess,
        sa,
        va,
        st,
        tp,
        tmc,
        tr,
        int(eod_exit_minute),
        float(quantity),
        float(commission_per_trade),
        float(slippage_per_share),
        reco,
        mh,
    )
    if tc == 0:
        return _metrics_from_trades(
            np.empty(0, np.float64),
            np.empty(0, np.float64),
            np.empty(0, np.int32),
            np.empty(0, np.int32),
        )
    return _metrics_from_trades(t_net[:tc], t_r[:tc], t_bars[:tc], t_exr[:tc])
