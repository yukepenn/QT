"""Gap acceptance / failure — true Numba fast core."""

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
    rolling_min_by_session,
    session_id_from_dates,
    thin_first_signal_per_session_numba,
)


@dataclass(frozen=True)
class GapAfContext:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    open_px: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    session_open: np.ndarray
    prior_day_close: np.ndarray
    gap_prior_range_norm: np.ndarray
    vwap: np.ndarray
    rolling_high_3_prior: np.ndarray
    atr: np.ndarray
    roll_lo10: np.ndarray
    roll_lo20: np.ndarray


@njit(cache=True)
def _gap_af_numba(
    n: int,
    session_id: np.ndarray,
    minute: np.ndarray,
    close: np.ndarray,
    low: np.ndarray,
    so: np.ndarray,
    pdc: np.ndarray,
    gpn: np.ndarray,
    vw: np.ndarray,
    rh3: np.ndarray,
    atr: np.ndarray,
    rl10: np.ndarray,
    rl20: np.ndarray,
    es: int,
    ee: int,
    mode_acc: int,
    min_norm: float,
    min_gap_atr: float,
    max_gap_atr: float,
    req_vw: int,
    confirm: int,
    hold_m: int,
    req_hold: int,
    stop_mode: int,
    open_buf: float,
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
        hc = True
        if req_hold != 0 and minute[i] < hold_m:
            hc = False
        if not hc:
            continue
        if minute[i] < es or minute[i] > ee:
            continue
        if min_gap_atr >= 0.0 or max_gap_atr >= 0.0:
            ga = so[i] - pdc[i]
            if atr[i] <= 0:
                continue
            gatr = math.fabs(ga) / atr[i]
            if min_gap_atr >= 0.0 and gatr < min_gap_atr:
                continue
            if max_gap_atr >= 0.0 and gatr > max_gap_atr:
                continue
        base = False
        if mode_acc != 0:
            if not (so[i] > pdc[i] and gpn[i] >= min_norm):
                continue
            base = (close[i] > pdc[i]) or (close[i] > so[i])
            if req_vw != 0:
                base = base and (close[i] > vw[i])
            if confirm == 0:
                base = base and (close[i] > rh3[i])
            elif confirm == 1:
                base = base and (close[i] > so[i])
            else:
                base = base and (close[i] > vw[i])
        else:
            if not (so[i] < pdc[i] and gpn[i] <= -min_norm):
                continue
            base = (close[i] > so[i]) or (close[i] > vw[i])
        if base:
            cand_long[i] = True
    fl, fs = thin_first_signal_per_session_numba(cand_long, cand_short, session_id, max_tr)
    for i in range(n):
        if not fl[i]:
            continue
        if stop_mode == 0:
            sl = rl10[i]
        elif stop_mode == 1:
            sl = so[i] - open_buf * atr[i]
        else:
            sl = rl20[i]
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


class GapAcceptanceFailureStrategy(BaseStrategy):
    """Gap acceptance / failure MVP: long-only signals (both gap-up and gap-down branches)."""

    name = "gap_acceptance_failure"
    supports_fast = True
    performance_tier = "A_true_context_fast_core"

    def validate_config(self, config: dict[str, Any]) -> None:
        validate_common_strategy_config(config)
        validate_long_only_mvp(config, strategy_name=self.name)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        feat = config.get("features") or {}
        mode = str(sig.get("mode", "gap_acceptance"))
        if mode not in ("gap_acceptance", "gap_failure"):
            raise ValueError(f"signal.mode must be gap_acceptance or gap_failure, got {mode!r}")
        validate_minute_range(
            "signal.entry_start_minute",
            sig.get("entry_start_minute"),
            "signal.entry_end_minute",
            sig.get("entry_end_minute"),
        )
        validate_nonnegative_number("signal.min_gap_norm", sig.get("min_gap_norm", 0.3))
        if sig.get("min_gap_size_atr") is not None:
            validate_nonnegative_number("signal.min_gap_size_atr", sig.get("min_gap_size_atr"))
        if sig.get("max_gap_size_atr") is not None:
            validate_nonnegative_number("signal.max_gap_size_atr", sig.get("max_gap_size_atr"))
        if sig.get("min_gap_size_atr") is not None and sig.get("max_gap_size_atr") is not None:
            if float(sig["max_gap_size_atr"]) <= float(sig["min_gap_size_atr"]):
                raise ValueError("signal.max_gap_size_atr must be > signal.min_gap_size_atr")
        confirm = str(sig.get("confirm_mode", "break_pullback"))
        if confirm not in ("break_pullback", "reclaim_open", "reclaim_vwap"):
            raise ValueError(f"signal.confirm_mode invalid: {confirm!r}")
        stop_mode = str(risk.get("stop_mode", "pullback_extreme"))
        if stop_mode not in ("pullback_extreme", "session_open_buffer", "failed_extreme"):
            raise ValueError(f"risk.stop_mode invalid: {stop_mode!r}")
        validate_positive_number("risk.target_r", risk.get("target_r"))
        validate_nonnegative_number("risk.open_buffer_atr", risk.get("open_buffer_atr", 0.1))
        validate_int_at_least("risk.max_trades_per_day", risk.get("max_trades_per_day", 1), 1)
        validate_int_at_least("features.opening_hold_minutes", feat.get("opening_hold_minutes", 10), 0)
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
            "open",
            "session_open",
            "prior_day_close",
            "gap_prior_range_norm",
            "vwap",
            "rolling_high_3_prior",
            "atr_like_15",
        ]

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        sig = config.get("signal") or {}
        feat = config.get("features") or {}
        return (
            "gap_af_ctx",
            str(sig.get("mode", "gap_acceptance")),
            int(feat.get("opening_hold_minutes", 10)),
            str(sig.get("atr_column", "atr_like_15")),
        )

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> GapAfContext:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        session_id = session_id_from_dates(work["session_date"])
        low = work["low"].to_numpy(dtype=np.float64)
        rl10 = rolling_min_by_session(low, session_id, 10)
        rl20 = rolling_min_by_session(low, session_id, 20)
        atr = atr_series(work, config).to_numpy(dtype=np.float64)
        return GapAfContext(
            n=len(work),
            session_id=session_id,
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            open_px=work["open"].to_numpy(dtype=np.float64),
            high=work["high"].to_numpy(dtype=np.float64),
            low=low,
            close=work["close"].to_numpy(dtype=np.float64),
            session_open=work["session_open"].to_numpy(dtype=np.float64),
            prior_day_close=work["prior_day_close"].to_numpy(dtype=np.float64),
            gap_prior_range_norm=work["gap_prior_range_norm"].to_numpy(dtype=np.float64),
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            rolling_high_3_prior=work["rolling_high_3_prior"].to_numpy(dtype=np.float64),
            atr=atr,
            roll_lo10=rl10,
            roll_lo20=rl20,
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, GapAfContext):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        feat = config.get("features") or {}
        risk = config.get("risk") or {}
        mode = str(sig.get("mode", "gap_acceptance"))
        es = int(sig["entry_start_minute"])
        ee = int(sig["entry_end_minute"])
        min_norm = float(sig.get("min_gap_norm", 0.3))
        # Backward-compatible alias: require_vwap_context (prefer it if present).
        req_vw_raw = sig.get("require_vwap_context")
        if req_vw_raw is None:
            req_vw_raw = sig.get("require_vwap_side", False)
        req_vw = int(bool(req_vw_raw))
        min_gap_atr = float(sig.get("min_gap_size_atr")) if sig.get("min_gap_size_atr") is not None else -1.0
        max_gap_atr = float(sig.get("max_gap_size_atr")) if sig.get("max_gap_size_atr") is not None else -1.0
        confirm = str(sig.get("confirm_mode", "break_pullback"))
        hold_m = int(feat.get("opening_hold_minutes", 10))
        req_hold = int(bool(sig.get("require_open_hold", True)))
        stop_mode = str(risk.get("stop_mode", "pullback_extreme"))
        open_buf = float(risk.get("open_buffer_atr", 0.1))
        target_r = float(risk["target_r"])
        max_tr = int(risk.get("max_trades_per_day", 1))
        min_risk = get_min_risk_per_share(config)
        mode_acc = 1 if mode == "gap_acceptance" else 0
        cmap = {"break_pullback": 0, "reclaim_open": 1, "reclaim_vwap": 2}
        ci = cmap.get(confirm, 0)
        smap = {"pullback_extreme": 0, "session_open_buffer": 1, "failed_extreme": 2}
        sm = smap.get(stop_mode, 0)
        side, valid, stp, tgtp, tmc, tr, rsk = _gap_af_numba(
            ctx.n,
            ctx.session_id,
            ctx.minute,
            ctx.close,
            ctx.low,
            ctx.session_open,
            ctx.prior_day_close,
            ctx.gap_prior_range_norm,
            ctx.vwap,
            ctx.rolling_high_3_prior,
            ctx.atr,
            ctx.roll_lo10,
            ctx.roll_lo20,
            es,
            ee,
            mode_acc,
            min_norm,
            min_gap_atr,
            max_gap_atr,
            req_vw,
            ci,
            hold_m,
            req_hold,
            sm,
            open_buf,
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
        sig = config.get("signal") or {}
        mode = str(sig.get("mode", "gap_acceptance"))
        out.loc[out["sig_valid"], "sig_reason"] = f"gap_{mode}"
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
            str(sig.get("mode", "gap_acceptance")),
            int(sig["entry_start_minute"]),
            int(sig["entry_end_minute"]),
            float(sig.get("min_gap_norm", 0.3)),
            bool(sig.get("require_vwap_context")) if sig.get("require_vwap_context") is not None else bool(sig.get("require_vwap_side", False)),
            (float(sig.get("min_gap_size_atr")) if sig.get("min_gap_size_atr") is not None else None),
            (float(sig.get("max_gap_size_atr")) if sig.get("max_gap_size_atr") is not None else None),
            str(sig.get("confirm_mode", "break_pullback")),
            int(feat.get("opening_hold_minutes", 10)),
            str(sig.get("atr_column", "atr_like_15")),
            str(risk.get("stop_mode", "pullback_extreme")),
            float(risk["target_r"]),
            float(risk.get("min_risk_per_share") or 0.0),
            nz(bt.get("max_hold_minutes")),
        )
