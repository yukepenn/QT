"""Bollinger squeeze + upper-band breakout — long-only MVP."""

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
class BollingerSqueezeCtx:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    vwap: np.ndarray
    upper: np.ndarray
    mid: np.ndarray
    squeeze: np.ndarray
    width_pct: np.ndarray
    ret_1m: np.ndarray
    atr: np.ndarray


@njit(cache=True)
def _bb_squeeze_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    close: np.ndarray,
    low: np.ndarray,
    vw: np.ndarray,
    upper: np.ndarray,
    mid: np.ndarray,
    sq: np.ndarray,
    wp: np.ndarray,
    ret1: np.ndarray,
    atr: np.ndarray,
    es: int,
    ee: int,
    max_wp: float,
    req_vwap: int,
    req_range: int,
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
        if sq[i] == 0:
            continue
        if not np.isnan(wp[i]) and wp[i] > max_wp:
            continue
        if close[i] <= upper[i]:
            continue
        if req_vwap != 0 and close[i] <= vw[i]:
            continue
        if req_range != 0 and ret1[i] <= 0.0:
            continue
        cand_long[i] = True

    fl, fs = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)
    for i in range(n):
        if not fl[i]:
            continue
        if stop_mode == 0:
            sl = mid[i]
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


class BollingerSqueezeBreakoutStrategy(BaseStrategy):
    name = "bollinger_squeeze_breakout"
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
        if sm not in ("bb_mid", "breakout_candle_low", "atr_buffer"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        validate_positive_number("risk.target_r", risk.get("target_r"))

    def required_features(self) -> list[str]:
        return [
            "session_date",
            "minute_from_open",
            "close",
            "low",
            "vwap",
            "ret_1m",
            "bb_mid_20",
            "bb_mid_30",
            "bb_upper_20_1.5",
            "bb_upper_20_2.0",
            "bb_upper_30_1.5",
            "bb_upper_30_2.0",
            "bb_squeeze_20_1.5_60",
            "bb_squeeze_20_1.5_120",
            "bb_squeeze_20_2.0_60",
            "bb_squeeze_20_2.0_120",
            "bb_squeeze_30_1.5_60",
            "bb_squeeze_30_2.0_60",
            "bb_width_percentile_20_1.5_60",
            "bb_width_percentile_20_1.5_120",
            "bb_width_percentile_20_2.0_60",
            "bb_width_percentile_30_2.0_60",
            "atr_like_20",
        ]

    def _cols(self, config: dict[str, Any]) -> tuple[str, str, str, str]:
        feat = config.get("features") or {}
        w = int(feat.get("bb_window", 20))
        std = float(feat.get("bb_std", 2.0))
        lb = int(feat.get("bandwidth_lookback", 60))
        return (
            f"bb_upper_{w}_{std}",
            f"bb_mid_{w}",
            f"bb_squeeze_{w}_{std}_{lb}",
            f"bb_width_percentile_{w}_{std}_{lb}",
        )

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        return ("bb_sq_ctx",) + self._cols(config)

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> BollingerSqueezeCtx:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        u, m, s, p = self._cols(config)
        ret1m = work["ret_1m"].to_numpy(dtype=np.float64)
        return BollingerSqueezeCtx(
            n=len(work),
            session_id=session_id_from_dates(work["session_date"]),
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=work["close"].to_numpy(dtype=np.float64),
            low=work["low"].to_numpy(dtype=np.float64),
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            upper=work[u].to_numpy(dtype=np.float64),
            mid=work[m].to_numpy(dtype=np.float64),
            squeeze=work[s].to_numpy(dtype=np.int8),
            width_pct=work[p].to_numpy(dtype=np.float64),
            ret_1m=ret1m,
            atr=atr_series(work, config).to_numpy(dtype=np.float64),
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, BollingerSqueezeCtx):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es = int(sig["entry_start_minute"])
        ee = int(sig["entry_end_minute"])
        max_wp = float(sig.get("max_bandwidth_percentile", 0.25))
        req_vwap = int(bool(sig.get("require_vwap_side", False)))
        req_range = int(bool(sig.get("require_range_expansion", False)))
        sm = str(risk.get("stop_mode", "breakout_candle_low"))
        stop_mode = 0 if sm == "bb_mid" else (1 if sm == "breakout_candle_low" else 2)
        atr_buf = float(risk.get("atr_buffer_mult", 0.5))
        target_r = float(risk["target_r"])
        max_tr = int(risk.get("max_trades_per_day", 1))
        min_risk = get_min_risk_per_share(config)
        side, valid, stp, tgtp, tmc, tr, rsk = _bb_squeeze_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.close,
            ctx.low,
            ctx.vwap,
            ctx.upper,
            ctx.mid,
            ctx.squeeze,
            ctx.width_pct,
            ctx.ret_1m,
            ctx.atr,
            es,
            ee,
            max_wp,
            req_vwap,
            req_range,
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
        out.loc[out["sig_valid"], "sig_reason"] = "bollinger_squeeze_breakout_long"
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
            int(feat.get("bandwidth_lookback", 60)),
            float(sig.get("max_bandwidth_percentile", 0.25)),
            bool(sig.get("require_vwap_side", False)),
            bool(sig.get("require_range_expansion", False)),
            str(risk.get("stop_mode", "breakout_candle_low")),
            float(risk.get("atr_buffer_mult", 0.5)),
            float(risk["target_r"]),
            nz(risk.get("max_hold_minutes")),
        )
