"""Donchian prior-high breakout with width filter — long-only MVP."""

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
    validate_long_only_mvp,
    validate_minute_range,
    validate_positive_number,
)


@dataclass(frozen=True)
class DonchianCtx:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    vwap: np.ndarray
    d_hi: np.ndarray
    d_w_atr: np.ndarray
    volr: np.ndarray
    atr: np.ndarray


@njit(cache=True)
def _donchian_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    close: np.ndarray,
    low: np.ndarray,
    vw: np.ndarray,
    d_hi: np.ndarray,
    dw: np.ndarray,
    volr: np.ndarray,
    atr: np.ndarray,
    es: int,
    ee: int,
    min_w: float,
    max_w: float,
    req_vwap: int,
    req_vol: float,
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

    for i in range(n):
        if minute[i] < es or minute[i] > ee:
            continue
        if np.isnan(d_hi[i]) or np.isnan(dw[i]):
            continue
        if dw[i] < min_w or dw[i] > max_w:
            continue
        if close[i] <= d_hi[i]:
            continue
        if req_vwap != 0 and close[i] <= vw[i]:
            continue
        if req_vol > 0.0 and volr[i] < req_vol:
            continue
        cand_long[i] = True

    fl, fs = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)
    for i in range(n):
        if not fl[i]:
            continue
        if stop_mode == 0:
            sl = (d_hi[i] + low[i]) * 0.5
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


class DonchianChannelBreakoutStrategy(BaseStrategy):
    name = "donchian_channel_breakout"
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
        sm = str(risk.get("stop_mode", "breakout_candle_low"))
        if sm not in ("channel_mid", "breakout_candle_low", "atr_buffer"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        validate_positive_number("risk.target_r", risk.get("target_r"))

    def required_features(self) -> list[str]:
        return [
            "session_date",
            "minute_from_open",
            "close",
            "low",
            "vwap",
            "volume_ratio_20",
            "donchian_high_20_prior",
            "donchian_high_30_prior",
            "donchian_high_60_prior",
            "donchian_width_atr_20",
            "donchian_width_atr_30",
            "donchian_width_atr_60",
            "atr_like_20",
        ]

    def _dh_dw(self, config: dict[str, Any]) -> tuple[str, str]:
        w = int((config.get("features") or {}).get("donchian_window", 20))
        return f"donchian_high_{w}_prior", f"donchian_width_atr_{w}"

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        return ("donchian_ctx",) + self._dh_dw(config)

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> DonchianCtx:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        dh, dw = self._dh_dw(config)
        return DonchianCtx(
            n=len(work),
            session_id=session_id_from_dates(work["session_date"]),
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=work["close"].to_numpy(dtype=np.float64),
            low=work["low"].to_numpy(dtype=np.float64),
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            d_hi=work[dh].to_numpy(dtype=np.float64),
            d_w_atr=work[dw].to_numpy(dtype=np.float64),
            volr=work["volume_ratio_20"].to_numpy(dtype=np.float64),
            atr=atr_series(work, config).to_numpy(dtype=np.float64),
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, DonchianCtx):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es = int(sig["entry_start_minute"])
        ee = int(sig["entry_end_minute"])
        min_w = float(sig.get("min_channel_width_atr", 1.0))
        max_w = float(sig.get("max_channel_width_atr", 3.0))
        req_vwap = int(bool(sig.get("require_vwap_side", False)))
        req_vol = float(sig.get("volume_expansion_mult", 1.15)) if bool(sig.get("require_volume_expansion")) else 0.0
        sm = str(risk.get("stop_mode", "breakout_candle_low"))
        stop_mode = 0 if sm == "channel_mid" else (1 if sm == "breakout_candle_low" else 2)
        atr_buf = float(risk.get("atr_buffer_mult", 0.5))
        target_r = float(risk["target_r"])
        max_tr = int(risk.get("max_trades_per_day", 1))
        min_risk = get_min_risk_per_share(config)
        side, valid, stp, tgtp, tmc, tr, rsk = _donchian_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.close,
            ctx.low,
            ctx.vwap,
            ctx.d_hi,
            ctx.d_w_atr,
            ctx.volr,
            ctx.atr,
            es,
            ee,
            min_w,
            max_w,
            req_vwap,
            req_vol,
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
        out.loc[out["sig_valid"], "sig_reason"] = "donchian_channel_breakout_long"
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
            int(feat.get("donchian_window", 20)),
            float(sig.get("min_channel_width_atr", 1.0)),
            float(sig.get("max_channel_width_atr", 3.0)),
            bool(sig.get("require_vwap_side", False)),
            bool(sig.get("require_volume_expansion", False)),
            float(sig.get("volume_expansion_mult", 1.2)),
            str(risk.get("stop_mode", "breakout_candle_low")),
            float(risk["target_r"]),
            nz(risk.get("max_hold_minutes")),
        )
