"""PA failed rolling-range breakout trap (long-only MVP; not ORB)."""

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
class PaFbTrapCtx:
    n: int
    session_id: np.ndarray
    minute: np.ndarray
    close: np.ndarray
    low: np.ndarray
    high: np.ndarray
    atr: np.ndarray
    fbd: np.ndarray
    cbi: np.ndarray
    bull_rev: np.ndarray
    ft_down: np.ndarray
    pa_rh: np.ndarray
    pa_rl: np.ndarray
    pa_rmid: np.ndarray
    pa_rut: np.ndarray
    pa_tr: np.ndarray


class PaFailedRangeBreakoutTrapStrategy(BaseStrategy):
    name = "pa_failed_range_breakout_trap"
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
            "signal.fail_window_bars", sig.get("fail_window_bars", 4)
        )
        sm = str(risk.get("stop_mode", "failed_extreme"))
        if sm not in ("failed_extreme", "range_low_buffer", "signal_low"):
            raise ValueError(f"risk.stop_mode invalid: {sm!r}")
        tm = str(risk.get("target_mode", "fixed_r"))
        if tm not in ("fixed_r", "range_mid", "range_high"):
            raise ValueError(f"risk.target_mode invalid: {tm!r}")
        validate_positive_number("risk.target_r", risk.get("target_r", 1.5))

    def required_features(self) -> list[str]:
        out = [
            "session_date",
            "minute_from_open",
            "open",
            "high",
            "low",
            "close",
            "bull_reversal_bar",
            "atr_like_20",
        ]
        for rw in (30, 60):
            out.extend(
                [
                    f"pa_range_high_{rw}",
                    f"pa_range_low_{rw}",
                    f"pa_breakout_down_{rw}",
                    f"pa_failed_breakout_down_{rw}",
                    f"pa_close_back_inside_{rw}",
                    f"pa_range_mid_{rw}",
                    f"pa_range_upper_third_{rw}",
                    f"pa_followthrough_down_{rw}",
                    f"pa_trading_range_score_{rw}",
                ]
            )
        return out

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        sig = config.get("signal") or {}
        return (
            "pa_fb_trap",
            pa_range_window(config),
            int(sig.get("fail_window_bars", 4)),
            bool(sig.get("require_tr_regime", False)),
            str(sig.get("atr_column", "atr_like_20")),
        )

    def prepare_signal_context(
        self, df: pd.DataFrame, config: dict[str, Any]
    ) -> PaFbTrapCtx:
        work = df.sort_values("ts_utc", kind="mergesort").reset_index(drop=True)
        rw = pa_range_window(config)
        ac = atr_col_name(config)
        if ac not in work.columns:
            raise ValueError(f"{self.name}: missing {ac!r}")
        trs = f"pa_trading_range_score_{rw}"
        if trs not in work.columns:
            raise ValueError(f"{self.name}: missing {trs!r}")
        ft = f"pa_followthrough_down_{rw}"
        if ft not in work.columns:
            raise ValueError(f"{self.name}: missing {ft!r}")
        return PaFbTrapCtx(
            n=len(work),
            session_id=session_id_from_dates(work["session_date"]),
            minute=work["minute_from_open"].to_numpy(dtype=np.int32),
            close=work["close"].to_numpy(dtype=np.float64),
            low=work["low"].to_numpy(dtype=np.float64),
            high=work["high"].to_numpy(dtype=np.float64),
            atr=atr_series(work, config).to_numpy(dtype=np.float64),
            fbd=work[f"pa_failed_breakout_down_{rw}"].to_numpy(dtype=np.int8),
            cbi=work[f"pa_close_back_inside_{rw}"].to_numpy(dtype=np.int8),
            bull_rev=work["bull_reversal_bar"].to_numpy(dtype=np.int8),
            ft_down=work[ft].to_numpy(dtype=np.int8),
            pa_rh=work[f"pa_range_high_{rw}"].to_numpy(dtype=np.float64),
            pa_rl=work[f"pa_range_low_{rw}"].to_numpy(dtype=np.float64),
            pa_rmid=work[f"pa_range_mid_{rw}"].to_numpy(dtype=np.float64),
            pa_rut=work[f"pa_range_upper_third_{rw}"].to_numpy(dtype=np.float64),
            pa_tr=work[trs].to_numpy(dtype=np.float64),
        )

    def generate_signal_arrays_from_context(
        self, ctx: Any, config: dict[str, Any]
    ) -> dict[str, Any]:
        if not isinstance(ctx, PaFbTrapCtx):
            raise TypeError(ctx)
        sig = config.get("signal") or {}
        risk = config.get("risk") or {}
        es, ee = int(sig["entry_start_minute"]), int(sig["entry_end_minute"])
        req_tr = bool(sig.get("require_tr_regime", False))
        tr_max = float(sig.get("tr_regime_max", 0.45))

        n = ctx.n
        cand = np.zeros(n, dtype=np.bool_)
        for i in range(n):
            if ctx.minute[i] < es or ctx.minute[i] > ee:
                continue
            if ctx.ft_down[i] != 0:
                continue
            if ctx.fbd[i] == 0 and not (ctx.cbi[i] != 0 and ctx.bull_rev[i] != 0):
                continue
            if req_tr and (not math.isfinite(ctx.pa_tr[i]) or ctx.pa_tr[i] > tr_max):
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
            stop_mode=str(risk.get("stop_mode", "failed_extreme")),
            target_mode=str(risk.get("target_mode", "fixed_r")),
            target_r=float(risk.get("target_r", 1.5)),
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
            int(sig.get("fail_window_bars", 4)),
            bool(sig.get("require_tr_regime", False)),
            float(sig.get("tr_regime_max", 0.45)),
            str(risk.get("stop_mode", "failed_extreme")),
            str(risk.get("target_mode", "fixed_r")),
            float(risk.get("target_r", 1.5)),
            nz((config.get("backtest") or {}).get("max_hold_minutes")),
        )
