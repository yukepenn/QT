"""PA climax / exhaustion fade reversal (long-only diagnostic-first)."""

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
class PaClimaxRevCtx:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    high: np.ndarray
    atr: np.ndarray
    vwap: np.ndarray
    pa_bear: np.ndarray
    pa_clx: np.ndarray
    pa_brexp: np.ndarray
    pa_dvw: np.ndarray
    pa_ftdn: np.ndarray
    pa_cbi: np.ndarray
    bull_rev: np.ndarray
    pa_rh: np.ndarray
    pa_rl: np.ndarray
    pa_rmid: np.ndarray
    pa_rut: np.ndarray


class PaClimaxReversalStrategy(BaseStrategy):
    name = "pa_climax_reversal"
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
            "signal.climax_score_min", sig.get("climax_score_min", 0.45)
        )
        validate_nonnegative_number(
            "signal.bar_range_expansion_min", sig.get("bar_range_expansion_min", 1.35)
        )
        sm = str(risk.get("stop_mode", "signal_low"))
        if sm not in ("climax_low", "signal_low", "atr_buffer"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        tm = str(risk.get("target_mode", "fixed_r"))
        if tm not in ("fixed_r", "vwap", "climax_mid", "range_mid"):
            raise ValueError(f"risk.target_mode invalid: {tm!r}")
        validate_positive_number("risk.target_r", risk.get("target_r", 1.35))
        validate_nonnegative_number(
            "risk.atr_buffer_mult", risk.get("atr_buffer_mult", 0.4)
        )

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
            "pa_distance_from_vwap_atr",
        ]
        for rw in (30, 60):
            base.extend(
                [
                    f"pa_tight_bear_channel_score_{rw}",
                    f"pa_broad_bear_channel_score_{rw}",
                    f"pa_climax_score_{rw}",
                    f"pa_bar_range_expansion_{rw}",
                    f"pa_followthrough_down_{rw}",
                    f"pa_close_back_inside_{rw}",
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
            "pa_climax_rev",
            pa_range_window(config),
            pa_regime_window(config),
            float(sig.get("climax_score_min", 0.45)),
            float(sig.get("bear_context_min", 0.22)),
            float(sig.get("max_dist_below_vwap_atr", -0.12)),
            str(sig.get("atr_column", "atr_like_20")),
        )

    def prepare_signal_context(
        self, df: pd.DataFrame, config: dict[str, Any]
    ) -> PaClimaxRevCtx:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        rw = pa_range_window(config)
        ac = atr_col_name(config)
        if ac not in work.columns:
            raise ValueError(f"{self.name}: missing {ac!r}")
        for c in (f"pa_climax_score_{rw}", "pa_distance_from_vwap_atr"):
            if c not in work.columns:
                raise ValueError(f"{self.name}: missing {c!r}")
        return PaClimaxRevCtx(
            n=len(work),
            session_id=session_id_from_dates(work["session_date"]),
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=work["close"].to_numpy(dtype=np.float64),
            low=work["low"].to_numpy(dtype=np.float64),
            high=work["high"].to_numpy(dtype=np.float64),
            atr=atr_series(work, config).to_numpy(dtype=np.float64),
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            pa_bear=(
                work[f"pa_tight_bear_channel_score_{rw}"]
                + work[f"pa_broad_bear_channel_score_{rw}"]
            ).to_numpy(dtype=np.float64),
            pa_clx=work[f"pa_climax_score_{rw}"].to_numpy(dtype=np.float64),
            pa_brexp=work[f"pa_bar_range_expansion_{rw}"].to_numpy(dtype=np.float64),
            pa_dvw=work["pa_distance_from_vwap_atr"].to_numpy(dtype=np.float64),
            pa_ftdn=work[f"pa_followthrough_down_{rw}"].to_numpy(dtype=np.int8),
            pa_cbi=work[f"pa_close_back_inside_{rw}"].to_numpy(dtype=np.int8),
            bull_rev=work["bull_reversal_bar"].to_numpy(dtype=np.int8),
            pa_rh=work[f"pa_range_high_{rw}"].to_numpy(dtype=np.float64),
            pa_rl=work[f"pa_range_low_{rw}"].to_numpy(dtype=np.float64),
            pa_rmid=work[f"pa_range_mid_{rw}"].to_numpy(dtype=np.float64),
            pa_rut=work[f"pa_range_upper_third_{rw}"].to_numpy(dtype=np.float64),
        )

    def generate_signal_arrays_from_context(
        self, ctx: Any, config: dict[str, Any]
    ) -> dict[str, Any]:
        if not isinstance(ctx, PaClimaxRevCtx):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es, ee = int(sig["entry_start_minute"]), int(sig["entry_end_minute"])
        clx_min = float(sig.get("climax_score_min", 0.45))
        bexp_min = float(sig.get("bar_range_expansion_min", 1.35))
        bear_min = float(sig.get("bear_context_min", 0.22))
        max_below = float(sig.get("max_dist_below_vwap_atr", -0.12))
        use_bexp = bool(sig.get("use_bar_range_expansion", True))

        n = ctx.n
        cand = np.zeros(n, dtype=np.bool_)
        for i in range(n):
            if ctx.minute[i] < es or ctx.minute[i] > ee:
                continue
            if not math.isfinite(ctx.pa_bear[i]) or ctx.pa_bear[i] < bear_min:
                continue
            clx_ok = math.isfinite(ctx.pa_clx[i]) and ctx.pa_clx[i] >= clx_min
            exp_ok = (not use_bexp) or (
                math.isfinite(ctx.pa_brexp[i]) and ctx.pa_brexp[i] >= bexp_min
            )
            if not (clx_ok or exp_ok):
                continue
            if not math.isfinite(ctx.pa_dvw[i]) or ctx.pa_dvw[i] > max_below:
                continue
            if ctx.pa_ftdn[i] != 0 and ctx.pa_cbi[i] == 0:
                continue
            if ctx.bull_rev[i] == 0:
                continue
            cand[i] = True

        sm = str(risk.get("stop_mode", "signal_low"))
        if sm == "climax_low":
            sm = "signal_low"
        tm = str(risk.get("target_mode", "fixed_r"))
        if tm == "climax_mid":
            tm = "range_mid"

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
            target_mode=tm,
            target_r=float(risk.get("target_r", 1.35)),
            atr_buf_mult=float(risk.get("atr_buffer_mult", 0.4)),
            range_low=ctx.pa_rl,
            range_mid=ctx.pa_rmid,
            range_high=ctx.pa_rh,
            upper_third=ctx.pa_rut,
            vwap=ctx.vwap,
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
            float(sig.get("climax_score_min", 0.45)),
            float(sig.get("bar_range_expansion_min", 1.35)),
            float(sig.get("bear_context_min", 0.22)),
            float(sig.get("max_dist_below_vwap_atr", -0.12)),
            bool(sig.get("use_bar_range_expansion", True)),
            str(risk.get("stop_mode", "signal_low")),
            str(risk.get("target_mode", "fixed_r")),
            float(risk.get("target_r", 1.35)),
            int(sig.get("entry_start_minute", 45)),
            int(sig.get("entry_end_minute", 270)),
            float(risk.get("atr_buffer_mult", 0.4)),
            int(risk.get("max_trades_per_day", 1)),
            nz(risk.get("min_risk_per_share")),
            nz((config.get("backtest") or {}).get("max_hold_minutes")),
        )
