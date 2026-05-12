"""Prior-day level trap — true Numba fast core."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numba import njit

from src.execution.types import TM_FIXED_PX, TM_FIXED_R, TM_NONE
from src.strategies.strategy._atr_helpers import atr_series
from src.strategies.strategy.base import BaseStrategy, init_standard_signal_columns
from src.utils.config_validation import (
    validate_common_strategy_config,
    validate_int_at_least,
    validate_long_only_mvp,
    validate_minute_range,
    validate_nonnegative_number,
    validate_positive_number,
)
from src.strategies.strategy.fast_utils import (
    apply_min_risk_filter_df,
    apply_min_risk_filter_numba_kernel,
    get_min_risk_per_share,
    past_any_bool_in_prior_fw_session,
    rolling_min_by_session,
    session_id_from_dates,
    thin_first_signal_per_session_numba,
)


@dataclass(frozen=True)
class PriorDayTrapContext:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    low: np.ndarray
    close: np.ndarray
    prior_day_low: np.ndarray
    prior_day_close: np.ndarray
    vwap: np.ndarray
    close_location: np.ndarray
    prev_high: np.ndarray
    prev_close: np.ndarray
    volume_ratio_20: np.ndarray
    atr: np.ndarray
    pierce: np.ndarray
    past_pierce: np.ndarray
    roll_lo: np.ndarray


@njit(cache=True)
def _pdl_trap_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    close: np.ndarray,
    low: np.ndarray,
    lv: np.ndarray,
    pdc: np.ndarray,
    vw: np.ndarray,
    cloc: np.ndarray,
    ph: np.ndarray,
    pc: np.ndarray,
    volr: np.ndarray,
    atr: np.ndarray,
    past_pi: np.ndarray,
    roll_lo: np.ndarray,
    es: int,
    ee: int,
    confirm: int,
    min_cl: float,
    req_va: int,
    req_vs: int,
    min_vm: float,
    stop_mode: int,
    atr_buf: float,
    tgt_mode: int,
    target_r: float,
    buf_lv: float,
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
        if minute[i] < es or minute[i] > ee:
            continue
        if not past_pi[i]:
            continue
        if close[i] <= lv[i]:
            continue
        if req_va != 0 and close[i] <= vw[i]:
            continue
        if req_vs != 0 and volr[i] < min_vm:
            continue
        ok = True
        if confirm == 1:
            ok = (low[i] < lv[i]) and (cloc[i] >= min_cl)
        elif confirm == 2:
            ok = (close[i] > ph[i]) or (close[i] > pc[i])
        if not ok:
            continue
        cand_long[i] = True
    fl, fs = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)
    for i in range(n):
        if not fl[i]:
            continue
        sl = roll_lo[i]
        if stop_mode != 0:
            sl = sl - atr_buf * atr[i]
        risk_l = close[i] - sl
        if risk_l <= 0:
            continue
        side[i] = 1
        valid[i] = True
        stp[i] = sl
        rsk[i] = risk_l
        if tgt_mode == 0:
            tgtp[i] = close[i] + target_r * risk_l
            tmc[i] = TM_FIXED_R
            tr[i] = target_r
        elif tgt_mode == 1:
            tgtp[i] = vw[i]
            tmc[i] = TM_FIXED_PX
        else:
            tgtp[i] = pdc[i]
            tmc[i] = TM_FIXED_PX
    apply_min_risk_filter_numba_kernel(valid, side, rsk, min_risk)
    return side, valid, stp, tgtp, tmc, tr, rsk


class PriorDayLevelTrapStrategy(BaseStrategy):
    """Prior-day low long trap MVP (no prior-day-high short path)."""

    name = "prior_day_level_trap"
    supports_fast = True
    performance_tier = "A_true_context_fast_core"

    def validate_config(self, config: dict[str, Any]) -> None:
        validate_common_strategy_config(config)
        validate_long_only_mvp(config, strategy_name=self.name)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        lt = str(sig.get("level_type", "prior_day_low"))
        if lt != "prior_day_low":
            raise ValueError(
                f"{self.name}: only level_type='prior_day_low' is implemented, got {lt!r}"
            )
        validate_minute_range(
            "signal.entry_start_minute",
            sig.get("entry_start_minute"),
            "signal.entry_end_minute",
            sig.get("entry_end_minute"),
        )
        validate_int_at_least("signal.fail_window_bars", sig.get("fail_window_bars", 5), 1)
        validate_nonnegative_number("signal.level_buffer_atr", sig.get("level_buffer_atr", 0.1))
        confirm = str(sig.get("confirm_mode", "close_reclaim"))
        if confirm not in ("close_reclaim", "wick_reclaim", "momentum_turn"):
            raise ValueError(f"signal.confirm_mode invalid: {confirm!r}")
        stop_mode = str(risk.get("stop_mode", "failed_extreme"))
        if stop_mode not in ("failed_extreme", "swing_buffered"):
            raise ValueError(f"risk.stop_mode invalid: {stop_mode!r}")
        target_mode = str(risk.get("target_mode", "fixed_r"))
        if target_mode not in ("fixed_r", "vwap", "prior_day_close"):
            raise ValueError(f"risk.target_mode invalid: {target_mode!r}")
        if target_mode == "fixed_r":
            validate_positive_number("risk.target_r", risk.get("target_r", 1.0))
        validate_nonnegative_number("risk.atr_buffer", risk.get("atr_buffer", 0.1))
        validate_int_at_least("risk.max_trades_per_day", risk.get("max_trades_per_day", 1), 1)
        ac = str(sig.get("atr_column", "atr_like_15") or "").strip()
        if not ac:
            raise ValueError("signal.atr_column must be a non-empty string when set")

    def required_features(self) -> list[str]:
        return [
            "session_date",
            "minute_from_open",
            "high",
            "low",
            "close",
            "prior_day_low",
            "vwap",
            "prior_day_close",
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
        buf = float(sig.get("level_buffer_atr", 0.1))
        atr_col = str(sig.get("atr_column", "atr_like_15"))
        return ("pdl_ctx", fw, ww, buf, atr_col)

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> PriorDayTrapContext:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        sig = config.get("signal") or {}
        fw = int(sig.get("fail_window_bars", 5))
        ww = max(fw * 3, 5)
        buf_lv = float(sig.get("level_buffer_atr", 0.1))
        session_id = session_id_from_dates(work["session_date"])
        low = work["low"].to_numpy(dtype=np.float64)
        atr = atr_series(work, config).to_numpy(dtype=np.float64)
        lv = work["prior_day_low"].to_numpy(dtype=np.float64)
        pierce = low < (lv - buf_lv * atr)
        past_pi = past_any_bool_in_prior_fw_session(pierce, session_id, fw)
        roll_lo = rolling_min_by_session(low, session_id, ww)
        return PriorDayTrapContext(
            n=len(work),
            session_id=session_id,
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            low=low,
            close=work["close"].to_numpy(dtype=np.float64),
            prior_day_low=lv,
            prior_day_close=work["prior_day_close"].to_numpy(dtype=np.float64),
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            close_location=work["close_location"].to_numpy(dtype=np.float64),
            prev_high=work["prev_high_by_session"].to_numpy(dtype=np.float64),
            prev_close=work["prev_close_by_session"].to_numpy(dtype=np.float64),
            volume_ratio_20=work["volume_ratio_20"].to_numpy(dtype=np.float64),
            atr=atr,
            pierce=pierce.astype(np.float64),
            past_pierce=past_pi.astype(np.float64),
            roll_lo=roll_lo,
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, PriorDayTrapContext):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es = int(sig["entry_start_minute"])
        ee = int(sig["entry_end_minute"])
        confirm = str(sig.get("confirm_mode", "close_reclaim"))
        min_cl = float(sig.get("min_close_location", 0.55))
        req_va = int(bool(sig.get("require_vwap_alignment", False)))
        req_vs = int(bool(sig.get("require_volume_surge", False)))
        min_vm = float(sig.get("min_volume_mult", 1.5))
        stop_mode = str(risk.get("stop_mode", "failed_extreme"))
        atr_buf = float(risk.get("atr_buffer", 0.1))
        target_mode = str(risk.get("target_mode", "fixed_r"))
        target_r = float(risk.get("target_r", 1.0))
        max_tr = int(risk.get("max_trades_per_day", 1))
        min_risk = get_min_risk_per_share(config)
        buf_lv = float(sig.get("level_buffer_atr", 0.1))
        cmap = {"close_reclaim": 0, "wick_reclaim": 1, "momentum_turn": 2}
        ci = cmap.get(confirm, 0)
        sm = 0 if stop_mode == "failed_extreme" else 1
        if target_mode == "fixed_r":
            tm = 0
        elif target_mode == "vwap":
            tm = 1
        else:
            tm = 2
        side, valid, stp, tgtp, tmc, tr, rsk = _pdl_trap_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.close,
            ctx.low,
            ctx.prior_day_low,
            ctx.prior_day_close,
            ctx.vwap,
            ctx.close_location,
            ctx.prev_high,
            ctx.prev_close,
            ctx.volume_ratio_20,
            ctx.atr,
            ctx.past_pierce,
            ctx.roll_lo,
            es,
            ee,
            ci,
            min_cl,
            req_va,
            req_vs,
            min_vm,
            sm,
            atr_buf,
            tm,
            target_r,
            buf_lv,
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
        return self.generate_signal_arrays_from_context(self.prepare_signal_context(df, config), config)

    def generate_signals(self, df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        arr = self.generate_signal_arrays_from_context(self.prepare_signal_context(df, config), config)
        out = init_standard_signal_columns(work, strategy_name=self.name, copy=True)
        out["sig_side"] = arr["side"]
        out["sig_valid"] = arr["valid"]
        out["sig_stop"] = arr["stop"]
        out["sig_target"] = arr["target_preview"]
        out["sig_target_mode"] = np.where(arr["target_mode_code"] == TM_FIXED_R, "fixed_r", "fixed_price")
        out["sig_target_r"] = arr["target_r"]
        out["sig_risk_per_share"] = arr["risk_preview"]
        out.loc[out["sig_valid"], "sig_reason"] = "pdl_trap_long"
        return apply_min_risk_filter_df(out, config=config)

    def normalized_param_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        bt = config.get("backtest") or {}

        def nz(x: Any) -> Any:
            if isinstance(x, float) and math.isnan(x):
                return None
            return x

        tm = str(risk.get("target_mode", "fixed_r"))
        parts: list[Any] = [
            str(sig.get("level_type", "prior_day_low")),
            str(sig.get("atr_column", "atr_like_15")),
            int(sig["entry_start_minute"]),
            int(sig["entry_end_minute"]),
            int(sig.get("fail_window_bars", 5)),
            float(sig.get("level_buffer_atr", 0.1)),
            str(sig.get("confirm_mode", "close_reclaim")),
            bool(sig.get("require_vwap_alignment", False)),
            str(risk.get("stop_mode", "failed_extreme")),
            tm,
        ]
        if tm == "fixed_r":
            parts.append(float(risk.get("target_r", 1.0)))
        parts.extend([float(risk.get("min_risk_per_share") or 0.0), nz(bt.get("max_hold_minutes"))])
        return tuple(parts)
