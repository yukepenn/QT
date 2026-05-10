"""Supertrend ATR flip / pullback — long-only MVP."""

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
class SupertrendContext:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    st_line: np.ndarray
    st_dir: np.ndarray
    ema20: np.ndarray
    vwap: np.ndarray
    atr: np.ndarray


@njit(cache=True)
def _st_flip_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    close: np.ndarray,
    low: np.ndarray,
    stl: np.ndarray,
    stdir: np.ndarray,
    ema20: np.ndarray,
    vw: np.ndarray,
    atr: np.ndarray,
    es: int,
    ee: int,
    trig: int,
    req_ema: int,
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
        if session_id[i] != session_id[i - 1]:
            continue
        if trig == 0:
            ok = stdir[i] == 1 and stdir[i - 1] == -1
        else:
            ok = stdir[i] == 1 and stdir[i - 1] == 1 and low[i] <= stl[i] and close[i] > stl[i]
        if not ok:
            continue
        if req_ema != 0 and not (close[i] > ema20[i]):
            continue
        if req_vwap != 0 and not (close[i] > vw[i]):
            continue
        cand_long[i] = True
    fl, _ = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)
    for i in range(n):
        if not fl[i]:
            continue
        if stop_mode == 0:
            sl = stl[i]
        elif stop_mode == 1:
            sl = low[i] - atr_buf * atr[i]
        else:
            sl = low[i]
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


class SupertrendAtrFlipStrategy(BaseStrategy):
    name = "supertrend_atr_flip"
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
        validate_int_at_least("features.atr_window", feat.get("atr_window", 14), 2)
        validate_positive_number("features.supertrend_mult", feat.get("supertrend_mult", 2.0))
        validate_int_at_least("features.ema_window", feat.get("ema_window", 20), 2)
        tm = str(sig.get("trigger_mode", "supertrend_flip_up"))
        if tm not in ("supertrend_flip_up", "supertrend_up_pullback"):
            raise ValueError(f"signal.trigger_mode invalid: {tm!r}")
        sm = str(risk.get("stop_mode", "supertrend_line"))
        if sm not in ("supertrend_line", "atr_buffer", "signal_candle_low"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        validate_nonnegative_number("risk.atr_buffer_mult", risk.get("atr_buffer_mult", 0.35))
        validate_positive_number("risk.target_r", risk.get("target_r"))

    def _st_cols(self, config: dict[str, Any]) -> tuple[str, str]:
        feat = config.get("features") or {}
        aw = int(feat.get("atr_window", 14))
        mult_z = int(round(float(feat.get("supertrend_mult", 2.0)) * 100.0))
        base = f"{aw}_{mult_z}"
        return f"supertrend_line_{base}", f"supertrend_dir_{base}"

    def required_features(self) -> list[str]:
        return [
            "session_date",
            "minute_from_open",
            "low",
            "close",
            "vwap",
            "ema_20",
            "supertrend_line_10_200",
            "supertrend_dir_10_200",
            "supertrend_line_14_200",
            "supertrend_dir_14_200",
            "supertrend_line_14_300",
            "supertrend_dir_14_300",
            "supertrend_line_20_200",
            "supertrend_dir_20_200",
            "atr_like_10",
            "atr_like_14",
            "atr_like_20",
        ]

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        feat = config.get("features") or {}
        sig = config.get("signal") or {}
        return (
            "supertrend_ctx",
            int(feat.get("atr_window", 14)),
            int(round(float(feat.get("supertrend_mult", 2.0)) * 100.0)),
            int(feat.get("ema_window", 20)),
            str(sig.get("trigger_mode", "supertrend_flip_up")),
            str(sig.get("atr_column", "atr_like_20")),
        )

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> SupertrendContext:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        lc, dc = self._st_cols(config)
        for c in (lc, dc):
            if c not in work.columns:
                raise ValueError(f"{self.name}: missing {c!r}; add features.indicators.supertrend_tuples")
        feat = config.get("features") or {}
        ew = int(feat.get("ema_window", 20))
        ema_col = f"ema_{ew}"
        if ema_col not in work.columns:
            raise ValueError(f"{self.name}: missing {ema_col!r}")
        return SupertrendContext(
            n=len(work),
            session_id=session_id_from_dates(work["session_date"]),
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=work["close"].to_numpy(dtype=np.float64),
            low=work["low"].to_numpy(dtype=np.float64),
            st_line=work[lc].to_numpy(dtype=np.float64),
            st_dir=work[dc].to_numpy(dtype=np.int8),
            ema20=work[ema_col].to_numpy(dtype=np.float64),
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            atr=atr_series(work, config).to_numpy(dtype=np.float64),
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, SupertrendContext):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es, ee = int(sig["entry_start_minute"]), int(sig["entry_end_minute"])
        tm = str(sig.get("trigger_mode", "supertrend_flip_up"))
        trig = 0 if tm == "supertrend_flip_up" else 1
        req_ema = int(bool(sig.get("require_ema_filter", False)))
        req_vwap = int(bool(sig.get("require_vwap_side", False)))
        smap = {"supertrend_line": 0, "atr_buffer": 1, "signal_candle_low": 2}
        stop_mode = smap[str(risk.get("stop_mode", "supertrend_line"))]
        side, valid, stp, tgtp, tmc, tr, rsk = _st_flip_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.close,
            ctx.low,
            ctx.st_line,
            ctx.st_dir,
            ctx.ema20,
            ctx.vwap,
            ctx.atr,
            es,
            ee,
            trig,
            req_ema,
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
        feat = config.get("features") or {}
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}

        def nz(x: Any) -> Any:
            if isinstance(x, float) and math.isnan(x):
                return None
            return x

        return (
            int(feat.get("atr_window", 14)),
            float(feat.get("supertrend_mult", 2.0)),
            int(feat.get("ema_window", 20)),
            str(sig.get("trigger_mode", "supertrend_flip_up")),
            bool(sig.get("require_ema_filter", False)),
            bool(sig.get("require_vwap_side", False)),
            str(risk.get("stop_mode", "supertrend_line")),
            float(risk["target_r"]),
            nz((config.get("backtest") or {}).get("max_hold_minutes")),
        )
