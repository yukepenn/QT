"""VWAP band mean-reversion / reversal strategy (standard signal schema)."""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd
from numba import njit

from src.backtest.constants import TM_FIXED_PX, TM_FIXED_R, TM_NONE
from src.data.read_bars import read_bars
from src.features.build_features import build_basic_features
from src.strategies.strategy.base import (
    BaseStrategy,
    init_standard_signal_columns,
    validate_standard_signal_columns,
)
from src.strategies.strategy.fast_utils import (
    apply_min_risk_filter_arrays,
    apply_min_risk_filter_df,
    get_min_risk_per_share,
    prev_by_session,
    rolling_max_by_session,
    rolling_min_by_session,
    session_id_from_dates,
    thin_first_signal_per_session_numba,
    thin_per_side_per_session_numba,
)

# Actual column names from src/features/vwap.py (band multipliers in names)
_BAND_COLS: dict[float, tuple[str, str]] = {
    1.0: ("vwap_upper_1.0", "vwap_lower_1.0"),
    2.0: ("vwap_upper_2.0", "vwap_lower_2.0"),
}


def _validate_vwap_reversal_config(sig_cfg: dict[str, Any], risk_cfg: dict[str, Any]) -> None:
    side = str(sig_cfg.get("side", "both"))
    if side not in ("long_only", "short_only", "both"):
        raise ValueError(f"side must be long_only, short_only, or both, got {side!r}")

    daily_mode = str(sig_cfg.get("daily_signal_mode", "first_signal"))
    if daily_mode not in ("first_signal", "per_side"):
        raise ValueError(f"daily_signal_mode must be first_signal or per_side, got {daily_mode!r}")

    confirm = str(sig_cfg.get("confirm_mode", "one_bar_reclaim"))
    if confirm not in ("one_bar_reclaim", "close_inside_band", "momentum_turn"):
        raise ValueError(f"confirm_mode invalid: {confirm!r}")

    slope_mode = str(sig_cfg.get("slope_filter_mode", "none"))
    if slope_mode not in ("against_trend", "flat_or_reverting", "none"):
        raise ValueError(f"slope_filter_mode invalid: {slope_mode!r}")

    ext = float(sig_cfg["extension_band"])
    if ext not in (1.0, 2.0):
        raise ValueError(f"extension_band must be 1.0 or 2.0, got {ext}")

    entry_start = int(sig_cfg["entry_start_minute"])
    entry_end = int(sig_cfg["entry_end_minute"])
    if entry_end <= entry_start:
        raise ValueError("entry_end_minute must be > entry_start_minute")

    stop_mode = str(risk_cfg.get("stop_mode", "band_extreme"))
    if stop_mode not in ("band_extreme", "recent_swing", "fixed_pct"):
        raise ValueError(f"stop_mode invalid: {stop_mode!r}")

    target_mode = str(risk_cfg.get("target_mode", "fixed_price"))
    if target_mode not in ("fixed_r", "fixed_price"):
        raise ValueError(f"target_mode invalid: {target_mode!r}")

    target_ref = str(risk_cfg.get("target_ref", "vwap"))
    if target_mode == "fixed_price" and target_ref != "vwap":
        raise ValueError(f"fixed_price currently requires target_ref vwap, got {target_ref!r}")

    target_r = float(risk_cfg["target_r"])
    if target_mode == "fixed_r" and target_r <= 0:
        raise ValueError("target_r must be > 0 when target_mode is fixed_r")

    swing_lb = int(risk_cfg.get("swing_lookback", 5))
    if swing_lb < 1:
        raise ValueError("swing_lookback must be >= 1")

    max_tr = int(risk_cfg.get("max_trades_per_day", 1))
    if max_tr < 1:
        raise ValueError("max_trades_per_day must be >= 1")

    stop_buf = float(risk_cfg.get("stop_buffer", 0.0))
    if stop_buf < 0:
        raise ValueError("stop_buffer must be >= 0")


def _signal_df_to_fast_arrays(sig: pd.DataFrame) -> dict[str, np.ndarray]:
    """Debug helper: map readable `generate_vwap_reversal_signals` DataFrame to fast array dict."""
    side = sig["sig_side"].fillna(0).to_numpy(dtype=np.float64).astype(np.int8)
    valid = sig["sig_valid"].fillna(False).to_numpy(dtype=bool)
    stp = pd.to_numeric(sig["sig_stop"], errors="coerce").fillna(0.0).to_numpy(dtype=np.float64)
    tgt = pd.to_numeric(sig["sig_target"], errors="coerce").fillna(0.0).to_numpy(dtype=np.float64)
    tr = pd.to_numeric(sig["sig_target_r"], errors="coerce").fillna(0.0).to_numpy(dtype=np.float64)
    risk = pd.to_numeric(sig["sig_risk_per_share"], errors="coerce").fillna(0.0).to_numpy(dtype=np.float64)
    mode_str = sig["sig_target_mode"].fillna("").astype(str).str.strip().str.lower()
    tmc = np.full(len(sig), TM_NONE, dtype=np.int8)
    tmc[mode_str == "fixed_r"] = TM_FIXED_R
    tmc[mode_str == "fixed_price"] = TM_FIXED_PX
    return {
        "side": side,
        "valid": valid,
        "stop": stp,
        "target_preview": tgt,
        "target_mode_code": tmc,
        "target_r": tr,
        "risk_preview": risk,
    }


@dataclass(frozen=True)
class VWAPReversalContext:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    vwap: np.ndarray
    vwap_slope_5: np.ndarray
    upper_1: np.ndarray
    lower_1: np.ndarray
    upper_2: np.ndarray
    lower_2: np.ndarray
    prev_close: np.ndarray
    prev_low: np.ndarray
    prev_high: np.ndarray
    prev_upper_1: np.ndarray
    prev_lower_1: np.ndarray
    prev_upper_2: np.ndarray
    prev_lower_2: np.ndarray
    rolling_low_swing: np.ndarray
    rolling_high_swing: np.ndarray
    swing_lookback: int


def prepare_vwap_reversal_context(df: pd.DataFrame, config: dict[str, Any]) -> VWAPReversalContext:
    risk_cfg = config.get("risk") or {}
    swing_lb = int(risk_cfg.get("swing_lookback", 5))
    if swing_lb < 1:
        raise ValueError("swing_lookback must be >= 1")

    need_cols = [
        "session_date",
        "minute_from_open",
        "open",
        "high",
        "low",
        "close",
        "vwap",
        "vwap_slope_5",
        "vwap_upper_1.0",
        "vwap_lower_1.0",
        "vwap_upper_2.0",
        "vwap_lower_2.0",
    ]
    miss = [c for c in need_cols if c not in df.columns]
    if miss:
        raise ValueError(f"VWAPReversalStrategy missing feature columns: {miss}")

    if "ts_utc" in df.columns:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
    else:
        work = df.reset_index(drop=True)

    n = len(work)
    sid = session_id_from_dates(work["session_date"])
    minute = work["minute_from_open"].to_numpy(dtype=np.int32, copy=False)
    op = work["open"].to_numpy(dtype=np.float64, copy=False)
    hi = work["high"].to_numpy(dtype=np.float64, copy=False)
    lo = work["low"].to_numpy(dtype=np.float64, copy=False)
    cl = work["close"].to_numpy(dtype=np.float64, copy=False)
    vw = work["vwap"].to_numpy(dtype=np.float64, copy=False)
    sl5 = work["vwap_slope_5"].to_numpy(dtype=np.float64, copy=False)
    u1 = work["vwap_upper_1.0"].to_numpy(dtype=np.float64, copy=False)
    l1 = work["vwap_lower_1.0"].to_numpy(dtype=np.float64, copy=False)
    u2 = work["vwap_upper_2.0"].to_numpy(dtype=np.float64, copy=False)
    l2 = work["vwap_lower_2.0"].to_numpy(dtype=np.float64, copy=False)

    prev_close = prev_by_session(cl, sid)
    prev_low = prev_by_session(lo, sid)
    prev_high = prev_by_session(hi, sid)
    prev_upper_1 = prev_by_session(u1, sid)
    prev_lower_1 = prev_by_session(l1, sid)
    prev_upper_2 = prev_by_session(u2, sid)
    prev_lower_2 = prev_by_session(l2, sid)
    roll_lo = rolling_min_by_session(lo, sid, swing_lb)
    roll_hi = rolling_max_by_session(hi, sid, swing_lb)

    return VWAPReversalContext(
        n=n,
        session_id=sid,
        minute=minute,
        open=op,
        high=hi,
        low=lo,
        close=cl,
        vwap=vw,
        vwap_slope_5=sl5,
        upper_1=u1,
        lower_1=l1,
        upper_2=u2,
        lower_2=l2,
        prev_close=prev_close,
        prev_low=prev_low,
        prev_high=prev_high,
        prev_upper_1=prev_upper_1,
        prev_lower_1=prev_lower_1,
        prev_upper_2=prev_upper_2,
        prev_lower_2=prev_lower_2,
        rolling_low_swing=roll_lo,
        rolling_high_swing=roll_hi,
        swing_lookback=swing_lb,
    )


@njit(cache=True)
def _build_vwap_reversal_arrays_numba(
    session_id,
    minute,
    high,
    low,
    close,
    vwap,
    slope,
    upper_band,
    lower_band,
    prev_close,
    prev_low,
    prev_high,
    prev_upper,
    prev_lower,
    rolling_low_swing,
    rolling_high_swing,
    side_code,
    entry_start,
    entry_end,
    confirm_mode_code,
    daily_mode_code,
    require_slope,
    slope_mode_code,
    use_max_abs_slope,
    max_abs_slope,
    use_min_band_width,
    min_band_width_pct,
    use_max_band_width,
    max_band_width_pct,
    stop_mode_code,
    stop_buffer,
    stop_pct,
    tgt_mode_scalar,
    target_r_value,
    max_trades_per_day,
):
    n = len(session_id)
    cand_long = np.zeros(n, dtype=np.bool_)
    cand_short = np.zeros(n, dtype=np.bool_)
    stop_long_all = np.zeros(n, dtype=np.float64)
    stop_short_all = np.zeros(n, dtype=np.float64)
    risk_long_all = np.zeros(n, dtype=np.float64)
    risk_short_all = np.zeros(n, dtype=np.float64)

    for i in range(n):
        mi = minute[i]
        if mi < entry_start or mi > entry_end:
            continue
        vw_i = vwap[i]
        ub_i = upper_band[i]
        lb_i = lower_band[i]
        cl = close[i]
        hi = high[i]
        lo = low[i]
        sl = slope[i]

        if vw_i != vw_i or ub_i != ub_i or lb_i != lb_i or cl != cl:
            continue
        if -1e-12 < vw_i < 1e-12:
            continue

        bw = (ub_i - lb_i) / vw_i
        if use_min_band_width != 0 and bw < min_band_width_pct:
            continue
        if use_max_band_width != 0 and bw > max_band_width_pct:
            continue

        ls_ok = True
        ss_ok = True
        if require_slope != 0 and slope_mode_code != 0:
            if slope_mode_code == 1:
                ls_ok = sl <= 0.0
                ss_ok = sl >= 0.0
            elif slope_mode_code == 2:
                if use_max_abs_slope != 0:
                    ls_ok = sl <= max_abs_slope
                    ss_ok = sl >= -max_abs_slope

        pc = prev_close[i]
        plw = prev_low[i]
        phg = prev_high[i]
        pu = prev_upper[i]
        plb = prev_lower[i]
        rlw = rolling_low_swing[i]
        rhg = rolling_high_swing[i]

        raw_l = False
        raw_s = False

        if confirm_mode_code == 1:
            if pc == pc and plb == plb:
                raw_l = ls_ok and (pc <= plb) and (cl > lb_i)
            if pc == pc and pu == pu:
                raw_s = ss_ok and (pc >= pu) and (cl < ub_i)
        elif confirm_mode_code == 2:
            raw_l = ls_ok and (lo <= lb_i) and (cl > lb_i)
            raw_s = ss_ok and (hi >= ub_i) and (cl < ub_i)
        else:
            if pc == pc:
                c1 = False
                if plb == plb:
                    c1 = pc <= plb
                c2 = False
                if plw == plw and plb == plb:
                    c2 = plw <= plb
                raw_l = ls_ok and (cl > pc) and (c1 or c2)
                c1s = False
                if pu == pu:
                    c1s = pc >= pu
                c2s = False
                if phg == phg and pu == pu:
                    c2s = phg >= pu
                raw_s = ss_ok and (cl < pc) and (c1s or c2s)

        if side_code == 1:
            raw_s = False
        elif side_code == -1:
            raw_l = False

        if stop_mode_code == 1:
            sli = lb_i - stop_buffer
            ssi = ub_i + stop_buffer
        elif stop_mode_code == 2:
            sli = rlw - stop_buffer
            ssi = rhg + stop_buffer
        else:
            sli = cl * (1.0 - stop_pct)
            ssi = cl * (1.0 + stop_pct)

        stop_long_all[i] = sli
        stop_short_all[i] = ssi
        rli = cl - sli
        rsi = ssi - cl
        risk_long_all[i] = rli
        risk_short_all[i] = rsi

        cand_li = raw_l and rli > 0.0
        cand_si = raw_s and rsi > 0.0

        if tgt_mode_scalar == 2:
            if cand_li and not (vw_i > cl):
                cand_li = False
            if cand_si and not (vw_i < cl):
                cand_si = False

        cand_long[i] = cand_li
        cand_short[i] = cand_si

    if daily_mode_code == 2:
        final_long, final_short = thin_per_side_per_session_numba(
            cand_long, cand_short, session_id, max_trades_per_day
        )
    else:
        final_long, final_short = thin_first_signal_per_session_numba(
            cand_long, cand_short, session_id, max_trades_per_day
        )

    side_a = np.zeros(n, dtype=np.int8)
    valid_a = np.zeros(n, dtype=np.bool_)
    stop_a = np.zeros(n, dtype=np.float64)
    tgt_prev = np.zeros(n, dtype=np.float64)
    tmode = np.zeros(n, dtype=np.int8)
    tr_a = np.zeros(n, dtype=np.float64)
    risk_a = np.zeros(n, dtype=np.float64)

    TM_FIXED_R = np.int8(1)
    TM_FIXED_PX = np.int8(2)

    for i in range(n):
        if final_long[i]:
            cl = close[i]
            rl = risk_long_all[i]
            side_a[i] = np.int8(1)
            valid_a[i] = True
            stop_a[i] = stop_long_all[i]
            risk_a[i] = rl
            if tgt_mode_scalar == 1:
                tgt_prev[i] = cl + target_r_value * rl
                tmode[i] = TM_FIXED_R
                tr_a[i] = target_r_value
            else:
                tgt_prev[i] = vwap[i]
                tmode[i] = TM_FIXED_PX
                tr_a[i] = 0.0

    for i in range(n):
        if final_short[i] and not final_long[i]:
            cl = close[i]
            rs = risk_short_all[i]
            side_a[i] = np.int8(-1)
            valid_a[i] = True
            stop_a[i] = stop_short_all[i]
            risk_a[i] = rs
            if tgt_mode_scalar == 1:
                tgt_prev[i] = cl - target_r_value * rs
                tmode[i] = TM_FIXED_R
                tr_a[i] = target_r_value
            else:
                tgt_prev[i] = vwap[i]
                tmode[i] = TM_FIXED_PX
                tr_a[i] = 0.0

    return side_a, valid_a, stop_a, tgt_prev, tmode, tr_a, risk_a


def build_vwap_reversal_signal_arrays_fast_from_context(
    ctx: VWAPReversalContext, config: dict[str, Any]
) -> dict[str, np.ndarray]:
    sig_cfg = config.get("signal") or {}
    risk_cfg = config.get("risk") or {}
    _validate_vwap_reversal_config(sig_cfg, risk_cfg)

    ext = float(sig_cfg["extension_band"])
    if ext == 1.0:
        ub = ctx.upper_1
        lb = ctx.lower_1
        pu = ctx.prev_upper_1
        pl = ctx.prev_lower_1
    elif ext == 2.0:
        ub = ctx.upper_2
        lb = ctx.lower_2
        pu = ctx.prev_upper_2
        pl = ctx.prev_lower_2
    else:
        raise ValueError(f"extension_band must be 1.0 or 2.0, got {ext}")

    side = str(sig_cfg.get("side", "both"))
    if side == "long_only":
        side_code = 1
    elif side == "short_only":
        side_code = -1
    else:
        side_code = 0

    confirm = str(sig_cfg.get("confirm_mode", "one_bar_reclaim"))
    if confirm == "one_bar_reclaim":
        ccode = 1
    elif confirm == "close_inside_band":
        ccode = 2
    else:
        ccode = 3

    daily_mode = str(sig_cfg.get("daily_signal_mode", "first_signal"))
    dcode = 2 if daily_mode == "per_side" else 1

    require_slope = 1 if bool(sig_cfg.get("require_vwap_slope_filter", False)) else 0
    slope_mode = str(sig_cfg.get("slope_filter_mode", "none"))
    if slope_mode == "against_trend":
        smode = 1
    elif slope_mode == "flat_or_reverting":
        smode = 2
    else:
        smode = 0

    max_abs = sig_cfg.get("max_abs_vwap_slope")
    if max_abs is not None and not (isinstance(max_abs, float) and math.isnan(max_abs)):
        use_max = 1
        max_abs_f = float(max_abs)
    else:
        use_max = 0
        max_abs_f = 0.0

    min_bw = sig_cfg.get("min_band_width_pct")
    if min_bw is not None and not (isinstance(min_bw, float) and math.isnan(min_bw)):
        use_min_bw = 1
        min_bw_f = float(min_bw)
    else:
        use_min_bw = 0
        min_bw_f = 0.0

    max_bw = sig_cfg.get("max_band_width_pct")
    if max_bw is not None and not (isinstance(max_bw, float) and math.isnan(max_bw)):
        use_max_bw = 1
        max_bw_f = float(max_bw)
    else:
        use_max_bw = 0
        max_bw_f = 0.0

    stop_mode = str(risk_cfg.get("stop_mode", "band_extreme"))
    if stop_mode == "band_extreme":
        stp_c = 1
    elif stop_mode == "recent_swing":
        stp_c = 2
    else:
        stp_c = 3

    target_mode = str(risk_cfg.get("target_mode", "fixed_price"))
    if target_mode == "fixed_r":
        tmc = 1
    else:
        tmc = 2

    side_a, valid_a, stop_a, tgt_prev, tmode, tr_a, risk_a = _build_vwap_reversal_arrays_numba(
        ctx.session_id,
        ctx.minute,
        ctx.high,
        ctx.low,
        ctx.close,
        ctx.vwap,
        ctx.vwap_slope_5,
        ub,
        lb,
        ctx.prev_close,
        ctx.prev_low,
        ctx.prev_high,
        pu,
        pl,
        ctx.rolling_low_swing,
        ctx.rolling_high_swing,
        side_code,
        int(sig_cfg["entry_start_minute"]),
        int(sig_cfg["entry_end_minute"]),
        ccode,
        dcode,
        require_slope,
        smode,
        use_max,
        max_abs_f,
        use_min_bw,
        min_bw_f,
        use_max_bw,
        max_bw_f,
        stp_c,
        float(risk_cfg.get("stop_buffer", 0.0)),
        float(risk_cfg.get("stop_pct", 0.003)),
        tmc,
        float(risk_cfg["target_r"]),
        int(risk_cfg.get("max_trades_per_day", 1)),
    )

    min_rr = get_min_risk_per_share(config)
    valid_a, side_a = apply_min_risk_filter_arrays(valid_a, side_a, risk_a, min_rr)

    return {
        "side": side_a,
        "valid": valid_a,
        "stop": stop_a,
        "target_preview": tgt_prev,
        "target_mode_code": tmode,
        "target_r": tr_a,
        "risk_preview": risk_a,
    }


def _thin_first_n_per_session(
    df: pd.DataFrame,
    raw_mask: pd.Series,
    *,
    max_n: int,
) -> pd.Series:
    keep = pd.Series(False, index=df.index)
    tcol = "ts_utc" if "ts_utc" in df.columns else "ts_ny"
    for sid in df["session_date"].unique():
        sub = df[df["session_date"] == sid].sort_values(tcol)
        taken = 0
        for idx in sub.index:
            if bool(raw_mask.loc[idx]) and taken < max_n:
                keep.loc[idx] = True
                taken += 1
    return keep


def _thin_first_signal_per_session(
    df: pd.DataFrame,
    cand_long: pd.Series,
    cand_short: pd.Series,
    *,
    max_n: int,
) -> tuple[pd.Series, pd.Series]:
    keep_long = pd.Series(False, index=df.index)
    keep_short = pd.Series(False, index=df.index)
    tcol = "ts_utc" if "ts_utc" in df.columns else "ts_ny"
    for sid in df["session_date"].unique():
        sub = df[df["session_date"] == sid].sort_values(tcol)
        picked: list = []
        for idx in sub.index:
            cl = bool(cand_long.loc[idx])
            cs = bool(cand_short.loc[idx])
            if cl and cs:
                picked.append((idx, 1))
            elif cl:
                picked.append((idx, 1))
            elif cs:
                picked.append((idx, -1))
        for idx, sgn in picked[:max_n]:
            if sgn == 1:
                keep_long.loc[idx] = True
            else:
                keep_short.loc[idx] = True
    return keep_long, keep_short


def generate_vwap_reversal_signals(
    df: pd.DataFrame,
    config: dict[str, Any],
    *,
    strategy_name: str = "vwap_reversal",
) -> pd.DataFrame:
    """Shared readable signal generation (used by class and fast array builder)."""
    sig_cfg = config.get("signal") or {}
    risk_cfg = config.get("risk") or {}
    _validate_vwap_reversal_config(sig_cfg, risk_cfg)

    side = str(sig_cfg.get("side", "both"))
    entry_start = int(sig_cfg["entry_start_minute"])
    entry_end = int(sig_cfg["entry_end_minute"])
    ext = float(sig_cfg["extension_band"])
    confirm = str(sig_cfg.get("confirm_mode", "one_bar_reclaim"))
    daily_mode = str(sig_cfg.get("daily_signal_mode", "first_signal"))
    require_slope = bool(sig_cfg.get("require_vwap_slope_filter", False))
    slope_mode = str(sig_cfg.get("slope_filter_mode", "none"))
    max_abs_slope = sig_cfg.get("max_abs_vwap_slope")
    min_bw = sig_cfg.get("min_band_width_pct")
    max_bw = sig_cfg.get("max_band_width_pct")

    stop_mode = str(risk_cfg.get("stop_mode", "band_extreme"))
    stop_buffer = float(risk_cfg.get("stop_buffer", 0.0))
    swing_lb = int(risk_cfg.get("swing_lookback", 5))
    stop_pct = float(risk_cfg.get("stop_pct", 0.003))
    target_mode = str(risk_cfg.get("target_mode", "fixed_price"))
    target_r = float(risk_cfg["target_r"])
    max_trades = int(risk_cfg.get("max_trades_per_day", 1))

    ku, kl = _BAND_COLS[ext]
    need_cols = [
        "session_date",
        "minute_from_open",
        "open",
        "high",
        "low",
        "close",
        "vwap",
        "vwap_slope_5",
        "vwap_std",
        ku,
        kl,
    ]
    miss = [c for c in need_cols if c not in df.columns]
    if miss:
        raise ValueError(f"VWAPReversalStrategy missing feature columns: {miss}")

    if "ts_utc" in df.columns:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
    else:
        work = df.reset_index(drop=True)

    out = init_standard_signal_columns(work, strategy_name=strategy_name, copy=True)

    minute = out["minute_from_open"].astype(np.int32)
    vw = out["vwap"].astype(float)
    ub = out[ku].astype(float)
    lb = out[kl].astype(float)
    close = out["close"].astype(float)
    high = out["high"].astype(float)
    low = out["low"].astype(float)
    slope = out["vwap_slope_5"].astype(float)

    valid_px = vw.notna() & ub.notna() & lb.notna() & close.notna() & (vw.abs() > 1e-12)
    bw_pct = (ub - lb) / vw
    base = (
        valid_px
        & (minute >= entry_start)
        & (minute <= entry_end)
    )
    if min_bw is not None and not (isinstance(min_bw, float) and math.isnan(min_bw)):
        base = base & (bw_pct >= float(min_bw))
    if max_bw is not None and not (isinstance(max_bw, float) and math.isnan(max_bw)):
        base = base & (bw_pct <= float(max_bw))

    g = out.groupby("session_date", sort=False)
    prev_close = g["close"].shift(1)
    prev_low = g["low"].shift(1)
    prev_high = g["high"].shift(1)
    prev_lb = g[kl].shift(1)
    prev_ub = g[ku].shift(1)

    # Slope filter masks (per-row ok for long / short)
    long_slope_ok = pd.Series(True, index=out.index)
    short_slope_ok = pd.Series(True, index=out.index)
    if require_slope and slope_mode != "none":
        if slope_mode == "against_trend":
            long_slope_ok = slope <= 0
            short_slope_ok = slope >= 0
        elif slope_mode == "flat_or_reverting":
            if max_abs_slope is not None and not (
                isinstance(max_abs_slope, float) and math.isnan(max_abs_slope)
            ):
                mx = float(max_abs_slope)
                long_slope_ok = slope <= mx
                short_slope_ok = slope >= -mx

    allow_long = side in ("long_only", "both")
    allow_short = side in ("short_only", "both")

    # Confirmation masks
    if confirm == "one_bar_reclaim":
        raw_long = base & long_slope_ok & (prev_close <= prev_lb) & (close > lb) & pd.notna(prev_close)
        raw_short = base & short_slope_ok & (prev_close >= prev_ub) & (close < ub) & pd.notna(prev_close)
    elif confirm == "close_inside_band":
        raw_long = base & long_slope_ok & (low <= lb) & (close > lb)
        raw_short = base & short_slope_ok & (high >= ub) & (close < ub)
    else:  # momentum_turn
        raw_long = (
            base
            & long_slope_ok
            & (close > prev_close)
            & pd.notna(prev_close)
            & ((prev_close <= prev_lb) | (prev_low <= prev_lb))
        )
        raw_short = (
            base
            & short_slope_ok
            & (close < prev_close)
            & pd.notna(prev_close)
            & ((prev_close >= prev_ub) | (prev_high >= prev_ub))
        )

    if not allow_long:
        raw_long = pd.Series(False, index=out.index)
    if not allow_short:
        raw_short = pd.Series(False, index=out.index)

    # Stops
    roll_min = g["low"].transform(lambda s: s.rolling(swing_lb, min_periods=1).min())
    roll_max = g["high"].transform(lambda s: s.rolling(swing_lb, min_periods=1).max())

    if stop_mode == "band_extreme":
        stop_long_s = lb - stop_buffer
        stop_short_s = ub + stop_buffer
    elif stop_mode == "recent_swing":
        stop_long_s = roll_min - stop_buffer
        stop_short_s = roll_max + stop_buffer
    else:
        stop_long_s = close * (1.0 - stop_pct)
        stop_short_s = close * (1.0 + stop_pct)

    risk_long = close - stop_long_s
    risk_short = stop_short_s - close

    cand_long = raw_long.fillna(False) & (risk_long > 0)
    cand_short = raw_short.fillna(False) & (risk_short > 0)

    # Target validity for fixed_price @ VWAP
    if target_mode == "fixed_price":
        cand_long = cand_long & (vw > close)
        cand_short = cand_short & (vw < close)

    out["vwap_rev_band_width_pct"] = bw_pct
    out["vwap_rev_raw_long"] = raw_long.fillna(False)
    out["vwap_rev_raw_short"] = raw_short.fillna(False)
    out["vwap_rev_candidate_long"] = cand_long
    out["vwap_rev_candidate_short"] = cand_short

    if daily_mode == "per_side":
        keep_l = _thin_first_n_per_session(out, cand_long, max_n=max_trades)
        keep_s = _thin_first_n_per_session(out, cand_short, max_n=max_trades)
        final_long = cand_long & keep_l
        final_short = cand_short & keep_s
    else:
        kl2, ks2 = _thin_first_signal_per_session(out, cand_long, cand_short, max_n=max_trades)
        final_long = cand_long & kl2
        final_short = cand_short & ks2

    short_ix = final_short & ~final_long

    if target_mode == "fixed_r":
        tgt_long = close + target_r * risk_long
        tgt_short = close - target_r * risk_short
        long_ix = final_long
        out.loc[long_ix, "sig_side"] = 1
        out.loc[long_ix, "sig_entry_ref"] = close[long_ix]
        out.loc[long_ix, "sig_stop"] = stop_long_s[long_ix]
        out.loc[long_ix, "sig_target_mode"] = "fixed_r"
        out.loc[long_ix, "sig_target_r"] = target_r
        out.loc[long_ix, "sig_target"] = tgt_long[long_ix]
        out.loc[long_ix, "sig_risk_per_share"] = risk_long[long_ix]
        out.loc[long_ix, "sig_reason"] = "vwap_rev_long"
        out.loc[long_ix, "sig_valid"] = True

        out.loc[short_ix, "sig_side"] = -1
        out.loc[short_ix, "sig_entry_ref"] = close[short_ix]
        out.loc[short_ix, "sig_stop"] = stop_short_s[short_ix]
        out.loc[short_ix, "sig_target_mode"] = "fixed_r"
        out.loc[short_ix, "sig_target_r"] = target_r
        out.loc[short_ix, "sig_target"] = tgt_short[short_ix]
        out.loc[short_ix, "sig_risk_per_share"] = risk_short[short_ix]
        out.loc[short_ix, "sig_reason"] = "vwap_rev_short"
        out.loc[short_ix, "sig_valid"] = True
    else:
        # fixed_price -> VWAP
        long_ix = final_long
        out.loc[long_ix, "sig_side"] = 1
        out.loc[long_ix, "sig_entry_ref"] = close[long_ix]
        out.loc[long_ix, "sig_stop"] = stop_long_s[long_ix]
        out.loc[long_ix, "sig_target_mode"] = "fixed_price"
        out.loc[long_ix, "sig_target_r"] = pd.NA
        out.loc[long_ix, "sig_target"] = vw[long_ix]
        out.loc[long_ix, "sig_risk_per_share"] = risk_long[long_ix]
        out.loc[long_ix, "sig_reason"] = "vwap_rev_long"
        out.loc[long_ix, "sig_valid"] = True

        out.loc[short_ix, "sig_side"] = -1
        out.loc[short_ix, "sig_entry_ref"] = close[short_ix]
        out.loc[short_ix, "sig_stop"] = stop_short_s[short_ix]
        out.loc[short_ix, "sig_target_mode"] = "fixed_price"
        out.loc[short_ix, "sig_target_r"] = pd.NA
        out.loc[short_ix, "sig_target"] = vw[short_ix]
        out.loc[short_ix, "sig_risk_per_share"] = risk_short[short_ix]
        out.loc[short_ix, "sig_reason"] = "vwap_rev_short"
        out.loc[short_ix, "sig_valid"] = True

    return apply_min_risk_filter_df(out, config=config)


class VWAPReversalStrategy(BaseStrategy):
    name = "vwap_reversal"
    supports_fast = True
    performance_tier = "A_true_context_fast_core"

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        risk = config.get("risk") or {}
        return (int(risk.get("swing_lookback", 5)),)

    def normalized_param_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        feat = config.get("features") or {}
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        bt = config.get("backtest") or {}

        def nz(x: Any) -> Any:
            if isinstance(x, float) and math.isnan(x):
                return None
            return x

        req_sl = bool(sig.get("require_vwap_slope_filter", False))
        parts: list[Any] = [
            int(feat.get("orb_open_minutes", 15)),
            str(sig.get("side", "both")),
            int(sig["entry_start_minute"]),
            int(sig["entry_end_minute"]),
            float(sig.get("extension_band", 2.0)),
            str(sig.get("confirm_mode", "one_bar_reclaim")),
            str(sig.get("daily_signal_mode", "first_signal")),
            req_sl,
        ]
        if req_sl:
            parts.append(str(sig.get("slope_filter_mode", "none")))
            parts.append(nz(sig.get("max_abs_vwap_slope")))
        parts.append(nz(sig.get("min_band_width_pct")))
        parts.append(nz(sig.get("max_band_width_pct")))
        parts.append(str(risk.get("stop_mode", "band_extreme")))
        parts.append(float(risk.get("stop_buffer", 0.0)))
        parts.append(int(risk.get("swing_lookback", 5)))
        sm = str(risk.get("stop_mode", "band_extreme"))
        if sm == "fixed_pct":
            parts.append(float(risk.get("stop_pct", 0.003)))
        tm = str(risk.get("target_mode", "fixed_price"))
        parts.append(tm)
        if tm == "fixed_r":
            parts.append(float(risk["target_r"]))
        if tm == "fixed_price":
            parts.append(str(risk.get("target_ref", "vwap")))
        parts.append(int(risk.get("max_trades_per_day", 1)))
        parts.extend(
            [
                int(bt.get("eod_exit_minute", 389)),
                float(bt.get("quantity", 1.0)),
                float(bt.get("commission_per_trade", 0.0)),
                float(bt.get("slippage_per_share", 0.0)),
                bool(bt.get("recompute_target_from_entry", True)),
                nz(bt.get("max_hold_minutes")),
                float(risk.get("min_risk_per_share") or 0.0),
            ]
        )
        return tuple(parts)

    def required_features(self) -> list[str]:
        return [
            "session_date",
            "minute_from_open",
            "open",
            "high",
            "low",
            "close",
            "vwap",
            "vwap_slope_5",
            "vwap_std",
            "vwap_upper_1.0",
            "vwap_lower_1.0",
            "vwap_upper_2.0",
            "vwap_lower_2.0",
        ]

    def validate_config(self, config: dict[str, Any]) -> None:
        from src.utils.config_validation import validate_common_strategy_config

        validate_common_strategy_config(config)
        _validate_vwap_reversal_config(config.get("signal") or {}, config.get("risk") or {})

    def generate_signals(self, df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
        out = generate_vwap_reversal_signals(df, config, strategy_name=self.name)
        validate_standard_signal_columns(out)
        return out

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> VWAPReversalContext:
        return prepare_vwap_reversal_context(df, config)

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if isinstance(ctx, pd.DataFrame):
            return super().generate_signal_arrays_from_context(ctx, config)
        if not isinstance(ctx, VWAPReversalContext):
            raise TypeError(f"expected VWAPReversalContext or DataFrame, got {type(ctx)}")
        return build_vwap_reversal_signal_arrays_fast_from_context(ctx, config)

    def generate_signal_arrays(self, df: pd.DataFrame, config: dict[str, Any]) -> dict[str, Any]:
        return self.generate_signal_arrays_from_context(self.prepare_signal_context(df, config), config)


def build_vwap_reversal_signal_arrays_fast(df: pd.DataFrame, config: dict[str, Any]) -> dict[str, np.ndarray]:
    s = VWAPReversalStrategy()
    return s.generate_signal_arrays(df, config)


def main(argv: list[str] | None = None) -> int:
    from src.strategies.loader import load_strategy_config

    p = argparse.ArgumentParser(description="VWAP reversal signal smoke test.")
    p.add_argument("--asset", choices=["equity", "futures"], required=True)
    p.add_argument("--symbol", required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--data-dir", default="data/raw/ibkr")
    args = p.parse_args(argv)

    cfg = load_strategy_config("vwap_reversal")
    feat_cfg = cfg.get("features") or {}
    raw = read_bars(
        asset=args.asset,
        symbol=args.symbol.upper().strip(),
        start=args.start,
        end=args.end,
        data_dir=args.data_dir,
    )
    if len(raw) == 0:
        print("ERROR empty bars", file=sys.stderr)
        return 1

    orb_m = int(feat_cfg.get("orb_open_minutes", 15))
    vb = tuple(feat_cfg.get("vwap_bands") or (1.0, 2.0))
    vw = tuple(feat_cfg.get("vol_windows") or (5, 15, 30))
    feat = build_basic_features(
        raw,
        orb_open_minutes=orb_m,
        vwap_bands=vb,
        vol_windows=vw,
        copy=True,
        allow_overwrite=False,
    )

    strat = VWAPReversalStrategy()
    out = strat.generate_signals(feat, cfg)

    v = out["sig_valid"].fillna(False)
    s = out["sig_side"].fillna(0)
    print(f"rows={len(out)}", flush=True)
    print(f"nonzero_signals={int((v & (s != 0)).sum())}", flush=True)
    print(f"long_signals={int((v & (s == 1)).sum())}", flush=True)
    print(f"short_signals={int((v & (s == -1)).sum())}", flush=True)
    print(f"sessions={out['session_date'].nunique()}", flush=True)
    print(f"sessions_with_signals={out.groupby('session_date')['sig_valid'].any().sum()}", flush=True)
    show = out[v][
        [
            "ts_ny",
            "session_date",
            "minute_from_open",
            "close",
            "vwap",
            "sig_side",
            "sig_stop",
            "sig_target",
            "sig_target_mode",
            "sig_target_r",
            "sig_risk_per_share",
            "sig_reason",
            "sig_valid",
        ]
    ].head(15)
    print("sample:", flush=True)
    print(show.to_string(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
