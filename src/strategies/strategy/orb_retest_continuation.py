"""ORB breakout + shallow retest continuation — true Numba fast core."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numba import njit

from src.backtest.constants import TM_FIXED_R, TM_NONE
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
    recent_any_bool_in_window_session,
    rolling_min_by_session,
    session_id_from_dates,
    thin_first_signal_per_session_numba,
)


@dataclass(frozen=True)
class OrbRetestContext:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    after_orb: np.ndarray
    close: np.ndarray
    low: np.ndarray
    orb_high: np.ndarray
    orb_mid: np.ndarray
    vwap: np.ndarray
    prev_high: np.ndarray
    vwap_slope_20: np.ndarray
    atr: np.ndarray
    recent_break: np.ndarray
    lo_roll: np.ndarray


@njit(cache=True)
def _orb_retest_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    after_orb: np.ndarray,
    close: np.ndarray,
    low: np.ndarray,
    oh: np.ndarray,
    om: np.ndarray,
    vw: np.ndarray,
    ph: np.ndarray,
    slope20: np.ndarray,
    atr: np.ndarray,
    recent_br: np.ndarray,
    lo_roll: np.ndarray,
    es: int,
    ee: int,
    ret_tol: float,
    req_vw: int,
    req_slope: int,
    stop_orb_mid: int,
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
    for i in range(n):
        if after_orb[i] == 0.0 or minute[i] < es or minute[i] > ee:
            continue
        if not recent_br[i]:
            continue
        if lo_roll[i] > oh[i] + ret_tol * atr[i]:
            continue
        if close[i] < oh[i] or close[i] <= ph[i]:
            continue
        if req_vw != 0 and close[i] <= vw[i]:
            continue
        if req_slope != 0 and slope20[i] <= 0.0:
            continue
        cand_long[i] = True
    cand_short = np.zeros(n, dtype=np.bool_)
    fl, _ = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)
    for i in range(n):
        if not fl[i]:
            continue
        sl = om[i] if stop_orb_mid != 0 else lo_roll[i]
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


class OrbRetestContinuationStrategy(BaseStrategy):
    """ORB breakout + shallow retest — long-only MVP."""

    name = "orb_retest_continuation"
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
        validate_int_at_least("signal.max_retest_bars", sig.get("max_retest_bars", 10), 1)
        validate_nonnegative_number("signal.retest_tolerance_atr", sig.get("retest_tolerance_atr", 0.5))
        stop_mode = str(risk.get("stop_mode", "retest_low"))
        if stop_mode not in ("retest_low", "orb_mid"):
            raise ValueError(f"risk.stop_mode invalid: {stop_mode!r}")
        validate_positive_number("risk.target_r", risk.get("target_r"))
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
            "vwap",
            "vwap_slope_5",
            "vwap_slope_20",
            "after_orb",
            "orb_high",
            "orb_mid",
            "prev_high_by_session",
            "atr_like_15",
        ]

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        sig = config.get("signal") or {}
        return (
            "orb_retest_ctx",
            int(sig.get("max_retest_bars", 10)),
            str(sig.get("atr_column", "atr_like_15")),
        )

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> OrbRetestContext:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        sig = config.get("signal") or {}
        mrb = int(sig.get("max_retest_bars", 10))
        session_id = session_id_from_dates(work["session_date"])
        cls_f = work["close"].to_numpy(dtype=np.float64)
        oh = work["orb_high"].to_numpy(dtype=np.float64)
        brk = cls_f > oh
        recent_br = recent_any_bool_in_window_session(brk, session_id, mrb)
        low = work["low"].to_numpy(dtype=np.float64)
        lo_roll = rolling_min_by_session(low, session_id, mrb)
        atr = atr_series(work, config).to_numpy(dtype=np.float64)
        return OrbRetestContext(
            n=len(work),
            session_id=session_id,
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            after_orb=work["after_orb"].astype(float).to_numpy(),
            close=cls_f,
            low=low,
            orb_high=oh,
            orb_mid=work["orb_mid"].to_numpy(dtype=np.float64),
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            prev_high=work["prev_high_by_session"].to_numpy(dtype=np.float64),
            vwap_slope_20=work["vwap_slope_20"].to_numpy(dtype=np.float64),
            atr=atr,
            recent_break=recent_br.astype(np.float64),
            lo_roll=lo_roll,
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, OrbRetestContext):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es = int(sig["entry_start_minute"])
        ee = int(sig["entry_end_minute"])
        ret_tol = float(sig.get("retest_tolerance_atr", 0.5))
        req_vw = int(bool(sig.get("require_vwap_side", True)))
        req_slope = int(bool(sig.get("require_vwap_slope", False)))
        stop_mode = str(risk.get("stop_mode", "retest_low"))
        target_r = float(risk["target_r"])
        max_tr = int(risk.get("max_trades_per_day", 1))
        min_risk = get_min_risk_per_share(config)
        stop_orb_mid = 1 if stop_mode == "orb_mid" else 0

        side, valid, stp, tgtp, tmc, tr, rsk = _orb_retest_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.after_orb,
            ctx.close,
            ctx.low,
            ctx.orb_high,
            ctx.orb_mid,
            ctx.vwap,
            ctx.prev_high,
            ctx.vwap_slope_20,
            ctx.atr,
            ctx.recent_break,
            ctx.lo_roll,
            es,
            ee,
            ret_tol,
            req_vw,
            req_slope,
            stop_orb_mid,
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
        ctx = self.prepare_signal_context(df, config)
        arrays = self.generate_signal_arrays_from_context(ctx, config)
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        out = init_standard_signal_columns(work, strategy_name=self.name, copy=True)
        out["sig_side"] = arrays["side"]
        out["sig_valid"] = arrays["valid"]
        out["sig_stop"] = arrays["stop"]
        out["sig_target"] = arrays["target_preview"]
        out["sig_target_mode"] = np.where(arrays["target_mode_code"] == TM_FIXED_R, "fixed_r", "")
        out["sig_target_r"] = arrays["target_r"]
        out["sig_risk_per_share"] = arrays["risk_preview"]
        out.loc[out["sig_valid"], "sig_reason"] = "orb_retest_long"
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
            int(feat.get("orb_open_minutes", 15)),
            str(sig.get("side", "long_only")),
            str(sig.get("atr_column", "atr_like_15")),
            int(sig["entry_start_minute"]),
            int(sig["entry_end_minute"]),
            float(sig.get("retest_tolerance_atr", 0.5)),
            int(sig.get("max_retest_bars", 10)),
            bool(sig.get("require_vwap_side", True)),
            bool(sig.get("require_vwap_slope", False)),
            str(risk.get("stop_mode", "retest_low")),
            float(risk["target_r"]),
            float(risk.get("min_risk_per_share") or 0.0),
            int(risk.get("max_trades_per_day", 1)),
            nz(bt.get("max_hold_minutes")),
        )
