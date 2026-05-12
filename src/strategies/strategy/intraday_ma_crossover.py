"""Intraday MA crossover / reclaim — long-only MVP, Numba fast core."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numba import njit

from src.execution.types import TM_FIXED_R, TM_NONE
from src.strategies.strategy._atr_helpers import atr_series
from src.strategies.strategy.base import BaseStrategy, init_standard_signal_columns
from src.strategies.strategy.fast_utils import (
    apply_min_risk_filter_df,
    apply_min_risk_filter_numba_kernel,
    get_min_risk_per_share,
    session_id_from_dates,
    thin_first_signal_per_session_numba,
)
from src.utils.config_validation import (
    validate_common_strategy_config,
    validate_int_at_least,
    validate_long_only_mvp,
    validate_minute_range,
    validate_nonnegative_number,
    validate_positive_number,
)


@dataclass(frozen=True)
class IntradayMaCrossoverContext:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    high: np.ndarray
    vwap: np.ndarray
    ema_fast: np.ndarray
    ema_slow: np.ndarray
    ema_trend: np.ndarray
    sma_ref: np.ndarray
    ema_fast_slope: np.ndarray
    atr: np.ndarray


@njit(cache=True)
def _intraday_ma_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    close: np.ndarray,
    low: np.ndarray,
    ema_f: np.ndarray,
    ema_s: np.ndarray,
    ema_t: np.ndarray,
    sma_r: np.ndarray,
    slope_f: np.ndarray,
    vw: np.ndarray,
    atr: np.ndarray,
    es: int,
    ee: int,
    trigger_mode: int,
    req_slope: int,
    min_slope_atr: float,
    req_vwap: int,
    stop_mode: int,
    atr_buf: float,
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

    for i in range(1, n):
        if minute[i] < es or minute[i] > ee:
            continue
        if np.isnan(ema_f[i]) or np.isnan(ema_s[i]):
            continue
        trig = False
        if trigger_mode == 0:
            trig = ema_f[i - 1] <= ema_s[i - 1] and ema_f[i] > ema_s[i]
        else:
            trig = close[i - 1] <= sma_r[i - 1] and close[i] > sma_r[i]
        if not trig:
            continue
        if req_slope != 0 and not (slope_f[i] >= min_slope_atr * atr[i]):
            continue
        if req_vwap != 0 and not (close[i] > vw[i]):
            continue
        if close[i] <= ema_t[i]:
            continue
        cand_long[i] = True

    fl, fs = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)
    for i in range(n):
        if not fl[i]:
            continue
        if stop_mode == 0:
            sl = low[i]
        elif stop_mode == 1:
            sl = ema_s[i] - atr_buf * atr[i]
        else:
            sl = low[i] - atr_buf * atr[i]
        risk = close[i] - sl
        if risk <= 0:
            continue
        side[i] = 1
        valid[i] = True
        stp[i] = sl
        tgtp[i] = close[i] + target_r * risk
        tmc[i] = TM_FIXED_R
        tr[i] = target_r
        rsk[i] = risk
    apply_min_risk_filter_numba_kernel(valid, side, rsk, min_risk)
    return side, valid, stp, tgtp, tmc, tr, rsk


class IntradayMaCrossoverStrategy(BaseStrategy):
    name = "intraday_ma_crossover"
    supports_fast = True
    performance_tier = "A_true_context_fast_core"

    def validate_config(self, config: dict[str, Any]) -> None:
        validate_common_strategy_config(config)
        validate_long_only_mvp(config, strategy_name=self.name)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        feat = config.get("features") or {}
        validate_minute_range(
            "signal.entry_start_minute",
            sig.get("entry_start_minute"),
            "signal.entry_end_minute",
            sig.get("entry_end_minute"),
        )
        validate_int_at_least("features.ema_fast", feat.get("ema_fast", 9), 2)
        validate_int_at_least("features.ema_slow", feat.get("ema_slow", 20), 3)
        validate_int_at_least("features.ema_trend", feat.get("ema_trend", 50), 5)
        validate_int_at_least("features.sma_ref", feat.get("sma_ref", 20), 3)
        tm = str(sig.get("trigger_mode", "ema_fast_cross_slow"))
        if tm not in ("ema_fast_cross_slow", "price_reclaim_sma20"):
            raise ValueError(f"signal.trigger_mode invalid: {tm!r}")
        sm = str(risk.get("stop_mode", "signal_candle_low"))
        if sm not in ("signal_candle_low", "ema_slow_buffer", "atr_buffer"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        validate_positive_number("risk.target_r", risk.get("target_r"))
        validate_nonnegative_number("risk.atr_buffer_mult", risk.get("atr_buffer_mult", 0.5))
        validate_int_at_least("risk.max_trades_per_day", risk.get("max_trades_per_day", 1), 1)
        ac = str(sig.get("atr_column", "atr_like_20") or "").strip()
        if not ac:
            raise ValueError("signal.atr_column must be set")

    def required_features(self) -> list[str]:
        return [
            "session_date",
            "minute_from_open",
            "open",
            "high",
            "low",
            "close",
            "vwap",
            "ema_9",
            "ema_10",
            "ema_20",
            "ema_50",
            "sma_20",
            "ema_slope_9",
            "ema_slope_10",
            "atr_like_20",
        ]

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        feat = config.get("features") or {}
        sig = config.get("signal") or {}
        return (
            "intraday_ma_ctx",
            int(feat.get("ema_fast", 9)),
            int(feat.get("ema_slow", 20)),
            int(feat.get("ema_trend", 50)),
            int(feat.get("sma_ref", 20)),
            str(sig.get("atr_column", "atr_like_20")),
        )

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> IntradayMaCrossoverContext:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        feat = config.get("features") or {}
        ef = int(feat.get("ema_fast", 9))
        es = int(feat.get("ema_slow", 20))
        et = int(feat.get("ema_trend", 50))
        sr = int(feat.get("sma_ref", 20))
        col_f = f"ema_{ef}"
        col_s = f"ema_{es}"
        col_t = f"ema_{et}"
        col_sr = f"sma_{sr}"
        col_sl = f"ema_slope_{ef}"
        return IntradayMaCrossoverContext(
            n=len(work),
            session_id=session_id_from_dates(work["session_date"]),
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=work["close"].to_numpy(dtype=np.float64),
            low=work["low"].to_numpy(dtype=np.float64),
            high=work["high"].to_numpy(dtype=np.float64),
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            ema_fast=work[col_f].to_numpy(dtype=np.float64),
            ema_slow=work[col_s].to_numpy(dtype=np.float64),
            ema_trend=work[col_t].to_numpy(dtype=np.float64),
            sma_ref=work[col_sr].to_numpy(dtype=np.float64),
            ema_fast_slope=work[col_sl].to_numpy(dtype=np.float64),
            atr=atr_series(work, config).to_numpy(dtype=np.float64),
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, IntradayMaCrossoverContext):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es = int(sig["entry_start_minute"])
        ee = int(sig["entry_end_minute"])
        tm = str(sig.get("trigger_mode", "ema_fast_cross_slow"))
        trigger_mode = 0 if tm == "ema_fast_cross_slow" else 1
        req_slope = int(bool(sig.get("require_ema_slope", False)))
        min_slope_atr = float(sig.get("min_slope_atr", 0.0))
        req_vwap = int(bool(sig.get("require_vwap_side", False)))
        sm = str(risk.get("stop_mode", "signal_candle_low"))
        stop_mode = 0 if sm == "signal_candle_low" else (1 if sm == "ema_slow_buffer" else 2)
        atr_buf = float(risk.get("atr_buffer_mult", 0.5))
        target_r = float(risk["target_r"])
        max_tr = int(risk.get("max_trades_per_day", 1))
        min_risk = get_min_risk_per_share(config)
        side, valid, stp, tgtp, tmc, tr, rsk = _intraday_ma_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.close,
            ctx.low,
            ctx.ema_fast,
            ctx.ema_slow,
            ctx.ema_trend,
            ctx.sma_ref,
            ctx.ema_fast_slope,
            ctx.vwap,
            ctx.atr,
            es,
            ee,
            trigger_mode,
            req_slope,
            min_slope_atr,
            req_vwap,
            stop_mode,
            atr_buf,
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
        ctx = self.prepare_signal_context(df, config)
        arr = self.generate_signal_arrays_from_context(ctx, config)
        out = init_standard_signal_columns(work, strategy_name=self.name, copy=True)
        out["sig_side"] = arr["side"]
        out["sig_valid"] = arr["valid"]
        out["sig_stop"] = arr["stop"]
        out["sig_target"] = arr["target_preview"]
        out["sig_target_mode"] = np.where(arr["target_mode_code"] == TM_FIXED_R, "fixed_r", "")
        out["sig_target_r"] = arr["target_r"]
        out["sig_risk_per_share"] = arr["risk_preview"]
        out.loc[out["sig_valid"], "sig_reason"] = "intraday_ma_crossover_long"
        return apply_min_risk_filter_df(out, config=config)

    def normalized_param_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        feat = config.get("features") or {}
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}

        def nz(x: Any) -> Any:
            if isinstance(x, float) and math.isnan(x):
                return None
            return x

        return (
            int(feat.get("ema_fast", 9)),
            int(feat.get("ema_slow", 20)),
            int(feat.get("ema_trend", 50)),
            int(feat.get("sma_ref", 20)),
            str(sig.get("trigger_mode", "ema_fast_cross_slow")),
            bool(sig.get("require_ema_slope", False)),
            bool(sig.get("require_vwap_side", False)),
            float(sig.get("min_slope_atr", 0.0)),
            str(risk.get("stop_mode", "signal_candle_low")),
            float(risk.get("atr_buffer_mult", 0.5)),
            float(risk["target_r"]),
            nz(risk.get("max_hold_minutes")),
        )
