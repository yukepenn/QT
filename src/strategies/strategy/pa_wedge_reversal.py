"""PA wedge-bottom / three-push reversal proxy (long-only diagnostic-first)."""

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
class PaWedgeRevCtx:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    high: np.ndarray
    atr: np.ndarray
    vwap: np.ndarray
    pa_wp: np.ndarray
    pa_bear: np.ndarray
    pa_leg: np.ndarray
    bull_rev: np.ndarray
    pa_rh: np.ndarray
    pa_rl: np.ndarray
    pa_rmid: np.ndarray
    pa_rut: np.ndarray


class PaWedgeReversalStrategy(BaseStrategy):
    name = "pa_wedge_reversal"
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
        validate_nonnegative_number("signal.min_wedge_pushes", sig.get("min_wedge_pushes", 2.5))
        sm = str(risk.get("stop_mode", "signal_low"))
        if sm not in ("wedge_low", "signal_low", "atr_buffer"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        tm = str(risk.get("target_mode", "fixed_r"))
        if tm not in ("fixed_r", "vwap", "prior_swing_high"):
            raise ValueError(f"risk.target_mode invalid: {tm!r}")
        validate_positive_number("risk.target_r", risk.get("target_r", 1.45))
        validate_nonnegative_number("risk.atr_buffer_mult", risk.get("atr_buffer_mult", 0.4))

    def required_features(self) -> list[str]:
        base = [
            "session_date",
            "minute_from_open",
            "open",
            "high",
            "low",
            "close",
            "vwap",
            "bull_reversal_bar",
            "atr_like_20",
        ]
        for rw in (30, 60):
            base.extend(
                [
                    f"pa_wedge_push_count_{rw}",
                    f"pa_broad_bear_channel_score_{rw}",
                    f"pa_tight_bear_channel_score_{rw}",
                    f"pa_leg_direction_{rw}",
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
            "pa_wedge_rev",
            pa_range_window(config),
            pa_regime_window(config),
            float(sig.get("min_wedge_pushes", 2.5)),
            float(sig.get("bear_context_min", 0.18)),
            str(sig.get("atr_column", "atr_like_20")),
        )

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> PaWedgeRevCtx:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        rw = pa_range_window(config)
        ac = atr_col_name(config)
        if ac not in work.columns:
            raise ValueError(f"{self.name}: missing {ac!r}")
        return PaWedgeRevCtx(
            n=len(work),
            session_id=session_id_from_dates(work["session_date"]),
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=work["close"].to_numpy(dtype=np.float64),
            low=work["low"].to_numpy(dtype=np.float64),
            high=work["high"].to_numpy(dtype=np.float64),
            atr=atr_series(work, config).to_numpy(dtype=np.float64),
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            pa_wp=work[f"pa_wedge_push_count_{rw}"].to_numpy(dtype=np.float64),
            pa_bear=(
                work[f"pa_broad_bear_channel_score_{rw}"] + work[f"pa_tight_bear_channel_score_{rw}"]
            ).to_numpy(dtype=np.float64),
            pa_leg=work[f"pa_leg_direction_{rw}"].to_numpy(dtype=np.int8),
            bull_rev=work["bull_reversal_bar"].to_numpy(dtype=np.int8),
            pa_rh=work[f"pa_range_high_{rw}"].to_numpy(dtype=np.float64),
            pa_rl=work[f"pa_range_low_{rw}"].to_numpy(dtype=np.float64),
            pa_rmid=work[f"pa_range_mid_{rw}"].to_numpy(dtype=np.float64),
            pa_rut=work[f"pa_range_upper_third_{rw}"].to_numpy(dtype=np.float64),
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, PaWedgeRevCtx):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es, ee = int(sig["entry_start_minute"]), int(sig["entry_end_minute"])
        min_wp = float(sig.get("min_wedge_pushes", 2.5))
        bear_min = float(sig.get("bear_context_min", 0.18))

        n = ctx.n
        cand = np.zeros(n, dtype=np.bool_)
        for i in range(n):
            if ctx.minute[i] < es or ctx.minute[i] > ee:
                continue
            if not math.isfinite(ctx.pa_wp[i]) or ctx.pa_wp[i] < min_wp:
                continue
            if not math.isfinite(ctx.pa_bear[i]) or ctx.pa_bear[i] < bear_min:
                continue
            if ctx.pa_leg[i] > 0:
                continue
            if ctx.bull_rev[i] == 0:
                continue
            cand[i] = True

        sm = str(risk.get("stop_mode", "signal_low"))
        if sm == "wedge_low":
            sm = "signal_low"

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
            stop_mode=sm,
            target_mode=str(risk.get("target_mode", "fixed_r")),
            target_r=float(risk.get("target_r", 1.45)),
            atr_buf_mult=float(risk.get("atr_buffer_mult", 0.4)),
            range_low=ctx.pa_rl,
            range_mid=ctx.pa_rmid,
            range_high=ctx.pa_rh,
            upper_third=ctx.pa_rut,
            vwap=ctx.vwap,
        )

    def generate_signal_arrays(self, df: pd.DataFrame, config: dict[str, Any]) -> dict[str, Any]:
        return self.generate_signal_arrays_from_context(self.prepare_signal_context(df, config), config)

    def generate_signals(self, df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        arr = self.generate_signal_arrays_from_context(self.prepare_signal_context(df, config), config)
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
            float(sig.get("min_wedge_pushes", 2.5)),
            float(sig.get("bear_context_min", 0.18)),
            str(risk.get("stop_mode", "signal_low")),
            str(risk.get("target_mode", "fixed_r")),
            float(risk.get("target_r", 1.45)),
            nz((config.get("backtest") or {}).get("max_hold_minutes")),
        )
