"""ADX/DMI trend continuation — long-only MVP."""

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
    rolling_max_by_session_prior_exclusive,
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
class AdxTrendContext:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    plus_di: np.ndarray
    minus_di: np.ndarray
    adx: np.ndarray
    ema20: np.ndarray
    vwap: np.ndarray
    atr: np.ndarray
    hh3_prior: np.ndarray


@njit(cache=True)
def _adx_trend_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    close: np.ndarray,
    low: np.ndarray,
    pdi: np.ndarray,
    mdi: np.ndarray,
    adx: np.ndarray,
    ema20: np.ndarray,
    vw: np.ndarray,
    atr: np.ndarray,
    hh3: np.ndarray,
    es: int,
    ee: int,
    min_adx: float,
    req_rise: int,
    trig: int,
    req_pm: int,
    req_vwap: int,
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
        if adx[i] < min_adx:
            continue
        if req_rise != 0 and not (adx[i] > adx[i - 1]):
            continue
        if req_pm != 0 and not (pdi[i] > mdi[i]):
            continue
        if trig == 0:
            ok = close[i] > hh3[i]
        else:
            ok = close[i] > ema20[i] and close[i - 1] <= ema20[i - 1]
        if not ok:
            continue
        if req_vwap != 0 and not (close[i] > vw[i]):
            continue
        cand_long[i] = True
    fl, _ = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)
    for i in range(n):
        if not fl[i]:
            continue
        if stop_mode == 0:
            sl = ema20[i] - ema_buf * atr[i]
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


class AdxDmiTrendContinuationStrategy(BaseStrategy):
    name = "adx_dmi_trend_continuation"
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
        validate_int_at_least("features.adx_window", feat.get("adx_window", 14), 3)
        validate_int_at_least("features.ema_window", feat.get("ema_window", 20), 2)
        tm = str(sig.get("trigger_mode", "break_3bar_high"))
        if tm not in ("break_3bar_high", "ema20_reclaim"):
            raise ValueError(f"signal.trigger_mode invalid: {tm!r}")
        sm = str(risk.get("stop_mode", "ema20_buffer"))
        if sm not in ("ema20_buffer", "signal_candle_low", "atr_buffer"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        validate_nonnegative_number("signal.min_adx", sig.get("min_adx", 20))
        validate_nonnegative_number("risk.ema_buffer_atr", risk.get("ema_buffer_atr", 0.1))
        validate_nonnegative_number("risk.atr_buffer_mult", risk.get("atr_buffer_mult", 0.35))
        validate_positive_number("risk.target_r", risk.get("target_r"))

    def _adx_cols(self, config: dict[str, Any]) -> tuple[str, str, str]:
        w = int((config.get("features") or {}).get("adx_window", 14))
        return f"plus_di_{w}", f"minus_di_{w}", f"adx_{w}"

    def required_features(self) -> list[str]:
        return [
            "session_date",
            "minute_from_open",
            "low",
            "close",
            "vwap",
            "ema_20",
            "plus_di_14",
            "minus_di_14",
            "adx_14",
            "plus_di_20",
            "minus_di_20",
            "adx_20",
            "rolling_high_3_prior",
            "atr_like_20",
        ]

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        feat = config.get("features") or {}
        sig = config.get("signal") or {}
        return (
            "adx_trend_ctx",
            int(feat.get("adx_window", 14)),
            int(feat.get("ema_window", 20)),
            float(sig.get("min_adx", 20)),
            str(sig.get("trigger_mode", "break_3bar_high")),
            str(sig.get("atr_column", "atr_like_20")),
        )

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> AdxTrendContext:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        pc, mc, ac = self._adx_cols(config)
        for c in (pc, mc, ac):
            if c not in work.columns:
                raise ValueError(f"{self.name}: missing {c!r}")
        feat = config.get("features") or {}
        ew = int(feat.get("ema_window", 20))
        ema_col = f"ema_{ew}"
        if ema_col not in work.columns:
            raise ValueError(f"{self.name}: missing {ema_col!r}")
        session_id = session_id_from_dates(work["session_date"])
        hh3 = rolling_max_by_session_prior_exclusive(work["high"].to_numpy(dtype=np.float64), session_id, 3)
        return AdxTrendContext(
            n=len(work),
            session_id=session_id,
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=work["close"].to_numpy(dtype=np.float64),
            low=work["low"].to_numpy(dtype=np.float64),
            plus_di=work[pc].to_numpy(dtype=np.float64),
            minus_di=work[mc].to_numpy(dtype=np.float64),
            adx=work[ac].to_numpy(dtype=np.float64),
            ema20=work[ema_col].to_numpy(dtype=np.float64),
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            atr=atr_series(work, config).to_numpy(dtype=np.float64),
            hh3_prior=hh3,
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, AdxTrendContext):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es, ee = int(sig["entry_start_minute"]), int(sig["entry_end_minute"])
        min_adx = float(sig.get("min_adx", 20))
        req_rise = int(bool(sig.get("require_adx_rising", False)))
        tm = str(sig.get("trigger_mode", "break_3bar_high"))
        trig = 0 if tm == "break_3bar_high" else 1
        req_pm = int(bool(sig.get("require_plus_di_above_minus_di", True)))
        req_vwap = int(bool(sig.get("require_vwap_side", False)))
        smap = {"ema20_buffer": 0, "signal_candle_low": 1, "atr_buffer": 2}
        stop_mode = smap[str(risk.get("stop_mode", "ema20_buffer"))]
        side, valid, stp, tgtp, tmc, tr, rsk = _adx_trend_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.close,
            ctx.low,
            ctx.plus_di,
            ctx.minus_di,
            ctx.adx,
            ctx.ema20,
            ctx.vwap,
            ctx.atr,
            ctx.hh3_prior,
            es,
            ee,
            min_adx,
            req_rise,
            trig,
            req_pm,
            req_vwap,
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
            int(feat.get("adx_window", 14)),
            int(feat.get("ema_window", 20)),
            float(sig.get("min_adx", 20)),
            bool(sig.get("require_adx_rising", False)),
            str(sig.get("trigger_mode", "break_3bar_high")),
            bool(sig.get("require_plus_di_above_minus_di", True)),
            bool(sig.get("require_vwap_side", False)),
            str(risk.get("stop_mode", "ema20_buffer")),
            float(risk["target_r"]),
            nz((config.get("backtest") or {}).get("max_hold_minutes")),
        )
