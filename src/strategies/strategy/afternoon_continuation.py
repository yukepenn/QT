"""Afternoon continuation — true Numba fast core."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numba import njit

from src.backtest.fast import TM_FIXED_R, TM_NONE
from src.strategies.strategy._atr_helpers import atr_series
from src.strategies.strategy.base import BaseStrategy, init_standard_signal_columns
from src.utils.config_validation import (
    has_nested,
    validate_common_strategy_config,
    validate_int_at_least,
    validate_long_only_mvp,
    validate_minute_range,
    validate_minute_value,
    validate_nonnegative_number,
    validate_positive_number,
)
from src.strategies.strategy.fast_utils import (
    apply_min_risk_filter_df,
    apply_min_risk_filter_numba_kernel,
    first_value_when_minute_ge_with_known,
    get_min_risk_per_share,
    session_id_from_dates,
    thin_first_signal_per_session_numba,
)


@dataclass(frozen=True)
class AfternoonContext:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    session_open: np.ndarray
    vwap: np.ndarray
    hi60: np.ndarray
    lo60: np.ndarray
    pers60: np.ndarray
    volr: np.ndarray
    atr: np.ndarray
    mor_close: np.ndarray
    mor_close_known: np.ndarray


@njit(cache=True)
def _afternoon_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    close: np.ndarray,
    so: np.ndarray,
    vw: np.ndarray,
    hi60: np.ndarray,
    lo60: np.ndarray,
    pers60: np.ndarray,
    volr: np.ndarray,
    atr: np.ndarray,
    mor_close: np.ndarray,
    mor_close_known: np.ndarray,
    es: int,
    ee: int,
    min_ret: float,
    min_p: float,
    req_vw: int,
    brk_vm: float,
    stop_mode: int,
    buf: float,
    target_r: float,
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
    mid_mid = np.empty(n, dtype=np.float64)
    for i in range(n):
        mid_mid[i] = (hi60[i] + lo60[i]) * 0.5
    for i in range(n):
        if minute[i] < es or minute[i] > ee:
            continue
        if not mor_close_known[i]:
            continue
        mc = mor_close[i]
        morning_ok = False
        if not np.isnan(mc) and (mc - so[i]) >= min_ret * atr[i]:
            morning_ok = True
        if pers60[i] >= min_p:
            morning_ok = True
        if not morning_ok:
            continue
        if close[i] <= hi60[i]:
            continue
        if volr[i] < brk_vm:
            continue
        if req_vw != 0 and close[i] <= vw[i]:
            continue
        cand_long[i] = True
    fl, fs = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)
    for i in range(n):
        if not fl[i]:
            continue
        if stop_mode == 0:
            sl = mid_mid[i]
        elif stop_mode == 1:
            sl = lo60[i]
        else:
            sl = vw[i] - buf * atr[i]
        risk_l = close[i] - sl
        if risk_l <= 0:
            continue
        side[i] = 1
        valid[i] = True
        stp[i] = sl
        tgtp[i] = close[i] + target_r * risk_l
        tmc[i] = TM_FIXED_R
        tr[i] = target_r
        rsk[i] = risk_l
    apply_min_risk_filter_numba_kernel(valid, side, rsk, min_risk)
    return side, valid, stp, tgtp, tmc, tr, rsk


class AfternoonContinuationStrategy(BaseStrategy):
    """Afternoon continuation — long-only MVP; `features.midday_window` is not used."""

    name = "afternoon_continuation"
    supports_fast = True
    performance_tier = "A_true_context_fast_core"

    def validate_config(self, config: dict[str, Any]) -> None:
        validate_common_strategy_config(config)
        validate_long_only_mvp(config, strategy_name=self.name)
        if has_nested(config, "features.midday_window"):
            raise ValueError(
                f"{self.name}: features.midday_window is not used by the engine; remove it from YAML"
            )
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        feat = config.get("features") or {}
        validate_minute_range(
            "signal.entry_start_minute",
            sig.get("entry_start_minute"),
            "signal.entry_end_minute",
            sig.get("entry_end_minute"),
        )
        mem = int(feat.get("morning_end_minute", 120))
        validate_minute_value("features.morning_end_minute", mem)
        es = int(sig["entry_start_minute"])
        if es <= mem:
            raise ValueError(
                f"signal.entry_start_minute ({es}) must be > features.morning_end_minute ({mem})"
            )
        validate_nonnegative_number("signal.min_morning_return_atr", sig.get("min_morning_return_atr", 1.0))
        validate_nonnegative_number("signal.min_vwap_persistence", sig.get("min_vwap_persistence", 0.7))
        validate_nonnegative_number("signal.breakout_volume_mult", sig.get("breakout_volume_mult", 1.2))
        sm = str(risk.get("stop_mode", "midday_mid"))
        if sm not in ("midday_mid", "midday_low", "vwap_buffer"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        validate_positive_number("risk.target_r", risk.get("target_r"))
        validate_nonnegative_number("risk.vwap_buffer_atr", risk.get("vwap_buffer_atr", 0.1))
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
            "session_open",
            "vwap",
            "rolling_high_60_prior",
            "rolling_low_60_prior",
            "vwap_persistence_above_60",
            "volume_ratio_20",
            "atr_like_15",
        ]

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        feat = config.get("features") or {}
        sig = config.get("signal") or {}
        return (
            "afternoon_ctx",
            int(feat.get("morning_end_minute", 120)),
            str(sig.get("atr_column", "atr_like_15")),
        )

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> AfternoonContext:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        feat = config.get("features") or {}
        mem = int(feat.get("morning_end_minute", 120))
        session_id = session_id_from_dates(work["session_date"])
        minute = work["minute_from_open"].to_numpy(dtype=np.int32)
        close = work["close"].to_numpy(dtype=np.float64)
        mor_close, mor_close_known = first_value_when_minute_ge_with_known(close, minute, session_id, mem)
        atr = atr_series(work, config).to_numpy(dtype=np.float64)
        return AfternoonContext(
            n=len(work),
            session_id=session_id,
            minute=minute,
            close=close,
            session_open=work["session_open"].to_numpy(dtype=np.float64),
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            hi60=work["rolling_high_60_prior"].to_numpy(dtype=np.float64),
            lo60=work["rolling_low_60_prior"].to_numpy(dtype=np.float64),
            pers60=work["vwap_persistence_above_60"].to_numpy(dtype=np.float64),
            volr=work["volume_ratio_20"].to_numpy(dtype=np.float64),
            atr=atr,
            mor_close=mor_close,
            mor_close_known=mor_close_known,
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, AfternoonContext):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es = int(sig["entry_start_minute"])
        ee = int(sig["entry_end_minute"])
        min_ret = float(sig.get("min_morning_return_atr", 1.0))
        min_p = float(sig.get("min_vwap_persistence", 0.7))
        req_vw = int(bool(sig.get("require_midday_hold_vwap", False)))
        brk_vm = float(sig.get("breakout_volume_mult", 1.2))
        stop_mode = str(risk.get("stop_mode", "midday_mid"))
        buf = float(risk.get("vwap_buffer_atr", 0.1))
        target_r = float(risk["target_r"])
        max_tr = int(risk.get("max_trades_per_day", 1))
        min_risk = get_min_risk_per_share(config)
        smap = {"midday_mid": 0, "midday_low": 1, "vwap_buffer": 2}
        sm = smap.get(stop_mode, 0)
        side, valid, stp, tgtp, tmc, tr, rsk = _afternoon_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.close,
            ctx.session_open,
            ctx.vwap,
            ctx.hi60,
            ctx.lo60,
            ctx.pers60,
            ctx.volr,
            ctx.atr,
            ctx.mor_close,
            ctx.mor_close_known,
            es,
            ee,
            min_ret,
            min_p,
            req_vw,
            brk_vm,
            sm,
            buf,
            target_r,
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
        out["sig_target_mode"] = np.where(arr["target_mode_code"] == TM_FIXED_R, "fixed_r", "")
        out["sig_target_r"] = arr["target_r"]
        out["sig_risk_per_share"] = arr["risk_preview"]
        out.loc[out["sig_valid"], "sig_reason"] = "afternoon_cont_long"
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

        return (
            int(feat.get("morning_end_minute", 120)),
            str(sig.get("atr_column", "atr_like_15")),
            int(sig["entry_start_minute"]),
            int(sig["entry_end_minute"]),
            float(sig.get("min_morning_return_atr", 1.0)),
            float(sig.get("min_vwap_persistence", 0.7)),
            bool(sig.get("require_midday_hold_vwap", False)),
            float(sig.get("breakout_volume_mult", 1.2)),
            str(risk.get("stop_mode", "midday_mid")),
            float(risk["target_r"]),
            float(risk.get("min_risk_per_share") or 0.0),
            nz(bt.get("max_hold_minutes")),
        )
