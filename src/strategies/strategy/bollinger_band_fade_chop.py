"""Bollinger band fade in chop — long-only mean reversion MVP."""

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
class BollingerFadeCtx:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    high: np.ndarray
    lower: np.ndarray
    mid: np.ndarray
    re: np.ndarray
    vwap_x: np.ndarray
    atr: np.ndarray


@njit(cache=True)
def _bb_fade_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    close: np.ndarray,
    low: np.ndarray,
    high: np.ndarray,
    lower: np.ndarray,
    mid: np.ndarray,
    re: np.ndarray,
    vwap_x: np.ndarray,
    atr: np.ndarray,
    es: int,
    ee: int,
    req_reg: int,
    max_re: float,
    min_vx: float,
    trigger_mode: int,
    stop_mode: int,
    atr_buf: float,
    target_mode: int,
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
        if req_reg != 0:
            if not (re[i] <= max_re or vwap_x[i] >= min_vx):
                continue
        if close[i - 1] > lower[i - 1]:
            continue
        trig = False
        if trigger_mode == 0:
            trig = close[i] > lower[i]
        else:
            trig = (low[i] <= lower[i]) and (close[i] > lower[i]) and (high[i] - close[i]) > (close[i] - low[i])
        if not trig:
            continue
        cand_long[i] = True

    fl, fs = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)
    for i in range(n):
        if not fl[i]:
            continue
        if stop_mode == 0:
            sl = lower[i] - atr_buf * atr[i]
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
        if target_mode == 0:
            tgtp[i] = close[i] + target_r * risk
            tmc[i] = TM_FIXED_R
            tr[i] = target_r
        else:
            tgtp[i] = mid[i]
            tmc[i] = TM_FIXED_PX
            tr[i] = 0.0
        rsk[i] = risk
    apply_min_risk_filter_numba_kernel(valid, side, rsk, min_risk)
    return side, valid, stp, tgtp, tmc, tr, rsk


class BollingerBandFadeChopStrategy(BaseStrategy):
    name = "bollinger_band_fade_chop"
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
        tm = str(sig.get("trigger_mode", "lower_band_reclaim"))
        if tm not in ("lower_band_reclaim", "wick_rejection"):
            raise ValueError(f"signal.trigger_mode invalid: {tm!r}")
        sm = str(risk.get("stop_mode", "band_extreme"))
        if sm not in ("band_extreme", "signal_candle_low", "atr_buffer"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        tgtm = str(risk.get("target_mode", "fixed_r"))
        if tgtm not in ("fixed_r", "bb_mid"):
            raise ValueError(f"risk.target_mode invalid: {tgtm!r}")
        if tgtm == "fixed_r":
            validate_positive_number("risk.target_r", risk.get("target_r"))

    def required_features(self) -> list[str]:
        return [
            "session_date",
            "minute_from_open",
            "high",
            "low",
            "close",
            "bb_mid_20",
            "bb_mid_30",
            "bb_lower_20_1.5",
            "bb_lower_20_2.0",
            "bb_lower_30_1.5",
            "bb_lower_30_2.0",
            "range_efficiency_30",
            "range_efficiency_60",
            "vwap_cross_count_30",
            "vwap_cross_count_60",
            "atr_like_20",
        ]

    def _cols(self, config: dict[str, Any]) -> tuple[str, str, str, str]:
        feat = config.get("features") or {}
        w = int(feat.get("bb_window", 20))
        std = float(feat.get("bb_std", 2.0))
        rw = int(feat.get("regime_window", 30))
        return f"bb_lower_{w}_{std}", f"bb_mid_{w}", f"range_efficiency_{rw}", f"vwap_cross_count_{rw}"

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        return ("bb_fade_ctx",) + self._cols(config)

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> BollingerFadeCtx:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        lo_c, mid_c, re_c, vx_c = self._cols(config)
        return BollingerFadeCtx(
            n=len(work),
            session_id=session_id_from_dates(work["session_date"]),
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=work["close"].to_numpy(dtype=np.float64),
            low=work["low"].to_numpy(dtype=np.float64),
            high=work["high"].to_numpy(dtype=np.float64),
            lower=work[lo_c].to_numpy(dtype=np.float64),
            mid=work[mid_c].to_numpy(dtype=np.float64),
            re=work[re_c].to_numpy(dtype=np.float64),
            vwap_x=work[vx_c].to_numpy(dtype=np.float64),
            atr=atr_series(work, config).to_numpy(dtype=np.float64),
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, BollingerFadeCtx):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es = int(sig["entry_start_minute"])
        ee = int(sig["entry_end_minute"])
        req_reg = int(bool(sig.get("require_range_regime", True)))
        max_re = float(sig.get("max_range_efficiency", 0.25))
        min_vx = float(sig.get("min_vwap_cross_count", 3.0))
        tm = str(sig.get("trigger_mode", "lower_band_reclaim"))
        trigger_mode = 0 if tm == "lower_band_reclaim" else 1
        sm = str(risk.get("stop_mode", "band_extreme"))
        stop_mode = 0 if sm == "band_extreme" else (1 if sm == "signal_candle_low" else 2)
        atr_buf = float(risk.get("atr_buffer_mult", 0.25))
        tgtm = str(risk.get("target_mode", "fixed_r"))
        target_mode = 0 if tgtm == "fixed_r" else 1
        target_r = float(risk.get("target_r", 1.0))
        max_tr = int(risk.get("max_trades_per_day", 1))
        min_risk = get_min_risk_per_share(config)
        side, valid, stp, tgtp, tmc, tr, rsk = _bb_fade_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.close,
            ctx.low,
            ctx.high,
            ctx.lower,
            ctx.mid,
            ctx.re,
            ctx.vwap_x,
            ctx.atr,
            es,
            ee,
            req_reg,
            max_re,
            min_vx,
            trigger_mode,
            stop_mode,
            atr_buf,
            target_mode,
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
        out["sig_target_mode"] = np.where(arr["target_mode_code"] == TM_FIXED_R, "fixed_r", "bb_mid")
        out["sig_target_r"] = arr["target_r"]
        out["sig_risk_per_share"] = arr["risk_preview"]
        out.loc[out["sig_valid"], "sig_reason"] = "bollinger_band_fade_chop_long"
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
            int(feat.get("bb_window", 20)),
            float(feat.get("bb_std", 2.0)),
            int(feat.get("regime_window", 30)),
            bool(sig.get("require_range_regime", True)),
            float(sig.get("max_range_efficiency", 0.25)),
            float(sig.get("min_vwap_cross_count", 3.0)),
            str(sig.get("trigger_mode", "lower_band_reclaim")),
            str(risk.get("stop_mode", "band_extreme")),
            str(risk.get("target_mode", "fixed_r")),
            float(risk.get("target_r", 1.0)),
            nz(risk.get("max_hold_minutes")),
        )
