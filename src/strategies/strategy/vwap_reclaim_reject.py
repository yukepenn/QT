"""VWAP reclaim — true Numba fast core."""

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
    validate_nonnegative_number,
    validate_positive_number,
)
from src.strategies.strategy.fast_utils import (
    apply_min_risk_filter_df,
    apply_min_risk_filter_numba_kernel,
    get_min_risk_per_share,
    rolling_max_by_session_prior_exclusive,
    rolling_min_by_session,
    rolling_sum_by_session_int,
    session_id_from_dates,
    thin_first_signal_per_session_numba,
)


@dataclass(frozen=True)
class VwapReclaimContext:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    high: np.ndarray
    vwap: np.ndarray
    prev_high: np.ndarray
    prev_close: np.ndarray
    atr: np.ndarray
    wrong_stack: np.ndarray
    hh3_prior: np.ndarray
    roll_lo10: np.ndarray
    volume_ratio_20: np.ndarray


@njit(cache=True)
def _vwap_reclaim_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    close: np.ndarray,
    low: np.ndarray,
    vw: np.ndarray,
    atr: np.ndarray,
    wstack: np.ndarray,
    hh3: np.ndarray,
    rl10: np.ndarray,
    volr: np.ndarray,
    ph: np.ndarray,
    pc: np.ndarray,
    es: int,
    ee: int,
    mb: float,
    confirm: int,
    req_vs: int,
    min_vm: float,
    stop_mode: int,
    buf: float,
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
        if wstack[i] < mb:
            continue
        if close[i] <= vw[i]:
            continue
        if req_vs != 0 and volr[i] < min_vm:
            continue
        ok = True
        if confirm == 1:
            ok = close[i] > hh3[i]
        elif confirm == 2:
            ok = (close[i] > pc[i]) and (close[i] > ph[i])
        if not ok:
            continue
        cand_long[i] = True
    fl, fs = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)
    for i in range(n):
        if not fl[i]:
            continue
        if stop_mode == 0:
            sl = low[i]
        elif stop_mode == 1:
            sl = vw[i] - buf * atr[i]
        else:
            sl = rl10[i]
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


class VwapReclaimRejectStrategy(BaseStrategy):
    """VWAP reclaim continuation — long-only MVP."""

    name = "vwap_reclaim_reject"
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
        validate_int_at_least("signal.min_bars_wrong_side", sig.get("min_bars_wrong_side", 10), 1)
        confirm = str(sig.get("confirm_mode", "close_reclaim"))
        if confirm not in ("close_reclaim", "break_3bar_high", "momentum_turn"):
            raise ValueError(f"signal.confirm_mode invalid: {confirm!r}")
        stop_mode = str(risk.get("stop_mode", "reclaim_candle"))
        if stop_mode not in ("reclaim_candle", "vwap_buffer", "swing_low"):
            raise ValueError(f"risk.stop_mode invalid: {stop_mode!r}")
        validate_positive_number("risk.target_r", risk.get("target_r"))
        validate_nonnegative_number("risk.vwap_buffer_atr", risk.get("vwap_buffer_atr", 0.1))
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
            "prev_high_by_session",
            "prev_close_by_session",
            "close_location",
            "volume_ratio_20",
            "atr_like_15",
        ]

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        sig = config.get("signal") or {}
        mb = int(sig.get("min_bars_wrong_side", 10))
        w = max(mb + 5, 15)
        return ("vwap_reclaim_ctx", mb, w, str(sig.get("atr_column", "atr_like_15")))

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> VwapReclaimContext:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        sig = config.get("signal") or {}
        mb = int(sig.get("min_bars_wrong_side", 10))
        W = max(mb + 5, 15)
        session_id = session_id_from_dates(work["session_date"])
        cls = work["close"].to_numpy(dtype=np.float64)
        vw = work["vwap"].to_numpy(dtype=np.float64)
        below = (cls < vw).astype(np.float64)
        wrong_stack = rolling_sum_by_session_int(below, session_id, W)
        low = work["low"].to_numpy(dtype=np.float64)
        high = work["high"].to_numpy(dtype=np.float64)
        hh3 = rolling_max_by_session_prior_exclusive(high, session_id, 3)
        rl10 = rolling_min_by_session(low, session_id, 10)
        atr = atr_series(work, config).to_numpy(dtype=np.float64)
        return VwapReclaimContext(
            n=len(work),
            session_id=session_id,
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=cls,
            low=low,
            high=high,
            vwap=vw,
            prev_high=work["prev_high_by_session"].to_numpy(dtype=np.float64),
            prev_close=work["prev_close_by_session"].to_numpy(dtype=np.float64),
            atr=atr,
            wrong_stack=wrong_stack,
            hh3_prior=hh3,
            roll_lo10=rl10,
            volume_ratio_20=work["volume_ratio_20"].to_numpy(dtype=np.float64),
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, VwapReclaimContext):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es = int(sig["entry_start_minute"])
        ee = int(sig["entry_end_minute"])
        mb = float(int(sig.get("min_bars_wrong_side", 10)))
        confirm = str(sig.get("confirm_mode", "close_reclaim"))
        req_vs = int(bool(sig.get("require_volume_surge", False)))
        min_vm = float(sig.get("min_volume_mult", 1.5))
        stop_mode = str(risk.get("stop_mode", "reclaim_candle"))
        buf = float(risk.get("vwap_buffer_atr", 0.1))
        target_r = float(risk["target_r"])
        max_tr = int(risk.get("max_trades_per_day", 1))
        min_risk = get_min_risk_per_share(config)
        cmap = {"close_reclaim": 0, "break_3bar_high": 1, "momentum_turn": 2}
        ci = cmap.get(confirm, 0)
        smap = {"reclaim_candle": 0, "vwap_buffer": 1, "swing_low": 2}
        sm = smap.get(stop_mode, 0)
        side, valid, stp, tgtp, tmc, tr, rsk = _vwap_reclaim_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.close,
            ctx.low,
            ctx.vwap,
            ctx.atr,
            ctx.wrong_stack,
            ctx.hh3_prior,
            ctx.roll_lo10,
            ctx.volume_ratio_20,
            ctx.prev_high,
            ctx.prev_close,
            es,
            ee,
            mb,
            ci,
            req_vs,
            min_vm,
            sm,
            buf,
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
        out.loc[out["sig_valid"], "sig_reason"] = "vwap_reclaim_long"
        return apply_min_risk_filter_df(out, config=config)

    def normalized_param_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        bt = config.get("backtest") or {}

        def nz(x: Any) -> Any:
            if isinstance(x, float) and math.isnan(x):
                return None
            return x

        return (
            int(sig["entry_start_minute"]),
            int(sig["entry_end_minute"]),
            int(sig.get("min_bars_wrong_side", 10)),
            str(sig.get("atr_column", "atr_like_15")),
            str(sig.get("confirm_mode", "close_reclaim")),
            bool(sig.get("require_volume_surge", False)),
            str(risk.get("stop_mode", "reclaim_candle")),
            float(risk["target_r"]),
            float(risk.get("min_risk_per_share") or 0.0),
            nz(bt.get("max_hold_minutes")),
        )
