"""Failed opening-range breakout (long/short) — true Numba fast core."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numba import njit

from src.backtest.fast import TM_FIXED_PX, TM_FIXED_R, TM_NONE
from src.strategies.strategy._atr_helpers import atr_series
from src.strategies.strategy.base import BaseStrategy, init_standard_signal_columns
from src.strategies.strategy.fast_utils import (
    apply_min_risk_filter_df,
    apply_min_risk_filter_numba_kernel,
    get_min_risk_per_share,
    past_any_bool_in_prior_fw_session,
    rolling_max_by_session,
    rolling_min_by_session,
    session_id_from_dates,
    thin_first_signal_per_session_numba,
)


@dataclass(frozen=True)
class FailedOrbContext:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    after_orb: np.ndarray
    low: np.ndarray
    high: np.ndarray
    close: np.ndarray
    orb_low: np.ndarray
    orb_high: np.ndarray
    orb_mid: np.ndarray
    vwap: np.ndarray
    close_location: np.ndarray
    prev_high: np.ndarray
    prev_close: np.ndarray
    volume_ratio_20: np.ndarray
    atr: np.ndarray
    past_break_below: np.ndarray
    past_break_above: np.ndarray
    roll_lo: np.ndarray
    roll_hi: np.ndarray


@njit(cache=True)
def _failed_orb_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    after_orb: np.ndarray,
    low: np.ndarray,
    high: np.ndarray,
    close: np.ndarray,
    ol: np.ndarray,
    oh: np.ndarray,
    om: np.ndarray,
    vw: np.ndarray,
    cloc: np.ndarray,
    ph: np.ndarray,
    pc: np.ndarray,
    volr: np.ndarray,
    atr: np.ndarray,
    past_bl: np.ndarray,
    past_bh: np.ndarray,
    roll_lo: np.ndarray,
    roll_hi: np.ndarray,
    es: int,
    ee: int,
    fw: int,
    confirm: int,
    min_cl: float,
    req_vw: int,
    req_vc: int,
    min_vm: float,
    stop_mode: int,
    atr_buf: float,
    tgt_mode: int,
    target_r: float,
    allow_long: int,
    allow_short: int,
    max_tr: int,
    min_risk: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    side = np.zeros(n, dtype=np.int8)
    valid = np.zeros(n, dtype=np.bool_)
    stp = np.zeros(n, dtype=np.float64)
    tgtp = np.zeros(n, dtype=np.float64)
    tmc = np.full(n, TM_NONE, dtype=np.int8)
    tr = np.zeros(n, dtype=np.float64)
    rsk = np.zeros(n, dtype=np.float64)

    cand_long = np.zeros(n, dtype=np.bool_)
    cand_short = np.zeros(n, dtype=np.bool_)

    for i in range(n):
        ab = bool(after_orb[i]) and es <= minute[i] <= ee
        broke_below = low[i] < ol[i]
        broke_above = high[i] > oh[i]
        reclaim_l = close[i] > ol[i]
        reclaim_s = close[i] < oh[i]

        m = ab and past_bl[i] and reclaim_l
        if req_vw != 0:
            m = m and (close[i] > vw[i])
        if req_vc != 0:
            m = m and (volr[i] >= min_vm)
        if confirm == 1:
            m = m and (low[i] < ol[i]) and (cloc[i] >= min_cl)
        elif confirm == 2:
            m = m and ((close[i] > ph[i]) or (close[i] > pc[i]))

        ms = ab and past_bh[i] and reclaim_s
        if req_vw != 0:
            ms = ms and (close[i] < vw[i])
        if req_vc != 0:
            ms = ms and (volr[i] >= min_vm)
        if confirm == 1:
            ms = ms and (high[i] > oh[i]) and ((1.0 - cloc[i]) >= min_cl)
        elif confirm == 2:
            ms = ms and ((close[i] < ph[i]) or (close[i] < pc[i]))

        cand_long[i] = m and allow_long != 0
        cand_short[i] = ms and allow_short != 0

        sl_l = roll_lo[i]
        ss = roll_hi[i]
        if stop_mode == 1:
            sl_l = sl_l - atr_buf * atr[i]
            ss = ss + atr_buf * atr[i]

        risk_l = close[i] - sl_l
        risk_s = ss - close[i]
        if cand_long[i] and risk_l <= 0:
            cand_long[i] = False
        if cand_short[i] and risk_s <= 0:
            cand_short[i] = False

    fl, fs = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)

    for i in range(n):
        if not fl[i] and not fs[i]:
            continue
        take_short = fs[i] and not fl[i]
        if take_short:
            ss = roll_hi[i]
            if stop_mode == 1:
                ss = ss + atr_buf * atr[i]
            risk_s = ss - close[i]
            side[i] = -1
            valid[i] = True
            stp[i] = ss
            rsk[i] = risk_s
            if tgt_mode == 0:
                tgtp[i] = close[i] - target_r * risk_s
                tmc[i] = TM_FIXED_R
                tr[i] = target_r
            elif tgt_mode == 1:
                tgtp[i] = om[i]
                tmc[i] = TM_FIXED_PX
            else:
                tgtp[i] = vw[i]
                tmc[i] = TM_FIXED_PX
        else:
            sl_l = roll_lo[i]
            if stop_mode == 1:
                sl_l = sl_l - atr_buf * atr[i]
            risk_l = close[i] - sl_l
            side[i] = 1
            valid[i] = True
            stp[i] = sl_l
            rsk[i] = risk_l
            if tgt_mode == 0:
                tgtp[i] = close[i] + target_r * risk_l
                tmc[i] = TM_FIXED_R
                tr[i] = target_r
            elif tgt_mode == 1:
                tgtp[i] = om[i]
                tmc[i] = TM_FIXED_PX
            else:
                tgtp[i] = vw[i]
                tmc[i] = TM_FIXED_PX

    apply_min_risk_filter_numba_kernel(valid, side, rsk, min_risk)
    return side, valid, stp, tgtp, tmc, tr, rsk


class FailedOrbStrategy(BaseStrategy):
    name = "failed_orb"
    supports_fast = True
    performance_tier = "A_true_context_fast_core"

    def required_features(self) -> list[str]:
        return [
            "session_date",
            "minute_from_open",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "after_orb",
            "orb_high",
            "orb_low",
            "orb_mid",
            "vwap",
            "close_location",
            "prev_high_by_session",
            "prev_close_by_session",
            "volume_ratio_20",
            "atr_like_15",
        ]

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        sig = config.get("signal") or {}
        fw = int(sig.get("fail_window_bars", 5))
        ww = max(fw * 3, 5)
        return ("failed_orb_ctx", fw, ww)

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> FailedOrbContext:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        sig = config.get("signal") or {}
        fw = int(sig.get("fail_window_bars", 5))
        ww = max(fw * 3, 5)

        session_id = session_id_from_dates(work["session_date"])
        low = work["low"].to_numpy(dtype=np.float64)
        high = work["high"].to_numpy(dtype=np.float64)
        broke_below = low < work["orb_low"].to_numpy(dtype=np.float64)
        broke_above = high > work["orb_high"].to_numpy(dtype=np.float64)
        past_bl = past_any_bool_in_prior_fw_session(broke_below, session_id, fw)
        past_bh = past_any_bool_in_prior_fw_session(broke_above, session_id, fw)
        roll_lo = rolling_min_by_session(low, session_id, ww)
        roll_hi = rolling_max_by_session(high, session_id, ww)
        atr = atr_series(work, config).to_numpy(dtype=np.float64)

        return FailedOrbContext(
            n=len(work),
            session_id=session_id,
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            after_orb=work["after_orb"].astype(bool).to_numpy(),
            low=low,
            high=high,
            close=work["close"].to_numpy(dtype=np.float64),
            orb_low=work["orb_low"].to_numpy(dtype=np.float64),
            orb_high=work["orb_high"].to_numpy(dtype=np.float64),
            orb_mid=work["orb_mid"].to_numpy(dtype=np.float64),
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            close_location=work["close_location"].to_numpy(dtype=np.float64),
            prev_high=work["prev_high_by_session"].to_numpy(dtype=np.float64),
            prev_close=work["prev_close_by_session"].to_numpy(dtype=np.float64),
            volume_ratio_20=work["volume_ratio_20"].to_numpy(dtype=np.float64),
            atr=atr,
            past_break_below=past_bl,
            past_break_above=past_bh,
            roll_lo=roll_lo,
            roll_hi=roll_hi,
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, FailedOrbContext):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        side_s = str(sig.get("side", "long_only"))
        es = int(sig["entry_start_minute"])
        ee = int(sig["entry_end_minute"])
        fw = int(sig.get("fail_window_bars", 5))
        confirm = str(sig.get("confirm_mode", "close_reclaim"))
        min_cl = float(sig.get("min_close_location", 0.55))
        req_vw = bool(sig.get("require_vwap_reclaim", False))
        req_vc = bool(sig.get("require_volume_climax", False))
        min_vm = float(sig.get("min_volume_mult", 1.5))
        stop_mode = str(risk.get("stop_mode", "failed_extreme"))
        atr_buf = float(risk.get("atr_buffer", 0.1))
        target_mode = str(risk.get("target_mode", "fixed_r"))
        target_r = float(risk.get("target_r", 1.0))
        max_tr = int(risk.get("max_trades_per_day", 1))
        min_risk = get_min_risk_per_share(config)

        cmap = {"close_reclaim": 0, "wick_reclaim": 1, "momentum_turn": 2}
        ci = cmap.get(confirm, 0)
        sm = 0 if stop_mode == "failed_extreme" else 1
        tm = {"fixed_r": 0, "orb_mid": 1, "vwap": 2}.get(target_mode, 0)
        al = 1 if side_s in ("long_only", "both") else 0
        ash = 1 if side_s in ("short_only", "both") else 0

        side, valid, stp, tgtp, tmc, tr, rsk = _failed_orb_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.after_orb.astype(np.float64),
            ctx.low,
            ctx.high,
            ctx.close,
            ctx.orb_low,
            ctx.orb_high,
            ctx.orb_mid,
            ctx.vwap,
            ctx.close_location,
            ctx.prev_high,
            ctx.prev_close,
            ctx.volume_ratio_20,
            ctx.atr,
            ctx.past_break_below.astype(np.float64),
            ctx.past_break_above.astype(np.float64),
            ctx.roll_lo,
            ctx.roll_hi,
            es,
            ee,
            fw,
            ci,
            min_cl,
            int(req_vw),
            int(req_vc),
            min_vm,
            sm,
            atr_buf,
            tm,
            target_r,
            al,
            ash,
            max_tr,
            float(min_risk),
        )
        return {
            "side": side,
            "valid": valid,
            "stop": stp,
            "target_preview": tgtp,
            "target_mode_code": tmc,
            "target_r": tr,
            "risk_preview": rsk,
        }

    def generate_signal_arrays(self, df: pd.DataFrame, config: dict[str, Any]) -> dict[str, Any]:
        ctx = self.prepare_signal_context(df, config)
        return self.generate_signal_arrays_from_context(ctx, config)

    def generate_signals(self, df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
        ctx = self.prepare_signal_context(df, config)
        arrays = self.generate_signal_arrays_from_context(ctx, config)
        tmp = pd.DataFrame({"__i": np.arange(ctx.n)})
        tmp["sig_side"] = arrays["side"]
        tmp["sig_valid"] = arrays["valid"]
        tmp["sig_stop"] = arrays["stop"]
        tmp["sig_target"] = arrays["target_preview"]
        tmp["sig_target_r"] = arrays["target_r"]
        tmp["sig_risk_per_share"] = arrays["risk_preview"]
        tmc = arrays["target_mode_code"]
        tmp["sig_target_mode"] = np.where(tmc == TM_FIXED_R, "fixed_r", np.where(tmc == TM_FIXED_PX, "fixed_price", ""))
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        out = init_standard_signal_columns(work, strategy_name=self.name, copy=True)
        for c in tmp.columns:
            if c != "__i":
                out[c] = tmp[c].values
        out.loc[out["sig_side"] == 1, "sig_reason"] = "failed_orb_long"
        out.loc[out["sig_side"] == -1, "sig_reason"] = "failed_orb_short"
        return apply_min_risk_filter_df(out, config=config)

    def normalized_param_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        feat = config.get("features") or {}
        bt = config.get("backtest") or {}

        def nz(x: Any) -> Any:
            if isinstance(x, float) and math.isnan(x):
                return None
            return x

        tm = str(risk.get("target_mode", "fixed_r"))
        parts: list[Any] = [
            int(feat.get("orb_open_minutes", 15)),
            str(sig.get("side", "long_only")),
            int(sig["entry_start_minute"]),
            int(sig["entry_end_minute"]),
            int(sig.get("fail_window_bars", 5)),
            str(sig.get("confirm_mode", "close_reclaim")),
            bool(sig.get("require_vwap_reclaim", False)),
            bool(sig.get("require_volume_climax", False)),
            float(sig.get("min_close_location", 0.55)),
            str(risk.get("stop_mode", "failed_extreme")),
            float(risk.get("atr_buffer", 0.1)),
            tm,
        ]
        if tm == "fixed_r":
            parts.append(float(risk.get("target_r", 1.0)))
        parts.extend(
            [
                float(risk.get("min_risk_per_share") or 0.0),
                int(risk.get("max_trades_per_day", 1)),
                nz(bt.get("max_hold_minutes")),
            ]
        )
        return tuple(parts)
