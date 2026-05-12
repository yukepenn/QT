"""Multi-day level trap — long-only MVP (distinct from prior_day_level_trap anchors)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numba import njit

from src.backtest.constants import TM_FIXED_PX, TM_FIXED_R, TM_NONE
from src.strategies.strategy._atr_helpers import atr_series
from src.strategies.strategy.base import BaseStrategy, init_standard_signal_columns
from src.strategies.strategy.fast_utils import (
    apply_min_risk_filter_df,
    apply_min_risk_filter_numba_kernel,
    get_min_risk_per_share,
    past_any_bool_in_prior_fw_session,
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
class MultiDayTrapContext:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    level: np.ndarray
    vwap: np.ndarray
    close_location: np.ndarray
    prev_high: np.ndarray
    prev_close: np.ndarray
    atr: np.ndarray
    past_pierce: np.ndarray
    roll_lo: np.ndarray


@njit(cache=True)
def _md_trap_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    close: np.ndarray,
    low: np.ndarray,
    lv: np.ndarray,
    vw: np.ndarray,
    cloc: np.ndarray,
    ph: np.ndarray,
    pc: np.ndarray,
    atr: np.ndarray,
    past_pi: np.ndarray,
    roll_lo: np.ndarray,
    es: int,
    ee: int,
    confirm: int,
    min_cl: float,
    req_va: int,
    stop_mode: int,
    atr_buf: float,
    tgt_mode: int,
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
        if past_pi[i] == 0:
            continue
        if close[i] <= lv[i]:
            continue
        if req_va != 0 and close[i] <= vw[i]:
            continue
        ok = True
        if confirm == 1:
            ok = (low[i] < lv[i]) and (cloc[i] >= min_cl)
        elif confirm == 2:
            ok = (close[i] > ph[i]) or (close[i] > pc[i])
        else:
            ok = True
        if not ok:
            continue
        cand_long[i] = True
    fl, _ = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)
    for i in range(n):
        if not fl[i]:
            continue
        sl = roll_lo[i]
        if stop_mode != 0:
            sl = sl - atr_buf * atr[i]
        risk = close[i] - sl
        if risk <= 0:
            continue
        side[i] = 1
        valid[i] = True
        stp[i] = sl
        rsk[i] = risk
        if tgt_mode == 0:
            tgtp[i] = close[i] + target_r * risk
            tmc[i] = TM_FIXED_R
            tr[i] = target_r
        else:
            tgtp[i] = vw[i]
            tmc[i] = TM_FIXED_PX
    apply_min_risk_filter_numba_kernel(valid, side, rsk, min_risk)
    return side, valid, stp, tgtp, tmc, tr, rsk


class MultiDayLevelTrapStrategy(BaseStrategy):
    name = "multi_day_level_trap"
    supports_fast = True
    performance_tier = "A_true_context_fast_core"

    def validate_config(self, config: dict[str, Any]) -> None:
        validate_common_strategy_config(config)
        validate_long_only_mvp(config, strategy_name=self.name)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        lt = str(sig.get("level_type", "prior_3day_low"))
        if lt not in ("prior_3day_low", "prior_5day_low", "previous_week_low"):
            raise ValueError(f"signal.level_type invalid: {lt!r}")
        validate_minute_range(
            "signal.entry_start_minute",
            sig.get("entry_start_minute"),
            "signal.entry_end_minute",
            sig.get("entry_end_minute"),
        )
        validate_int_at_least("signal.fail_window_bars", sig.get("fail_window_bars", 3), 1)
        validate_nonnegative_number("signal.level_buffer_atr", sig.get("level_buffer_atr", 0.0))
        cm = str(sig.get("confirm_mode", "close_reclaim"))
        if cm not in ("close_reclaim", "wick_reclaim", "momentum_turn"):
            raise ValueError(f"signal.confirm_mode invalid: {cm!r}")
        sm = str(risk.get("stop_mode", "failed_extreme"))
        if sm not in ("failed_extreme", "atr_buffered_extreme"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        tm = str(risk.get("target_mode", "fixed_r"))
        if tm not in ("fixed_r", "vwap"):
            raise ValueError(f"risk.target_mode invalid: {tm!r}")
        if tm == "fixed_r":
            validate_positive_number("risk.target_r", risk.get("target_r", 1.0))
        validate_nonnegative_number("risk.atr_buffer", risk.get("atr_buffer", 0.1))
        validate_int_at_least("risk.max_trades_per_day", risk.get("max_trades_per_day", 1), 1)

    def _level_col(self, config: dict[str, Any]) -> str:
        lt = str((config.get("signal") or {}).get("level_type", "prior_3day_low"))
        return lt

    def required_features(self) -> list[str]:
        return [
            "session_date",
            "minute_from_open",
            "low",
            "close",
            "vwap",
            "close_location",
            "prev_high_by_session",
            "prev_close_by_session",
            "prior_3day_low",
            "prior_5day_low",
            "previous_week_low",
            "atr_like_20",
        ]

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        sig = config.get("signal") or {}
        return (
            "multi_day_trap_ctx",
            str(sig.get("level_type", "prior_3day_low")),
            int(sig.get("fail_window_bars", 3)),
            float(sig.get("level_buffer_atr", 0.0)),
            str(sig.get("atr_column", "atr_like_20")),
        )

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> MultiDayTrapContext:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        lc = self._level_col(config)
        if lc not in work.columns:
            raise ValueError(f"{self.name}: missing level column {lc!r}")
        sig = config.get("signal") or {}
        fw = int(sig.get("fail_window_bars", 3))
        buf_atr = float(sig.get("level_buffer_atr", 0.0))
        atr = atr_series(work, config).astype(float)
        lv_raw = work[lc].astype(float)
        level = (lv_raw - buf_atr * atr).to_numpy(dtype=np.float64)
        pierce = work["low"].astype(float).to_numpy(dtype=np.float64) < level
        session_id = session_id_from_dates(work["session_date"])
        past_pi = past_any_bool_in_prior_fw_session(pierce.astype(np.int8), session_id, fw)
        roll_lo = rolling_min_by_session(work["low"].to_numpy(dtype=np.float64), session_id, fw + 5)
        return MultiDayTrapContext(
            n=len(work),
            session_id=session_id,
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=work["close"].to_numpy(dtype=np.float64),
            low=work["low"].to_numpy(dtype=np.float64),
            level=level,
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            close_location=work["close_location"].to_numpy(dtype=np.float64),
            prev_high=work["prev_high_by_session"].to_numpy(dtype=np.float64),
            prev_close=work["prev_close_by_session"].to_numpy(dtype=np.float64),
            atr=atr.to_numpy(dtype=np.float64),
            past_pierce=past_pi.astype(np.int8),
            roll_lo=roll_lo,
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, MultiDayTrapContext):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es, ee = int(sig["entry_start_minute"]), int(sig["entry_end_minute"])
        cm = str(sig.get("confirm_mode", "close_reclaim"))
        cmap = {"close_reclaim": 0, "wick_reclaim": 1, "momentum_turn": 2}
        confirm = cmap.get(cm, 0)
        min_cl = float(sig.get("min_close_location", 0.5))
        req_va = int(bool(sig.get("require_vwap_alignment", False)))
        smap = {"failed_extreme": 0, "atr_buffered_extreme": 1}
        stop_mode = smap[str(risk.get("stop_mode", "failed_extreme"))]
        tgt_mode = 0 if str(risk.get("target_mode", "fixed_r")) == "fixed_r" else 1
        target_r = float(risk.get("target_r", 1.0))
        side, valid, stp, tgtp, tmc, tr, rsk = _md_trap_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.close,
            ctx.low,
            ctx.level,
            ctx.vwap,
            ctx.close_location,
            ctx.prev_high,
            ctx.prev_close,
            ctx.atr,
            ctx.past_pierce,
            ctx.roll_lo,
            es,
            ee,
            confirm,
            min_cl,
            req_va,
            stop_mode,
            float(risk.get("atr_buffer", 0.1)),
            tgt_mode,
            target_r,
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
        out["sig_target_mode"] = np.where(arr["target_mode_code"] == TM_FIXED_R, "fixed_r", "fixed_price")
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
            str(sig.get("level_type", "prior_3day_low")),
            int(sig.get("fail_window_bars", 3)),
            float(sig.get("level_buffer_atr", 0.0)),
            str(sig.get("confirm_mode", "close_reclaim")),
            bool(sig.get("require_vwap_alignment", False)),
            str(risk.get("stop_mode", "failed_extreme")),
            str(risk.get("target_mode", "fixed_r")),
            float(risk.get("target_r", 1.0)),
            nz((config.get("backtest") or {}).get("max_hold_minutes")),
        )
