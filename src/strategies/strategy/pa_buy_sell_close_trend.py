"""Strong bull-bar trend continuation; fast engine enters next bar open (no same-bar close fill)."""

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
class PaBuySellCloseCtx:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    high: np.ndarray
    atr: np.ndarray
    vwap: np.ndarray
    cnh: np.ndarray
    body_pct: np.ndarray
    cbc3: np.ndarray
    ts: np.ndarray
    pa_clx: np.ndarray
    pa_rh: np.ndarray
    pa_rl: np.ndarray
    pa_rmid: np.ndarray
    pa_rut: np.ndarray


class PaBuySellCloseTrendStrategy(BaseStrategy):
    name = "pa_buy_sell_close_trend"
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
            "signal.body_pct_min", sig.get("body_pct_min", 0.52)
        )
        validate_nonnegative_number(
            "signal.trend_score_min", sig.get("trend_score_min", 0.35)
        )
        sm = str(risk.get("stop_mode", "signal_low"))
        if sm not in ("signal_low", "last_pullback_low", "atr_buffer"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        tm = str(risk.get("target_mode", "fixed_r"))
        if tm != "fixed_r":
            raise ValueError(f"risk.target_mode invalid: {tm!r} (only fixed_r in MVP)")
        validate_positive_number("risk.target_r", risk.get("target_r", 1.2))
        validate_nonnegative_number(
            "risk.atr_buffer_mult", risk.get("atr_buffer_mult", 0.35)
        )

    def required_features(self) -> list[str]:
        regw = 30
        rw = 60
        return [
            "session_date",
            "minute_from_open",
            "open",
            "high",
            "low",
            "close",
            "vwap",
            "close_near_high",
            "body_pct",
            "consecutive_bull_closes_3",
            f"trend_score_{regw}",
            f"pa_climax_score_{rw}",
            f"pa_range_high_{rw}",
            f"pa_range_low_{rw}",
            f"pa_range_mid_{rw}",
            f"pa_range_upper_third_{rw}",
            "atr_like_20",
        ]

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        sig = config.get("signal") or {}
        return (
            "pa_buy_sell_close",
            pa_range_window(config),
            pa_regime_window(config),
            float(sig.get("body_pct_min", 0.52)),
            float(sig.get("trend_score_min", 0.35)),
            bool(sig.get("require_vwap_side", False)),
            str(sig.get("atr_column", "atr_like_20")),
        )

    def prepare_signal_context(
        self, df: pd.DataFrame, config: dict[str, Any]
    ) -> PaBuySellCloseCtx:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        rw = pa_range_window(config)
        regw = pa_regime_window(config)
        ac = atr_col_name(config)
        if ac not in work.columns:
            raise ValueError(f"{self.name}: missing {ac!r}")
        ts_col = f"trend_score_{regw}"
        if ts_col not in work.columns:
            raise ValueError(f"{self.name}: missing {ts_col!r}")
        return PaBuySellCloseCtx(
            n=len(work),
            session_id=session_id_from_dates(work["session_date"]),
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=work["close"].to_numpy(dtype=np.float64),
            low=work["low"].to_numpy(dtype=np.float64),
            high=work["high"].to_numpy(dtype=np.float64),
            atr=atr_series(work, config).to_numpy(dtype=np.float64),
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            cnh=work["close_near_high"].to_numpy(dtype=np.int8),
            body_pct=work["body_pct"].to_numpy(dtype=np.float64),
            cbc3=work["consecutive_bull_closes_3"].to_numpy(dtype=np.int8),
            ts=work[ts_col].to_numpy(dtype=np.float64),
            pa_clx=work[f"pa_climax_score_{rw}"].to_numpy(dtype=np.float64),
            pa_rh=work[f"pa_range_high_{rw}"].to_numpy(dtype=np.float64),
            pa_rl=work[f"pa_range_low_{rw}"].to_numpy(dtype=np.float64),
            pa_rmid=work[f"pa_range_mid_{rw}"].to_numpy(dtype=np.float64),
            pa_rut=work[f"pa_range_upper_third_{rw}"].to_numpy(dtype=np.float64),
        )

    def generate_signal_arrays_from_context(
        self, ctx: Any, config: dict[str, Any]
    ) -> dict[str, Any]:
        if not isinstance(ctx, PaBuySellCloseCtx):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es, ee = int(sig["entry_start_minute"]), int(sig["entry_end_minute"])
        body_min = float(sig.get("body_pct_min", 0.52))
        ts_min = float(sig.get("trend_score_min", 0.35))
        req_v = bool(sig.get("require_vwap_side", False))
        clx_max = float(sig.get("climax_score_max", 0.75))
        block_clx = bool(sig.get("block_climax", True))

        n = ctx.n
        cand = np.zeros(n, dtype=np.bool_)
        for i in range(n):
            if ctx.minute[i] < es or ctx.minute[i] > ee:
                continue
            if ctx.cnh[i] == 0:
                continue
            if not math.isfinite(ctx.body_pct[i]) or ctx.body_pct[i] < body_min:
                continue
            if ctx.cbc3[i] == 0:
                continue
            if not math.isfinite(ctx.ts[i]) or ctx.ts[i] < ts_min:
                continue
            if req_v and (not math.isfinite(ctx.vwap[i]) or ctx.close[i] < ctx.vwap[i]):
                continue
            if block_clx and math.isfinite(ctx.pa_clx[i]) and ctx.pa_clx[i] > clx_max:
                continue
            cand[i] = True

        sm = str(risk.get("stop_mode", "signal_low"))
        if sm == "last_pullback_low":
            sm = "range_low"

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
            target_mode="fixed_r",
            target_r=float(risk.get("target_r", 1.2)),
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
            float(sig.get("body_pct_min", 0.52)),
            float(sig.get("trend_score_min", 0.35)),
            bool(sig.get("require_vwap_side", False)),
            bool(sig.get("block_climax", True)),
            float(sig.get("climax_score_max", 0.75)),
            str(risk.get("stop_mode", "signal_low")),
            str(risk.get("target_mode", "fixed_r")),
            float(risk.get("target_r", 1.2)),
            int(sig.get("entry_start_minute", 60)),
            int(sig.get("entry_end_minute", 270)),
            float(risk.get("atr_buffer_mult", 0.35)),
            int(risk.get("max_trades_per_day", 1)),
            nz(risk.get("min_risk_per_share")),
            nz((config.get("backtest") or {}).get("max_hold_minutes")),
        )
