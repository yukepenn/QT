"""PA broad bull-channel buy-zone pullback (long-only MVP; not ORB/VWAP core)."""

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
class PaBroadChannelCtx:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    high: np.ndarray
    atr: np.ndarray
    vwap: np.ndarray
    pa_bbull: np.ndarray
    pa_rlt: np.ndarray
    pa_rh: np.ndarray
    pa_rl: np.ndarray
    pa_rmid: np.ndarray
    pa_rut: np.ndarray
    pa_pd: np.ndarray
    bull_rev: np.ndarray
    pa_clx: np.ndarray


class PaBroadChannelZoneStrategy(BaseStrategy):
    name = "pa_broad_channel_zone"
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
        validate_nonnegative_number("signal.broad_bull_score_min", sig.get("broad_bull_score_min", 0.28))
        validate_nonnegative_number("signal.max_pullback_depth_atr", sig.get("max_pullback_depth_atr", 1.15))
        validate_nonnegative_number("signal.min_pullback_depth_atr", sig.get("min_pullback_depth_atr", 0.05))
        sm = str(risk.get("stop_mode", "range_low"))
        if sm not in ("channel_low", "range_low", "signal_low", "atr_buffer"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        tm = str(risk.get("target_mode", "fixed_r"))
        if tm not in ("fixed_r", "channel_mid", "range_mid", "prior_high"):
            raise ValueError(f"risk.target_mode invalid: {tm!r}")
        validate_positive_number("risk.target_r", risk.get("target_r", 1.5))
        validate_nonnegative_number("risk.atr_buffer_mult", risk.get("atr_buffer_mult", 0.35))

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
                    f"pa_broad_bull_channel_score_{rw}",
                    f"pa_range_high_{rw}",
                    f"pa_range_low_{rw}",
                    f"pa_range_mid_{rw}",
                    f"pa_range_upper_third_{rw}",
                    f"pa_range_lower_third_{rw}",
                    f"pa_pullback_depth_atr_{rw}",
                    f"pa_climax_score_{rw}",
                ]
            )
        return base

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        sig = config.get("signal") or {}
        return (
            "pa_broad_ch",
            pa_range_window(config),
            pa_regime_window(config),
            float(sig.get("broad_bull_score_min", 0.28)),
            bool(sig.get("require_vwap_context", False)),
            bool(sig.get("block_climax", True)),
            str(sig.get("atr_column", "atr_like_20")),
        )

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> PaBroadChannelCtx:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        rw = pa_range_window(config)
        ac = atr_col_name(config)
        if ac not in work.columns:
            raise ValueError(f"{self.name}: missing {ac!r}")
        col = f"pa_broad_bull_channel_score_{rw}"
        if col not in work.columns:
            raise ValueError(f"{self.name}: missing {col!r}")
        return PaBroadChannelCtx(
            n=len(work),
            session_id=session_id_from_dates(work["session_date"]),
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=work["close"].to_numpy(dtype=np.float64),
            low=work["low"].to_numpy(dtype=np.float64),
            high=work["high"].to_numpy(dtype=np.float64),
            atr=atr_series(work, config).to_numpy(dtype=np.float64),
            vwap=work["vwap"].to_numpy(dtype=np.float64),
            pa_bbull=work[col].to_numpy(dtype=np.float64),
            pa_rlt=work[f"pa_range_lower_third_{rw}"].to_numpy(dtype=np.float64),
            pa_rh=work[f"pa_range_high_{rw}"].to_numpy(dtype=np.float64),
            pa_rl=work[f"pa_range_low_{rw}"].to_numpy(dtype=np.float64),
            pa_rmid=work[f"pa_range_mid_{rw}"].to_numpy(dtype=np.float64),
            pa_rut=work[f"pa_range_upper_third_{rw}"].to_numpy(dtype=np.float64),
            pa_pd=work[f"pa_pullback_depth_atr_{rw}"].to_numpy(dtype=np.float64),
            bull_rev=work["bull_reversal_bar"].to_numpy(dtype=np.int8),
            pa_clx=work[f"pa_climax_score_{rw}"].to_numpy(dtype=np.float64),
        )

    def generate_signal_arrays_from_context(self, ctx: Any, config: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(ctx, PaBroadChannelCtx):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es, ee = int(sig["entry_start_minute"]), int(sig["entry_end_minute"])
        thr = float(sig.get("broad_bull_score_min", 0.28))
        max_pd = float(sig.get("max_pullback_depth_atr", 1.15))
        min_pd = float(sig.get("min_pullback_depth_atr", 0.05))
        req_v = bool(sig.get("require_vwap_context", False))
        vwap_min = float(sig.get("vwap_context_min_atr", -0.15))
        block_clx = bool(sig.get("block_climax", True))
        clx_max = float(sig.get("climax_score_max", 0.78))

        n = ctx.n
        cand = np.zeros(n, dtype=np.bool_)
        for i in range(n):
            if ctx.minute[i] < es or ctx.minute[i] > ee:
                continue
            if not math.isfinite(ctx.pa_bbull[i]) or ctx.pa_bbull[i] < thr:
                continue
            if not math.isfinite(ctx.close[i]) or ctx.close[i] > ctx.pa_rlt[i]:
                continue
            if not math.isfinite(ctx.pa_pd[i]) or ctx.pa_pd[i] < min_pd or ctx.pa_pd[i] > max_pd:
                continue
            if req_v and (not math.isfinite(ctx.vwap[i]) or ctx.close[i] < ctx.vwap[i] + vwap_min * ctx.atr[i]):
                continue
            if ctx.bull_rev[i] == 0:
                continue
            if block_clx and math.isfinite(ctx.pa_clx[i]) and ctx.pa_clx[i] > clx_max:
                continue
            cand[i] = True

        sm = str(risk.get("stop_mode", "range_low"))
        if sm == "channel_low":
            sm = "range_low"
        tm = str(risk.get("target_mode", "fixed_r"))
        if tm == "channel_mid":
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
            target_r=float(risk.get("target_r", 1.5)),
            atr_buf_mult=float(risk.get("atr_buffer_mult", 0.35)),
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
            float(sig.get("broad_bull_score_min", 0.28)),
            float(sig.get("max_pullback_depth_atr", 1.15)),
            float(sig.get("min_pullback_depth_atr", 0.05)),
            bool(sig.get("require_vwap_context", False)),
            float(sig.get("vwap_context_min_atr", -0.15)),
            bool(sig.get("block_climax", True)),
            float(sig.get("climax_score_max", 0.78)),
            str(risk.get("stop_mode", "range_low")),
            str(risk.get("target_mode", "fixed_r")),
            float(risk.get("target_r", 1.5)),
            nz((config.get("backtest") or {}).get("max_hold_minutes")),
        )
