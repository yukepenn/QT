"""Midday compression breakout — true Numba fast core."""

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
from src.utils.config_validation import (
    validate_common_strategy_config,
    validate_int_at_least,
    validate_long_only_mvp,
    validate_minute_range,
    validate_positive_number,
)
from src.strategies.strategy.fast_utils import (
    apply_min_risk_filter_df,
    apply_min_risk_filter_numba_kernel,
    get_min_risk_per_share,
    session_id_from_dates,
    thin_first_signal_per_session_numba,
)


def _compression_cols(feat: dict[str, Any], columns: pd.Index) -> tuple[str, str, str]:
    w = int(feat.get("compression_window", 30))
    rh = f"rolling_high_{w}_prior"
    rl = f"rolling_low_{w}_prior"
    rw = f"range_width_{w}"
    if rh not in columns:
        rh, rl, rw = "rolling_high_30_prior", "rolling_low_30_prior", "range_width_30"
    return rh, rl, rw


@dataclass(frozen=True)
class MiddayCompressionContext:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    vwap: np.ndarray
    volr: np.ndarray
    atr: np.ndarray
    hi_n: np.ndarray
    lo_n: np.ndarray
    rng_w: np.ndarray


@njit(cache=True)
def _midday_comp_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    close: np.ndarray,
    low: np.ndarray,
    vw: np.ndarray,
    volr: np.ndarray,
    atr: np.ndarray,
    hi_n: np.ndarray,
    lo_n: np.ndarray,
    rng_w: np.ndarray,
    es: int,
    ee: int,
    max_ra: float,
    req_dry: int,
    brk_vm: float,
    req_vw: int,
    stop_mode: int,
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
    mid = np.empty(n, dtype=np.float64)
    for i in range(n):
        mid[i] = (hi_n[i] + lo_n[i]) * 0.5
    for i in range(n):
        if minute[i] < es or minute[i] > ee:
            continue
        if rng_w[i] > max_ra * atr[i]:
            continue
        if close[i] <= hi_n[i]:
            continue
        if volr[i] < brk_vm:
            continue
        if req_dry != 0 and volr[i] > 1.0:
            continue
        if req_vw != 0 and close[i] <= vw[i]:
            continue
        cand_long[i] = True
    fl, fs = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)
    for i in range(n):
        if not fl[i]:
            continue
        if stop_mode == 0:
            sl = mid[i]
        elif stop_mode == 1:
            sl = lo_n[i]
        else:
            sl = low[i]
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


class MiddayCompressionBreakoutStrategy(BaseStrategy):
    """Midday range compression breakout — long-only MVP."""

    name = "midday_compression_breakout"
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
        validate_int_at_least("features.compression_window", feat.get("compression_window", 30), 1)
        validate_positive_number("signal.max_range_atr", sig.get("max_range_atr", 1.5))
        sm = str(risk.get("stop_mode", "range_mid"))
        if sm not in ("range_mid", "range_opposite", "breakout_candle"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
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
            "volume_ratio_20",
            "rolling_high_20_prior",
            "rolling_low_20_prior",
            "rolling_high_30_prior",
            "rolling_low_30_prior",
            "rolling_high_60_prior",
            "rolling_low_60_prior",
            "atr_like_15",
        ]

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        feat = config.get("features") or {}
        sig = config.get("signal") or {}
        return (
            "midday_comp_ctx",
            int(feat.get("compression_window", 30)),
            str(sig.get("atr_column", "atr_like_15")),
        )

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> MiddayCompressionContext:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        feat = config.get("features") or {}
        rh_c, rl_c, rw_c = _compression_cols(feat, work.columns)
        session_id = session_id_from_dates(work["session_date"])
        atr = atr_series(work, config).to_numpy(dtype=np.float64)
        return MiddayCompressionContext(
            n=len(work),
            session_id=session_id,
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=work["close"].to_numpy(dtype=np.float64),
            low=work["low"].to_numpy(dtype=np.float64),
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            volr=work["volume_ratio_20"].to_numpy(dtype=np.float64),
            atr=atr,
            hi_n=work[rh_c].to_numpy(dtype=np.float64),
            lo_n=work[rl_c].to_numpy(dtype=np.float64),
            rng_w=work[rw_c].to_numpy(dtype=np.float64),
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, MiddayCompressionContext):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es = int(sig["entry_start_minute"])
        ee = int(sig["entry_end_minute"])
        max_ra = float(sig.get("max_range_atr", 1.5))
        req_dry = int(bool(sig.get("require_volume_dryup", False)))
        brk_vm = float(sig.get("breakout_volume_mult", 1.2))
        req_vw = int(bool(sig.get("require_vwap_side", False)))
        stop_mode = str(risk.get("stop_mode", "range_mid"))
        target_r = float(risk["target_r"])
        max_tr = int(risk.get("max_trades_per_day", 1))
        min_risk = get_min_risk_per_share(config)
        smap = {"range_mid": 0, "range_opposite": 1, "breakout_candle": 2}
        sm = smap.get(stop_mode, 0)
        side, valid, stp, tgtp, tmc, tr, rsk = _midday_comp_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.close,
            ctx.low,
            ctx.vwap,
            ctx.volr,
            ctx.atr,
            ctx.hi_n,
            ctx.lo_n,
            ctx.rng_w,
            es,
            ee,
            max_ra,
            req_dry,
            brk_vm,
            req_vw,
            sm,
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
        arr = self.generate_signal_arrays_from_context(self.prepare_signal_context(df, config), config)
        out = init_standard_signal_columns(work, strategy_name=self.name, copy=True)
        out["sig_side"] = arr["side"]
        out["sig_valid"] = arr["valid"]
        out["sig_stop"] = arr["stop"]
        out["sig_target"] = arr["target_preview"]
        out["sig_target_mode"] = np.where(arr["target_mode_code"] == TM_FIXED_R, "fixed_r", "")
        out["sig_target_r"] = arr["target_r"]
        out["sig_risk_per_share"] = arr["risk_preview"]
        out.loc[out["sig_valid"], "sig_reason"] = "midday_compression_long"
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
            int(feat.get("compression_window", 30)),
            str(sig.get("atr_column", "atr_like_15")),
            int(sig["entry_start_minute"]),
            int(sig["entry_end_minute"]),
            float(sig.get("max_range_atr", 1.5)),
            bool(sig.get("require_volume_dryup", False)),
            float(sig.get("breakout_volume_mult", 1.2)),
            bool(sig.get("require_vwap_side", False)),
            str(risk.get("stop_mode", "range_mid")),
            float(risk["target_r"]),
            float(risk.get("min_risk_per_share") or 0.0),
            nz(bt.get("max_hold_minutes")),
        )
