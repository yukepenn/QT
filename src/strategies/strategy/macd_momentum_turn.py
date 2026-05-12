"""MACD momentum turn — long-only MVP."""

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
class MacdMomentumContext:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    line: np.ndarray
    sigl: np.ndarray
    hist: np.ndarray
    ema20: np.ndarray
    vwap: np.ndarray
    atr: np.ndarray


@njit(cache=True)
def _macd_mom_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    close: np.ndarray,
    low: np.ndarray,
    line: np.ndarray,
    sigl: np.ndarray,
    hist: np.ndarray,
    ema20: np.ndarray,
    vw: np.ndarray,
    atr: np.ndarray,
    es: int,
    ee: int,
    trig: int,
    req_ema: int,
    req_vwap: int,
    min_slope: float,
    stop_mode: int,
    ema_buf: float,
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
        if req_ema != 0 and not (close[i] > ema20[i]):
            continue
        if req_vwap != 0 and not (close[i] > vw[i]):
            continue
        hs = hist[i] - hist[i - 1]
        if min_slope > 0.0 and hs < min_slope * atr[i]:
            continue
        ok = False
        if trig == 0:
            ok = hist[i - 1] <= 0.0 and hist[i] > 0.0
        elif trig == 1:
            ok = line[i - 1] <= sigl[i - 1] and line[i] > sigl[i]
        else:
            ok = line[i - 1] <= 0.0 and line[i] > 0.0
        if not ok:
            continue
        cand_long[i] = True
    fl, _ = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)
    for i in range(n):
        if not fl[i]:
            continue
        if stop_mode == 0:
            sl = low[i]
        elif stop_mode == 1:
            sl = ema20[i] - ema_buf * atr[i]
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


class MacdMomentumTurnStrategy(BaseStrategy):
    name = "macd_momentum_turn"
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
        validate_int_at_least("features.macd_fast", feat.get("macd_fast", 12), 2)
        validate_int_at_least("features.macd_slow", feat.get("macd_slow", 26), 3)
        validate_int_at_least("features.macd_signal", feat.get("macd_signal", 9), 2)
        validate_int_at_least("features.ema_window", feat.get("ema_window", 20), 2)
        mf, ms = int(feat.get("macd_fast", 12)), int(feat.get("macd_slow", 26))
        if mf >= ms:
            raise ValueError("features.macd_fast must be < features.macd_slow")
        tm = str(sig.get("trigger_mode", "hist_cross_up"))
        if tm not in ("hist_cross_up", "macd_signal_cross", "zero_reclaim"):
            raise ValueError(f"signal.trigger_mode invalid: {tm!r}")
        sm = str(risk.get("stop_mode", "signal_candle_low"))
        if sm not in ("signal_candle_low", "ema_buffer", "atr_buffer"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        validate_nonnegative_number("signal.min_hist_slope", sig.get("min_hist_slope", 0.0))
        validate_nonnegative_number("risk.ema_buffer_atr", risk.get("ema_buffer_atr", 0.1))
        validate_nonnegative_number("risk.atr_buffer_mult", risk.get("atr_buffer_mult", 0.35))
        validate_positive_number("risk.target_r", risk.get("target_r"))

    def _col_names(self, config: dict[str, Any]) -> tuple[str, str, str]:
        feat = config.get("features") or {}
        f, s, sg = int(feat.get("macd_fast", 12)), int(feat.get("macd_slow", 26)), int(feat.get("macd_signal", 9))
        return (
            f"macd_line_{f}_{s}",
            f"macd_signal_{f}_{s}_{sg}",
            f"macd_hist_{f}_{s}_{sg}",
        )

    def required_features(self) -> list[str]:
        return [
            "session_date",
            "minute_from_open",
            "low",
            "close",
            "vwap",
            "ema_20",
            "macd_line_8_21",
            "macd_signal_8_21_9",
            "macd_hist_8_21_9",
            "macd_line_12_26",
            "macd_signal_12_26_9",
            "macd_hist_12_26_9",
            "atr_like_20",
        ]

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        feat = config.get("features") or {}
        return (
            "macd_mom_ctx",
            int(feat.get("macd_fast", 12)),
            int(feat.get("macd_slow", 26)),
            int(feat.get("macd_signal", 9)),
            int(feat.get("ema_window", 20)),
            str((config.get("signal") or {}).get("atr_column", "atr_like_20")),
        )

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> MacdMomentumContext:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        ln, sn, hn = self._col_names(config)
        for c in (ln, sn, hn):
            if c not in work.columns:
                raise ValueError(f"{self.name}: missing {c!r}; extend features.indicators.macd_tuples")
        feat = config.get("features") or {}
        ew = int(feat.get("ema_window", 20))
        ema_col = f"ema_{ew}"
        if ema_col not in work.columns:
            raise ValueError(f"{self.name}: missing {ema_col!r}")
        return MacdMomentumContext(
            n=len(work),
            session_id=session_id_from_dates(work["session_date"]),
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=work["close"].to_numpy(dtype=np.float64),
            low=work["low"].to_numpy(dtype=np.float64),
            line=work[ln].to_numpy(dtype=np.float64),
            sigl=work[sn].to_numpy(dtype=np.float64),
            hist=work[hn].to_numpy(dtype=np.float64),
            ema20=work[ema_col].to_numpy(dtype=np.float64),
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            atr=atr_series(work, config).to_numpy(dtype=np.float64),
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, MacdMomentumContext):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es, ee = int(sig["entry_start_minute"]), int(sig["entry_end_minute"])
        tm = str(sig.get("trigger_mode", "hist_cross_up"))
        trig = 0 if tm == "hist_cross_up" else (1 if tm == "macd_signal_cross" else 2)
        req_ema = int(bool(sig.get("require_price_above_ema", True)))
        req_vwap = int(bool(sig.get("require_vwap_side", False)))
        min_slope = float(sig.get("min_hist_slope", 0.0))
        smap = {"signal_candle_low": 0, "ema_buffer": 1, "atr_buffer": 2}
        stop_mode = smap[str(risk.get("stop_mode", "signal_candle_low"))]
        side, valid, stp, tgtp, tmc, tr, rsk = _macd_mom_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.close,
            ctx.low,
            ctx.line,
            ctx.sigl,
            ctx.hist,
            ctx.ema20,
            ctx.vwap,
            ctx.atr,
            es,
            ee,
            trig,
            req_ema,
            req_vwap,
            min_slope,
            stop_mode,
            float(risk.get("ema_buffer_atr", 0.1)),
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
            int(feat.get("macd_fast", 12)),
            int(feat.get("macd_slow", 26)),
            int(feat.get("macd_signal", 9)),
            int(feat.get("ema_window", 20)),
            str(sig.get("trigger_mode", "hist_cross_up")),
            bool(sig.get("require_price_above_ema", True)),
            bool(sig.get("require_vwap_side", False)),
            float(sig.get("min_hist_slope", 0.0)),
            str(risk.get("stop_mode", "signal_candle_low")),
            float(risk["target_r"]),
            nz((config.get("backtest") or {}).get("max_hold_minutes")),
        )
