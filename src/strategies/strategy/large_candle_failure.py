"""Large candle failure / reclaim — long-only MVP."""

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
class LargeCandleContext:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    vwap: np.ndarray
    atr: np.ndarray
    large_red: np.ndarray
    reclaim_thr: np.ndarray


@njit(cache=True)
def _large_candle_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    close: np.ndarray,
    low: np.ndarray,
    vw: np.ndarray,
    atr: np.ndarray,
    large_red: np.ndarray,
    rthr: np.ndarray,
    es: int,
    ee: int,
    fail_fw: int,
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
    anchor_low = np.zeros(n, dtype=np.float64)
    for i in range(n):
        anchor_low[i] = np.nan
        if minute[i] < es or minute[i] > ee:
            continue
        for j in range(i - 1, -1, -1):
            if session_id[j] != session_id[i]:
                break
            if i < j + fail_fw + 1:
                continue
            if large_red[j] == 0:
                continue
            ok = True
            for k in range(j + 1, i):
                if low[k] < low[j]:
                    ok = False
                    break
            if not ok:
                continue
            if close[i] <= rthr[j]:
                continue
            if req_vwap != 0 and not (close[i] > vw[i]):
                continue
            cand_long[i] = True
            anchor_low[i] = low[j]
            break
    fl, _ = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)
    for i in range(n):
        if not fl[i]:
            continue
        if stop_mode == 0:
            sl = anchor_low[i]
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


class LargeCandleFailureStrategy(BaseStrategy):
    name = "large_candle_failure"
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
        validate_int_at_least("signal.fail_window_bars", sig.get("fail_window_bars", 3), 1)
        validate_positive_number("signal.large_candle_atr", sig.get("large_candle_atr", 2.0))
        rl = str(sig.get("reclaim_level", "candle_mid"))
        if rl not in ("candle_mid", "candle_open"):
            raise ValueError(f"signal.reclaim_level invalid: {rl!r}")
        sm = str(risk.get("stop_mode", "large_candle_low"))
        if sm not in ("large_candle_low", "atr_buffer"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        validate_positive_number("risk.target_r", risk.get("target_r"))
        validate_nonnegative_number("risk.atr_buffer_mult", risk.get("atr_buffer_mult", 0.35))

    def required_features(self) -> list[str]:
        return [
            "session_date",
            "minute_from_open",
            "open",
            "low",
            "close",
            "vwap",
            "bar_range",
            "is_red",
            "atr_like_20",
        ]

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        sig = config.get("signal") or {}
        return (
            "large_candle_ctx",
            int(sig.get("fail_window_bars", 3)),
            float(sig.get("large_candle_atr", 2.0)),
            str(sig.get("reclaim_level", "candle_mid")),
            str(sig.get("atr_column", "atr_like_20")),
        )

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> LargeCandleContext:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        sig = config.get("signal") or {}
        lat = float(sig.get("large_candle_atr", 2.0))
        atr = atr_series(work, config).astype(float)
        br = work["bar_range"].astype(float)
        is_red = work["is_red"].astype(bool)
        large_red = (is_red & (br > lat * atr)).to_numpy(dtype=np.int8)
        o = work["open"].to_numpy(dtype=np.float64)
        c = work["close"].to_numpy(dtype=np.float64)
        rl = str(sig.get("reclaim_level", "candle_mid"))
        reclaim_thr = (
            np.where(large_red > 0, o, np.nan)
            if rl == "candle_open"
            else np.where(large_red > 0, (o + c) * 0.5, np.nan)
        ).astype(np.float64)
        return LargeCandleContext(
            n=len(work),
            session_id=session_id_from_dates(work["session_date"]),
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=c,
            low=work["low"].to_numpy(dtype=np.float64),
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            atr=atr.to_numpy(dtype=np.float64),
            large_red=large_red,
            reclaim_thr=reclaim_thr,
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, LargeCandleContext):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es, ee = int(sig["entry_start_minute"]), int(sig["entry_end_minute"])
        fail_fw = int(sig.get("fail_window_bars", 3))
        req_vwap = int(bool(sig.get("require_vwap_filter", False)))
        smap = {"large_candle_low": 0, "atr_buffer": 1}
        stop_mode = smap[str(risk.get("stop_mode", "large_candle_low"))]
        side, valid, stp, tgtp, tmc, tr, rsk = _large_candle_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.close,
            ctx.low,
            ctx.vwap,
            ctx.atr,
            ctx.large_red,
            ctx.reclaim_thr,
            es,
            ee,
            fail_fw,
            req_vwap,
            stop_mode,
            float(risk.get("atr_buffer_mult", 0.35)),
            float(risk["target_r"]),
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
        out["sig_target_mode"] = np.where(arr["target_mode_code"] == TM_FIXED_R, "fixed_r", "")
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
            int(sig.get("fail_window_bars", 3)),
            float(sig.get("large_candle_atr", 2.0)),
            str(sig.get("reclaim_level", "candle_mid")),
            bool(sig.get("require_no_new_low", True)),
            bool(sig.get("require_vwap_filter", False)),
            str(risk.get("stop_mode", "large_candle_low")),
            float(risk["target_r"]),
            nz((config.get("backtest") or {}).get("max_hold_minutes")),
        )
