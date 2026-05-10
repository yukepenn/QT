"""Generic rolling-range breakout pullback (not ORB); long-only MVP."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from src.strategies.strategy._atr_helpers import atr_series
from src.strategies.strategy.base import BaseStrategy
from src.strategies.strategy.fast_utils import session_id_from_dates
from src.strategies.strategy.pa_batch_a_utils import (
    atr_col_name,
    finalize_long_signals_df,
    pa_range_window,
    pa_regime_window,
    signals_df_from_arrays,
)
from src.utils.config_validation import (
    validate_common_strategy_config,
    validate_long_only_mvp,
    validate_minute_range,
    validate_nonnegative_number,
    validate_positive_number,
)


@dataclass(frozen=True)
class PaGenBrkCtx:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    high: np.ndarray
    atr: np.ndarray
    bo_up: np.ndarray
    pa_rh: np.ndarray
    pa_pd: np.ndarray
    pa_ftu: np.ndarray
    pa_ol: np.ndarray
    bull_rev: np.ndarray
    pa_rl: np.ndarray
    pa_rmid: np.ndarray
    pa_rut: np.ndarray


class PaGenericBreakoutPullbackStrategy(BaseStrategy):
    name = "pa_generic_breakout_pullback"
    supports_fast = True
    performance_tier = "B_context_fast"

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
        validate_nonnegative_number(
            "signal.pullback_test_atr", sig.get("pullback_test_atr", 0.35)
        )
        sm = str(risk.get("stop_mode", "pullback_low"))
        if sm not in ("pullback_low", "breakout_point_buffer", "atr_buffer"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        tm = str(risk.get("target_mode", "fixed_r"))
        if tm not in ("fixed_r", "prior_high"):
            raise ValueError(f"risk.target_mode invalid: {tm!r}")
        validate_positive_number("risk.target_r", risk.get("target_r", 1.45))
        validate_nonnegative_number(
            "risk.atr_buffer_mult", risk.get("atr_buffer_mult", 0.35)
        )

    def required_features(self) -> list[str]:
        regw = 30
        base = [
            "session_date",
            "minute_from_open",
            "open",
            "high",
            "low",
            "close",
            "bull_reversal_bar",
            "atr_like_20",
            f"pa_overlap_score_{regw}",
        ]
        for rw in (30, 60):
            base.extend(
                [
                    f"pa_breakout_up_{rw}",
                    f"pa_prior_high_{rw}",
                    f"pa_pullback_depth_atr_{rw}",
                    f"pa_followthrough_up_{rw}",
                    f"pa_range_high_{rw}",
                    f"pa_range_low_{rw}",
                    f"pa_range_mid_{rw}",
                    f"pa_range_upper_third_{rw}",
                ]
            )
        return base

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        sig = config.get("signal") or {}
        return (
            "pa_gen_brk_pb",
            pa_range_window(config),
            pa_regime_window(config),
            str(sig.get("atr_column", "atr_like_20")),
        )

    def prepare_signal_context(
        self, df: pd.DataFrame, config: dict[str, Any]
    ) -> PaGenBrkCtx:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        rw = pa_range_window(config)
        regw = pa_regime_window(config)
        ac = atr_col_name(config)
        if ac not in work.columns:
            raise ValueError(f"{self.name}: missing {ac!r}")
        ol_col = f"pa_overlap_score_{regw}"
        if ol_col not in work.columns:
            raise ValueError(f"{self.name}: missing {ol_col!r}")
        return PaGenBrkCtx(
            n=len(work),
            session_id=session_id_from_dates(work["session_date"]),
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=work["close"].to_numpy(dtype=np.float64),
            low=work["low"].to_numpy(dtype=np.float64),
            high=work["high"].to_numpy(dtype=np.float64),
            atr=atr_series(work, config).to_numpy(dtype=np.float64),
            bo_up=work[f"pa_breakout_up_{rw}"].to_numpy(dtype=np.int8),
            pa_rh=work[f"pa_prior_high_{rw}"].to_numpy(dtype=np.float64),
            pa_pd=work[f"pa_pullback_depth_atr_{rw}"].to_numpy(dtype=np.float64),
            pa_ftu=work[f"pa_followthrough_up_{rw}"].to_numpy(dtype=np.int8),
            pa_ol=work[ol_col].to_numpy(dtype=np.float64),
            bull_rev=work["bull_reversal_bar"].to_numpy(dtype=np.int8),
            pa_rl=work[f"pa_range_low_{rw}"].to_numpy(dtype=np.float64),
            pa_rmid=work[f"pa_range_mid_{rw}"].to_numpy(dtype=np.float64),
            pa_rut=work[f"pa_range_upper_third_{rw}"].to_numpy(dtype=np.float64),
        )

    def generate_signal_arrays_from_context(
        self, ctx: Any, config: dict[str, Any]
    ) -> dict[str, Any]:
        if not isinstance(ctx, PaGenBrkCtx):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es, ee = int(sig["entry_start_minute"]), int(sig["entry_end_minute"])
        lb = max(2, int(sig.get("recent_breakout_lookback", 6)))
        test_w = float(sig.get("pullback_test_atr", 0.35))
        min_pd = float(sig.get("min_pullback_depth_atr", 0.12))
        ol_max = float(sig.get("overlap_score_max", 0.62))
        need_ft = bool(sig.get("require_followthrough_recent", True))

        n = ctx.n
        recent_bo = np.zeros(n, dtype=np.int8)
        recent_ft = np.zeros(n, dtype=np.int8)
        for i in range(n):
            j0 = max(0, i - lb)
            if np.any(ctx.bo_up[j0:i] != 0):
                recent_bo[i] = 1
            if np.any(ctx.pa_ftu[j0:i] != 0):
                recent_ft[i] = 1

        cand = np.zeros(n, dtype=np.bool_)
        for i in range(n):
            if ctx.minute[i] < es or ctx.minute[i] > ee:
                continue
            if recent_bo[i] == 0:
                continue
            if need_ft and recent_ft[i] == 0:
                continue
            if not math.isfinite(ctx.pa_rh[i]) or not math.isfinite(ctx.atr[i]):
                continue
            lo_b = ctx.pa_rh[i] - test_w * ctx.atr[i]
            hi_b = ctx.pa_rh[i] + 0.25 * ctx.atr[i]
            if ctx.close[i] < lo_b or ctx.close[i] > hi_b:
                continue
            if not math.isfinite(ctx.pa_pd[i]) or ctx.pa_pd[i] < min_pd:
                continue
            if math.isfinite(ctx.pa_ol[i]) and ctx.pa_ol[i] > ol_max:
                continue
            if ctx.bull_rev[i] == 0:
                continue
            cand[i] = True

        return finalize_long_signals_df(
            pd.DataFrame({"_i": np.arange(ctx.n)}),
            strategy_name=self.name,
            config=config,
            cand_long=cand,
            session_id=ctx.session_id,
            close=ctx.close,
            low=ctx.low,
            high=ctx.high,
            atr=ctx.atr,
            stop_mode=str(risk.get("stop_mode", "pullback_low")),
            target_mode=str(risk.get("target_mode", "fixed_r")),
            target_r=float(risk.get("target_r", 1.45)),
            atr_buf_mult=float(risk.get("atr_buffer_mult", 0.35)),
            range_low=ctx.pa_rl,
            range_mid=ctx.pa_rmid,
            range_high=ctx.pa_rh,
            upper_third=ctx.pa_rut,
        )

    def generate_signal_arrays(
        self, df: pd.DataFrame, config: dict[str, Any]
    ) -> dict[str, Any]:
        return self.generate_signal_arrays_from_context(
            self.prepare_signal_context(df, config), config
        )

    def generate_signals(
        self, df: pd.DataFrame, config: dict[str, Any]
    ) -> pd.DataFrame:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        arr = self.generate_signal_arrays_from_context(
            self.prepare_signal_context(df, config), config
        )
        return signals_df_from_arrays(work, self.name, arr, config)

    def normalized_param_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        feat = config.get("features") or {}
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}

        def nz(x: Any) -> Any:
            if isinstance(x, float) and math.isnan(x):
                return None
            return x

        return (
            int(feat.get("pa_range_window", 60)),
            int(feat.get("pa_regime_window", 30)),
            int(sig.get("recent_breakout_lookback", 6)),
            float(sig.get("pullback_test_atr", 0.35)),
            float(sig.get("min_pullback_depth_atr", 0.12)),
            float(sig.get("overlap_score_max", 0.62)),
            bool(sig.get("require_followthrough_recent", True)),
            str(risk.get("stop_mode", "pullback_low")),
            str(risk.get("target_mode", "fixed_r")),
            float(risk.get("target_r", 1.45)),
            int(sig.get("entry_start_minute", 60)),
            int(sig.get("entry_end_minute", 270)),
            float(risk.get("atr_buffer_mult", 0.35)),
            int(risk.get("max_trades_per_day", 1)),
            nz(risk.get("min_risk_per_share")),
            nz((config.get("backtest") or {}).get("max_hold_minutes")),
        )
