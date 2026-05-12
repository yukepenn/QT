"""Consecutive red-bar exhaustion reversal — long-only MVP."""

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
    validate_long_only_mvp,
    validate_minute_range,
    validate_positive_number,
)


@dataclass(frozen=True)
class ExhaustionCtx:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    high: np.ndarray
    open_: np.ndarray
    is_red: np.ndarray
    consec_red: np.ndarray
    down_move: np.ndarray
    volr: np.ndarray
    prev_high: np.ndarray
    atr: np.ndarray


@njit(cache=True)
def _exhaust_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    close: np.ndarray,
    low: np.ndarray,
    high: np.ndarray,
    open_: np.ndarray,
    is_red: np.ndarray,
    cred: np.ndarray,
    dmove: np.ndarray,
    volr: np.ndarray,
    ph: np.ndarray,
    atr: np.ndarray,
    es: int,
    ee: int,
    min_red: int,
    min_down_atr: float,
    req_wick: int,
    req_vol: float,
    confirm_mode: int,
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
        if cred[i] < min_red:
            continue
        if dmove[i] < min_down_atr * atr[i]:
            continue
        if req_wick != 0:
            rng = high[i] - low[i]
            if rng < 1e-9:
                continue
            lw = (min(open_[i], close[i]) - low[i]) / rng
            if lw < 0.25:
                continue
        if req_vol > 0.0 and volr[i] < req_vol:
            continue
        ok = False
        if confirm_mode == 0:
            ok = close[i] > ph[i]
        else:
            ok = close[i] > open_[i]
        if not ok:
            continue
        cand_long[i] = True

    fl, fs = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)
    for i in range(n):
        if not fl[i]:
            continue
        if stop_mode == 0:
            sl = low[i]
        elif stop_mode == 1:
            sl = low[i]
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


class ConsecutiveBarExhaustionStrategy(BaseStrategy):
    name = "consecutive_bar_exhaustion"
    supports_fast = True
    performance_tier = "A_true_context_fast_core"

    def validate_config(self, config: dict[str, Any]) -> None:
        validate_common_strategy_config(config)
        validate_long_only_mvp(config, strategy_name=self.name)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        validate_minute_range(
            "signal.entry_start_minute",
            sig.get("entry_start_minute"),
            "signal.entry_end_minute",
            sig.get("entry_end_minute"),
        )
        cm = str(sig.get("confirm_mode", "break_prior_high"))
        if cm not in ("break_prior_high", "close_green"):
            raise ValueError(f"signal.confirm_mode invalid: {cm!r}")
        sm = str(risk.get("stop_mode", "exhaustion_low"))
        if sm not in ("exhaustion_low", "signal_candle_low", "atr_buffer"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        validate_positive_number("risk.target_r", risk.get("target_r"))

    def required_features(self) -> list[str]:
        return [
            "session_date",
            "minute_from_open",
            "open",
            "high",
            "low",
            "close",
            "is_red",
            "prev_high_by_session",
            "volume_ratio_20",
            "atr_like_20",
        ]

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        feat = config.get("features") or {}
        return ("exhaust_ctx", int(feat.get("exhaustion_window", 5)))

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> ExhaustionCtx:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        feat = config.get("features") or {}
        ew = int(feat.get("exhaustion_window", 5))
        gsd = work.groupby("session_date", sort=False)
        is_red = work["is_red"].to_numpy(dtype=np.int8)
        cred = gsd["is_red"].transform(lambda s, w=ew: s.rolling(w, min_periods=1).sum()).to_numpy(dtype=np.float64)
        o = work["open"].to_numpy(dtype=np.float64)
        c = work["close"].to_numpy(dtype=np.float64)
        prev_c = gsd["close"].shift(1)
        drop = (prev_c - work["close"]).clip(lower=0.0)
        dmove = drop.groupby(work["session_date"]).transform(lambda s, w=ew: s.rolling(w, min_periods=1).sum()).to_numpy(dtype=np.float64)
        return ExhaustionCtx(
            n=len(work),
            session_id=session_id_from_dates(work["session_date"]),
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=c,
            low=work["low"].to_numpy(dtype=np.float64),
            high=work["high"].to_numpy(dtype=np.float64),
            open_=o,
            is_red=is_red,
            consec_red=cred,
            down_move=dmove,
            volr=work["volume_ratio_20"].to_numpy(dtype=np.float64),
            prev_high=work["prev_high_by_session"].to_numpy(dtype=np.float64),
            atr=atr_series(work, config).to_numpy(dtype=np.float64),
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, ExhaustionCtx):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es = int(sig["entry_start_minute"])
        ee = int(sig["entry_end_minute"])
        min_red = int(sig.get("min_consecutive_red", 3))
        min_down_atr = float(sig.get("min_down_move_atr", 1.5))
        req_wick = int(bool(sig.get("require_lower_wick", False)))
        req_vol = float(sig.get("volume_surge_mult", 0.0)) if sig.get("require_volume_surge") else 0.0
        cm = str(sig.get("confirm_mode", "break_prior_high"))
        confirm_mode = 0 if cm == "break_prior_high" else 1
        sm = str(risk.get("stop_mode", "exhaustion_low"))
        stop_mode = 0 if sm == "exhaustion_low" else (1 if sm == "signal_candle_low" else 2)
        atr_buf = float(risk.get("atr_buffer_mult", 0.5))
        target_r = float(risk["target_r"])
        max_tr = int(risk.get("max_trades_per_day", 1))
        min_risk = get_min_risk_per_share(config)
        side, valid, stp, tgtp, tmc, tr, rsk = _exhaust_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.close,
            ctx.low,
            ctx.high,
            ctx.open_,
            ctx.is_red,
            ctx.consec_red,
            ctx.down_move,
            ctx.volr,
            ctx.prev_high,
            ctx.atr,
            es,
            ee,
            min_red,
            min_down_atr,
            req_wick,
            req_vol,
            confirm_mode,
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
        out.loc[out["sig_valid"], "sig_reason"] = "consecutive_bar_exhaustion_long"
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
            int(feat.get("exhaustion_window", 5)),
            int(sig.get("min_consecutive_red", 3)),
            float(sig.get("min_down_move_atr", 1.5)),
            bool(sig.get("require_lower_wick", False)),
            bool(sig.get("require_volume_surge", False)),
            str(sig.get("confirm_mode", "break_prior_high")),
            str(risk.get("stop_mode", "exhaustion_low")),
            float(risk["target_r"]),
            nz(risk.get("max_hold_minutes")),
        )
