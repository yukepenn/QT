"""PA trading-range buy-low / sell-high scalp (long-only MVP; not ORB/VWAP core)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from src.strategies.strategy.base import BaseStrategy
from src.strategies.strategy.pa_batch_a_utils import (
    atr_col_name,
    finalize_long_signals_df,
    pa_range_window,
    pa_regime_window,
    signals_df_from_arrays,
)
from src.strategies.strategy._atr_helpers import atr_series
from src.strategies.strategy.fast_utils import session_id_from_dates
from src.utils.config_validation import (
    validate_common_strategy_config,
    validate_long_only_mvp,
    validate_minute_range,
    validate_nonnegative_number,
    validate_positive_number,
)


@dataclass(frozen=True)
class PaTrBlsCtx:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    high: np.ndarray
    atr: np.ndarray
    pa_tr: np.ndarray
    pa_rh: np.ndarray
    pa_rl: np.ndarray
    pa_rmid: np.ndarray
    pa_rut: np.ndarray
    pa_rlt: np.ndarray
    pa_rw_atr: np.ndarray
    bull_rev: np.ndarray
    fbd: np.ndarray
    lwp: np.ndarray
    uwp: np.ndarray
    reff: np.ndarray


class PaTradingRangeBlsHsStrategy(BaseStrategy):
    name = "pa_trading_range_bls_hs"
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
        validate_nonnegative_number(
            "signal.trading_range_score_min", sig.get("trading_range_score_min", 0.35)
        )
        validate_nonnegative_number(
            "signal.min_range_width_atr", sig.get("min_range_width_atr", 0.8)
        )
        sm = str(risk.get("stop_mode", "range_low"))
        if sm not in ("range_low", "signal_low", "atr_buffer"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        tm = str(risk.get("target_mode", "fixed_r"))
        if tm not in ("fixed_r", "range_mid", "upper_third"):
            raise ValueError(f"risk.target_mode invalid: {tm!r}")
        validate_positive_number("risk.target_r", risk.get("target_r", 1.5))
        validate_nonnegative_number(
            "risk.atr_buffer_mult", risk.get("atr_buffer_mult", 0.35)
        )

    def required_features(self) -> list[str]:
        base = [
            "session_date",
            "minute_from_open",
            "open",
            "high",
            "low",
            "close",
            "bull_reversal_bar",
            "bear_reversal_bar",
            "lower_wick_pct",
            "upper_wick_pct",
            "atr_like_20",
        ]
        for rw in (30, 60):
            base.extend(
                [
                    f"pa_trading_range_score_{rw}",
                    f"pa_range_high_{rw}",
                    f"pa_range_low_{rw}",
                    f"pa_range_mid_{rw}",
                    f"pa_range_upper_third_{rw}",
                    f"pa_range_lower_third_{rw}",
                    f"pa_range_width_atr_{rw}",
                    f"pa_failed_breakout_down_{rw}",
                ]
            )
        for w in (30,):
            base.extend([f"range_efficiency_{w}", f"vwap_cross_count_{w}"])
        return base

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        sig = config.get("signal") or {}
        return (
            "pa_tr_bls",
            pa_range_window(config),
            pa_regime_window(config),
            str(sig.get("atr_column", "atr_like_20")),
        )

    def prepare_signal_context(
        self, df: pd.DataFrame, config: dict[str, Any]
    ) -> PaTrBlsCtx:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        rw = pa_range_window(config)
        regw = pa_regime_window(config)
        ac = atr_col_name(config)
        if ac not in work.columns:
            raise ValueError(f"{self.name}: missing {ac!r}")
        trs = f"pa_trading_range_score_{rw}"
        if trs not in work.columns:
            raise ValueError(f"{self.name}: missing {trs!r}")
        reff_col = f"range_efficiency_{regw}"
        if reff_col not in work.columns:
            raise ValueError(
                f"{self.name}: missing {reff_col!r} (set features.regime.windows to include {regw})"
            )
        vcc_col = f"vwap_cross_count_{regw}"
        if vcc_col not in work.columns:
            raise ValueError(f"{self.name}: missing {vcc_col!r}")
        return PaTrBlsCtx(
            n=len(work),
            session_id=session_id_from_dates(work["session_date"]),
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=work["close"].to_numpy(dtype=np.float64),
            low=work["low"].to_numpy(dtype=np.float64),
            high=work["high"].to_numpy(dtype=np.float64),
            atr=atr_series(work, config).to_numpy(dtype=np.float64),
            pa_tr=work[trs].to_numpy(dtype=np.float64),
            pa_rh=work[f"pa_range_high_{rw}"].to_numpy(dtype=np.float64),
            pa_rl=work[f"pa_range_low_{rw}"].to_numpy(dtype=np.float64),
            pa_rmid=work[f"pa_range_mid_{rw}"].to_numpy(dtype=np.float64),
            pa_rut=work[f"pa_range_upper_third_{rw}"].to_numpy(dtype=np.float64),
            pa_rlt=work[f"pa_range_lower_third_{rw}"].to_numpy(dtype=np.float64),
            pa_rw_atr=work[f"pa_range_width_atr_{rw}"].to_numpy(dtype=np.float64),
            bull_rev=work["bull_reversal_bar"].to_numpy(dtype=np.int8),
            fbd=work[f"pa_failed_breakout_down_{rw}"].to_numpy(dtype=np.int8),
            lwp=work["lower_wick_pct"].to_numpy(dtype=np.float64),
            uwp=work["upper_wick_pct"].to_numpy(dtype=np.float64),
            reff=work[reff_col].to_numpy(dtype=np.float64),
        )

    def generate_signal_arrays_from_context(
        self, ctx: Any, config: dict[str, Any]
    ) -> dict[str, Any]:
        if not isinstance(ctx, PaTrBlsCtx):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es, ee = int(sig["entry_start_minute"]), int(sig["entry_end_minute"])
        thr = float(sig.get("trading_range_score_min", 0.35))
        min_rw = float(sig.get("min_range_width_atr", 0.8))
        cm = str(sig.get("confirm_mode", "bull_reversal_or_failed_break"))
        block = int(bool(sig.get("block_strong_bear_breakout", True)))

        n = ctx.n
        cand = np.zeros(n, dtype=np.bool_)
        for i in range(n):
            if ctx.minute[i] < es or ctx.minute[i] > ee:
                continue
            if not math.isfinite(ctx.pa_tr[i]) or ctx.pa_tr[i] < thr:
                continue
            if (
                not math.isfinite(ctx.close[i])
                or not math.isfinite(ctx.pa_rlt[i])
                or ctx.close[i] > ctx.pa_rlt[i]
            ):
                continue
            if ctx.pa_rw_atr[i] < min_rw:
                continue
            if cm == "bull_reversal_only":
                ok_conf = ctx.bull_rev[i] != 0
            else:
                wick = (ctx.lwp[i] > ctx.uwp[i]) and (ctx.lwp[i] > 0.35)
                ok_conf = (ctx.bull_rev[i] != 0) or (ctx.fbd[i] != 0) or wick
            if not ok_conf:
                continue
            if block and (ctx.reff[i] > 0.72) and (ctx.pa_tr[i] < 0.22):
                continue
            cand[i] = True

        work_len = ctx.n
        # range arrays for finalize — rebuild from ctx fields already scoped to rw
        range_low = ctx.pa_rl
        range_mid = ctx.pa_rmid
        range_high = ctx.pa_rh
        upper_third = ctx.pa_rut
        return finalize_long_signals_df(
            pd.DataFrame({"_i": np.arange(work_len)}),
            strategy_name=self.name,
            config=config,
            cand_long=cand,
            session_id=ctx.session_id,
            close=ctx.close,
            low=ctx.low,
            high=ctx.high,
            atr=ctx.atr,
            stop_mode=str(risk.get("stop_mode", "range_low")),
            target_mode=str(risk.get("target_mode", "fixed_r")),
            target_r=float(risk.get("target_r", 1.5)),
            atr_buf_mult=float(risk.get("atr_buffer_mult", 0.35)),
            range_low=range_low,
            range_mid=range_mid,
            range_high=range_high,
            upper_third=upper_third,
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
            float(sig.get("trading_range_score_min", 0.35)),
            str(sig.get("confirm_mode", "bull_reversal_or_failed_break")),
            bool(sig.get("block_strong_bear_breakout", True)),
            str(risk.get("stop_mode", "range_low")),
            str(risk.get("target_mode", "fixed_r")),
            float(risk.get("target_r", 1.5)),
            int(sig.get("entry_start_minute", 60)),
            int(sig.get("entry_end_minute", 270)),
            float(risk.get("atr_buffer_mult", 0.35)),
            int(risk.get("max_trades_per_day", 1)),
            nz(risk.get("min_risk_per_share")),
            nz((config.get("backtest") or {}).get("max_hold_minutes")),
        )
