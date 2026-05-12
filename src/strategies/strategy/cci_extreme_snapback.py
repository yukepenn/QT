"""CCI extreme snapback — long-only MVP."""

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
    recent_any_bool_in_window_session,
    rolling_max_by_session_prior_exclusive,
    rolling_min_by_session,
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
class CciSnapContext:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    cci: np.ndarray
    vwap: np.ndarray
    atr: np.ndarray
    past_os: np.ndarray
    hh3_prior: np.ndarray


@njit(cache=True)
def _cci_snap_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    close: np.ndarray,
    low: np.ndarray,
    cci: np.ndarray,
    vw: np.ndarray,
    atr: np.ndarray,
    past_os: np.ndarray,
    hh3_prior: np.ndarray,
    es: int,
    ee: int,
    os_lvl: float,
    trig: int,
    req_pc: int,
    req_vwap: int,
    stop_mode: int,
    swing_lb: int,
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
        if past_os[i] == 0:
            continue
        if trig == 0:
            ok = cci[i - 1] <= os_lvl and cci[i] > os_lvl
        else:
            ok = cci[i - 1] <= 0.0 and cci[i] > 0.0
        if not ok:
            continue
        if req_pc != 0 and not (close[i] > hh3_prior[i]):
            continue
        if req_vwap != 0 and not (close[i] > vw[i]):
            continue
        cand_long[i] = True
    fl, _ = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)
    roll_lo = rolling_min_by_session(low, session_id, swing_lb)
    for i in range(n):
        if not fl[i]:
            continue
        if stop_mode == 0:
            sl = low[i]
        elif stop_mode == 1:
            sl = roll_lo[i]
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


class CciExtremeSnapbackStrategy(BaseStrategy):
    name = "cci_extreme_snapback"
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
        validate_int_at_least("features.cci_window", feat.get("cci_window", 20), 3)
        validate_int_at_least("features.swing_lookback", feat.get("swing_lookback", 10), 3)
        tm = str(sig.get("trigger_mode", "cross_above_oversold"))
        if tm not in ("cross_above_oversold", "cross_above_zero"):
            raise ValueError(f"signal.trigger_mode invalid: {tm!r}")
        sm = str(risk.get("stop_mode", "signal_candle_low"))
        if sm not in ("signal_candle_low", "swing_low", "atr_buffer"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        validate_positive_number("risk.target_r", risk.get("target_r"))
        validate_nonnegative_number("risk.atr_buffer_mult", risk.get("atr_buffer_mult", 0.35))

    def _cci_col(self, config: dict[str, Any]) -> str:
        w = int((config.get("features") or {}).get("cci_window", 20))
        return f"cci_{w}"

    def required_features(self) -> list[str]:
        return [
            "session_date",
            "minute_from_open",
            "low",
            "close",
            "vwap",
            "cci_14",
            "cci_20",
            "cci_30",
            "rolling_high_3_prior",
            "atr_like_20",
        ]

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        feat = config.get("features") or {}
        sig = config.get("signal") or {}
        return (
            "cci_snap_ctx",
            int(feat.get("cci_window", 20)),
            int(feat.get("swing_lookback", 10)),
            float(sig.get("oversold_level", -150)),
            str(sig.get("trigger_mode", "cross_above_oversold")),
            str(sig.get("atr_column", "atr_like_20")),
        )

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> CciSnapContext:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        cc = self._cci_col(config)
        if cc not in work.columns:
            raise ValueError(f"{self.name}: missing {cc!r}")
        feat = config.get("features") or {}
        sig = config.get("signal") or {}
        os_lvl = float(sig.get("oversold_level", -150))
        lb = int(feat.get("swing_lookback", 10))
        pred_os = (work[cc].astype(float) < os_lvl).to_numpy()
        session_id = session_id_from_dates(work["session_date"])
        past_os = recent_any_bool_in_window_session(pred_os.astype(np.int8), session_id, lb)
        hh3 = rolling_max_by_session_prior_exclusive(work["high"].to_numpy(dtype=np.float64), session_id, 3)
        return CciSnapContext(
            n=len(work),
            session_id=session_id,
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=work["close"].to_numpy(dtype=np.float64),
            low=work["low"].to_numpy(dtype=np.float64),
            cci=work[cc].to_numpy(dtype=np.float64),
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            atr=atr_series(work, config).to_numpy(dtype=np.float64),
            past_os=past_os.astype(np.int8),
            hh3_prior=hh3,
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, CciSnapContext):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        feat = config.get("features") or {}
        es, ee = int(sig["entry_start_minute"]), int(sig["entry_end_minute"])
        os_lvl = float(sig.get("oversold_level", -150))
        tm = str(sig.get("trigger_mode", "cross_above_oversold"))
        trig = 0 if tm == "cross_above_oversold" else 1
        req_pc = int(bool(sig.get("require_price_confirmation", True)))
        req_vwap = int(bool(sig.get("require_vwap_filter", False)))
        smap = {"signal_candle_low": 0, "swing_low": 1, "atr_buffer": 2}
        stop_mode = smap[str(risk.get("stop_mode", "signal_candle_low"))]
        side, valid, stp, tgtp, tmc, tr, rsk = _cci_snap_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.close,
            ctx.low,
            ctx.cci,
            ctx.vwap,
            ctx.atr,
            ctx.past_os,
            ctx.hh3_prior,
            es,
            ee,
            os_lvl,
            trig,
            req_pc,
            req_vwap,
            stop_mode,
            int(feat.get("swing_lookback", 10)),
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
            int(feat.get("cci_window", 20)),
            int(feat.get("swing_lookback", 10)),
            float(sig.get("oversold_level", -150)),
            str(sig.get("trigger_mode", "cross_above_oversold")),
            bool(sig.get("require_price_confirmation", True)),
            bool(sig.get("require_vwap_filter", False)),
            str(risk.get("stop_mode", "signal_candle_low")),
            float(risk["target_r"]),
            nz((config.get("backtest") or {}).get("max_hold_minutes")),
        )
