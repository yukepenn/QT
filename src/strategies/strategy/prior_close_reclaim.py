"""Prior session close reclaim — long-only MVP."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numba import njit

from src.backtest.constants import TM_FIXED_PX, TM_FIXED_R, TM_NONE
from src.strategies.strategy._atr_helpers import atr_series
from src.strategies.strategy.base import BaseStrategy, init_standard_signal_columns
from src.strategies.strategy.fast_utils import (
    apply_min_risk_filter_df,
    apply_min_risk_filter_numba_kernel,
    get_min_risk_per_share,
    rolling_max_by_session_prior_exclusive,
    rolling_sum_by_session_int,
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
class PriorCloseReclaimContext:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    pdc: np.ndarray
    vwap: np.ndarray
    atr: np.ndarray
    below_sum_prev: np.ndarray
    hh3_prior: np.ndarray


@njit(cache=True)
def _pdc_reclaim_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    close: np.ndarray,
    low: np.ndarray,
    pdc: np.ndarray,
    vw: np.ndarray,
    atr: np.ndarray,
    below_prev: np.ndarray,
    hh3: np.ndarray,
    es: int,
    ee: int,
    mb: int,
    rbuf: float,
    confirm: int,
    req_vwap_rec: int,
    stop_mode: int,
    pbuf: float,
    atr_buf: float,
    tgt_mode: int,
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
        if below_prev[i] + 1e-9 < float(mb):
            continue
        if not (close[i] > pdc[i] + rbuf * atr[i]):
            continue
        if req_vwap_rec != 0 and not (close[i] > vw[i]):
            continue
        if confirm != 0 and not (close[i] > hh3[i]):
            continue
        cand_long[i] = True
    fl, _ = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)
    for i in range(n):
        if not fl[i]:
            continue
        if stop_mode == 0:
            sl = low[i]
        elif stop_mode == 1:
            sl = pdc[i] - pbuf * atr[i]
        else:
            sl = low[i] - atr_buf * atr[i]
        risk = close[i] - sl
        if risk <= 0:
            continue
        side[i] = 1
        valid[i] = True
        stp[i] = sl
        rsk[i] = risk
        if tgt_mode == 0:
            tgtp[i] = close[i] + target_r * risk
            tmc[i] = TM_FIXED_R
            tr[i] = target_r
        else:
            tgtp[i] = vw[i]
            tmc[i] = TM_FIXED_PX
    apply_min_risk_filter_numba_kernel(valid, side, rsk, min_risk)
    return side, valid, stp, tgtp, tmc, tr, rsk


class PriorCloseReclaimStrategy(BaseStrategy):
    name = "prior_close_reclaim"
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
        validate_int_at_least("signal.min_bars_below_prior_close", sig.get("min_bars_below_prior_close", 10), 1)
        validate_nonnegative_number("signal.reclaim_buffer_atr", sig.get("reclaim_buffer_atr", 0.0))
        cm = str(sig.get("confirm_mode", "close_reclaim"))
        if cm not in ("close_reclaim", "break_3bar_high"):
            raise ValueError(f"signal.confirm_mode invalid: {cm!r}")
        sm = str(risk.get("stop_mode", "reclaim_candle_low"))
        if sm not in ("reclaim_candle_low", "prior_close_buffer", "atr_buffer"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        tm = str(risk.get("target_mode", "fixed_r"))
        if tm not in ("fixed_r", "vwap"):
            raise ValueError(f"risk.target_mode invalid: {tm!r}")
        if tm == "fixed_r":
            validate_positive_number("risk.target_r", risk.get("target_r", 1.0))
        validate_nonnegative_number("risk.prior_close_buffer_atr", risk.get("prior_close_buffer_atr", 0.1))
        validate_nonnegative_number("risk.atr_buffer_mult", risk.get("atr_buffer_mult", 0.35))

    def required_features(self) -> list[str]:
        return [
            "session_date",
            "minute_from_open",
            "low",
            "close",
            "vwap",
            "prior_day_close",
            "rolling_high_3_prior",
            "atr_like_20",
        ]

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        sig = config.get("signal") or {}
        return (
            "prior_close_reclaim_ctx",
            int(sig.get("min_bars_below_prior_close", 10)),
            float(sig.get("reclaim_buffer_atr", 0.0)),
            str(sig.get("atr_column", "atr_like_20")),
        )

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> PriorCloseReclaimContext:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        sig = config.get("signal") or {}
        mb = int(sig.get("min_bars_below_prior_close", 10))
        pdc = work["prior_day_close"].to_numpy(dtype=np.float64)
        cls = work["close"].to_numpy(dtype=np.float64)
        below = (cls < pdc).astype(np.float64)
        session_id = session_id_from_dates(work["session_date"])
        rs = rolling_sum_by_session_int(below, session_id, mb)
        below_prev = np.zeros(len(work), dtype=np.float64)
        for i in range(1, len(work)):
            if session_id[i] != session_id[i - 1]:
                below_prev[i] = 0.0
            else:
                below_prev[i] = rs[i - 1]
        hh3 = rolling_max_by_session_prior_exclusive(work["high"].to_numpy(dtype=np.float64), session_id, 3)
        return PriorCloseReclaimContext(
            n=len(work),
            session_id=session_id,
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=cls,
            low=work["low"].to_numpy(dtype=np.float64),
            pdc=pdc,
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            atr=atr_series(work, config).to_numpy(dtype=np.float64),
            below_sum_prev=below_prev,
            hh3_prior=hh3,
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, PriorCloseReclaimContext):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es, ee = int(sig["entry_start_minute"]), int(sig["entry_end_minute"])
        mb = int(sig.get("min_bars_below_prior_close", 10))
        rbuf = float(sig.get("reclaim_buffer_atr", 0.0))
        confirm = 0 if str(sig.get("confirm_mode", "close_reclaim")) == "close_reclaim" else 1
        req_vwap_rec = int(bool(sig.get("require_vwap_reclaim", False)))
        smap = {"reclaim_candle_low": 0, "prior_close_buffer": 1, "atr_buffer": 2}
        stop_mode = smap[str(risk.get("stop_mode", "reclaim_candle_low"))]
        tgt_mode = 0 if str(risk.get("target_mode", "fixed_r")) == "fixed_r" else 1
        target_r = float(risk.get("target_r", 1.0))
        side, valid, stp, tgtp, tmc, tr, rsk = _pdc_reclaim_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.close,
            ctx.low,
            ctx.pdc,
            ctx.vwap,
            ctx.atr,
            ctx.below_sum_prev,
            ctx.hh3_prior,
            es,
            ee,
            mb,
            rbuf,
            confirm,
            req_vwap_rec,
            stop_mode,
            float(risk.get("prior_close_buffer_atr", 0.1)),
            float(risk.get("atr_buffer_mult", 0.35)),
            tgt_mode,
            target_r,
            int(risk.get("max_trades_per_day", 1)),
            float(get_min_risk_per_share(config)),
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
        out.loc[out["sig_valid"], "sig_reason"] = f"{self.name}_long"
        return apply_min_risk_filter_df(out, config=config)

    def normalized_param_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}

        def nz(x: Any) -> Any:
            if isinstance(x, float) and math.isnan(x):
                return None
            return x

        return (
            int(sig.get("min_bars_below_prior_close", 10)),
            float(sig.get("reclaim_buffer_atr", 0.0)),
            bool(sig.get("require_vwap_reclaim", False)),
            str(sig.get("confirm_mode", "close_reclaim")),
            str(risk.get("stop_mode", "reclaim_candle_low")),
            str(risk.get("target_mode", "fixed_r")),
            float(risk.get("target_r", 1.0)),
            nz((config.get("backtest") or {}).get("max_hold_minutes")),
        )
