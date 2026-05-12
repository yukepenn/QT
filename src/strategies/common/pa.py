"""Generic PA helpers: config parsing, long stop/target, signal finalization.

New code should import from this module. ``src.strategies.strategy.pa_batch_a_utils`` remains a
thin compatibility shim for existing strategy and research imports.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from src.execution.types import TM_FIXED_R, TM_NONE
from src.strategies.strategy.base import init_standard_signal_columns
from src.strategies.strategy.fast_utils import (
    apply_min_risk_filter_df,
    get_min_risk_per_share,
    thin_first_signal_per_session_numba,
)


def pa_range_window(config: dict[str, Any]) -> int:
    return int((config.get("features") or {}).get("pa_range_window", 60))


def pa_regime_window(config: dict[str, Any]) -> int:
    return int((config.get("features") or {}).get("pa_regime_window", 30))


def atr_col_name(config: dict[str, Any]) -> str:
    return str((config.get("signal") or {}).get("atr_column", "atr_like_20"))


def pa_context_windows(config: dict[str, Any]) -> tuple[int, int, str]:
    """Return (pa_range_window, pa_regime_window, atr_column_name) from merged strategy config."""
    return (
        int(pa_range_window(config)),
        int(pa_regime_window(config)),
        str(atr_col_name(config)),
    )


def pa_family_from_strategy_name(name: str) -> str:
    """Coarse PA plugin family label for logging / reasons (not used in feature_key)."""
    if name.startswith("pa_"):
        return "pa_mvp"
    return "other"


def build_pa_reason(
    strategy_name: str,
    setup_name: str,
    regime_tag: str | None = None,
    extra: str | None = None,
) -> str:
    parts = [strategy_name, setup_name]
    if regime_tag:
        parts.append(regime_tag)
    if extra:
        parts.append(extra)
    return "|".join(parts)


def safe_bool_array(x: Any, n: int) -> np.ndarray:
    """Coerce to int8 0/1 array length n (fills False on bad input)."""
    if isinstance(x, np.ndarray) and x.dtype == np.bool_:
        return x.astype(np.int8)
    if isinstance(x, np.ndarray):
        return (x != 0).astype(np.int8)
    try:
        arr = np.asarray(x, dtype=np.float64)
        return (arr != 0.0).astype(np.int8)
    except Exception:
        return np.zeros(n, dtype=np.int8)


def safe_float_array(x: Any, n: int) -> np.ndarray:
    """Coerce to float64 length n (NaN on failure)."""
    try:
        arr = np.asarray(x, dtype=np.float64)
        if arr.size != n:
            return np.full(n, np.nan, dtype=np.float64)
        return arr
    except Exception:
        return np.full(n, np.nan, dtype=np.float64)


def long_stop_target(
    *,
    close: float,
    low: float,
    high: float,
    atr: float,
    vwap: float,
    stop_mode: str,
    target_mode: str,
    target_r: float,
    atr_buf_mult: float,
    range_low: float,
    range_mid: float,
    range_high: float,
    upper_third: float,
) -> tuple[float, float, int, float] | None:
    """Return (stop, target, target_mode_code, target_r_multiple) or None if invalid long geometry.

    Structural modes such as ``range_mid``, ``range_high``, ``vwap``, ``prior_high``, etc. are
    converted at **signal-bar close** into an **effective fixed-R multiple** (see ``TM_FIXED_R`` /
    ``fast.py``). They do **not** emit ``TM_FIXED_PX`` today; see ``pa_structural_target_semantics.md``.
    """
    if stop_mode == "range_low":
        sl = float(range_low)
    elif stop_mode == "channel_low":
        sl = float(range_low)
    elif stop_mode == "signal_low":
        sl = float(low)
    elif stop_mode in ("climax_low", "second_entry_low", "wedge_low"):
        sl = float(low)
    elif stop_mode == "pullback_low":
        sl = float(low)
    elif stop_mode == "major_low":
        sl = float(range_low)
    elif stop_mode == "failed_extreme":
        sl = float(low)
    elif stop_mode == "range_low_buffer":
        sl = float(range_low) - 0.05 * float(atr)
    elif stop_mode == "breakout_point_buffer":
        sl = float(range_high) - float(atr_buf_mult) * float(atr)
    elif stop_mode == "last_pullback_low":
        sl = float(range_low)
    elif stop_mode == "atr_buffer":
        sl = float(close) - float(atr_buf_mult) * float(atr)
    else:
        sl = float(low)

    risk = float(close) - sl
    if risk <= 0 or not math.isfinite(risk):
        return None

    if target_mode == "fixed_r":
        tgt = float(close) + float(target_r) * risk
        tmc = TM_FIXED_R
        tr = float(target_r)
    elif target_mode == "range_mid":
        tgt = max(float(close) + 1e-6 * risk, float(range_mid))
        tmc = TM_FIXED_R
        tr = (tgt - float(close)) / risk if risk > 0 else float(target_r)
    elif target_mode == "upper_third":
        tgt = max(float(close) + 1e-6 * risk, float(upper_third))
        tmc = TM_FIXED_R
        tr = (tgt - float(close)) / risk if risk > 0 else float(target_r)
    elif target_mode == "range_high":
        tgt = max(float(close) + 1e-6 * risk, float(range_high))
        tmc = TM_FIXED_R
        tr = (tgt - float(close)) / risk if risk > 0 else float(target_r)
    elif target_mode == "prior_swing_high":
        tgt = max(float(close) + 1e-6 * risk, float(range_high))
        tmc = TM_FIXED_R
        tr = (tgt - float(close)) / risk if risk > 0 else float(target_r)
    elif target_mode == "vwap":
        if math.isfinite(float(vwap)):
            tgt = float(vwap)
        else:
            tgt = float(close) + float(target_r) * risk
        tmc = TM_FIXED_R
        tr = (tgt - float(close)) / risk if risk > 0 else float(target_r)
    elif target_mode in ("climax_mid", "channel_mid"):
        tgt = max(float(close) + 1e-6 * risk, float(range_mid))
        tmc = TM_FIXED_R
        tr = (tgt - float(close)) / risk if risk > 0 else float(target_r)
    elif target_mode == "prior_high":
        tgt = max(float(close) + 1e-6 * risk, float(range_high))
        tmc = TM_FIXED_R
        tr = (tgt - float(close)) / risk if risk > 0 else float(target_r)
    else:
        tgt = float(close) + float(target_r) * risk
        tmc = TM_FIXED_R
        tr = float(target_r)

    if not (math.isfinite(tgt) and tgt > float(close) and sl < float(close)):
        return None
    return sl, tgt, tmc, tr


def finalize_long_signals_df(
    work: pd.DataFrame,
    *,
    strategy_name: str,
    config: dict[str, Any],
    cand_long: np.ndarray,
    session_id: np.ndarray,
    close: np.ndarray,
    low: np.ndarray,
    high: np.ndarray,
    atr: np.ndarray,
    stop_mode: str,
    target_mode: str,
    target_r: float,
    atr_buf_mult: float,
    range_low: np.ndarray,
    range_mid: np.ndarray,
    range_high: np.ndarray,
    upper_third: np.ndarray,
    vwap: np.ndarray | None = None,
) -> dict[str, Any]:
    n = len(work)
    cand_short = np.zeros(n, dtype=np.bool_)
    max_tr = int((config.get("risk") or {}).get("max_trades_per_day", 1))
    fl, _ = thin_first_signal_per_session_numba(
        cand_long, cand_short, session_id, max_tr
    )
    side = np.zeros(n, dtype=np.int8)
    valid = np.zeros(n, dtype=np.bool_)
    stp = np.zeros(n, dtype=np.float64)
    tgtp = np.zeros(n, dtype=np.float64)
    tmc = np.full(n, TM_NONE, dtype=np.int8)
    tr = np.zeros(n, dtype=np.float64)
    rsk = np.zeros(n, dtype=np.float64)
    min_risk = float(get_min_risk_per_share(config))
    vw = vwap if vwap is not None else np.full(n, np.nan, dtype=np.float64)
    for i in range(n):
        if not fl[i]:
            continue
        got = long_stop_target(
            close=float(close[i]),
            low=float(low[i]),
            high=float(high[i]),
            atr=float(atr[i]),
            vwap=float(vw[i]),
            stop_mode=stop_mode,
            target_mode=target_mode,
            target_r=target_r,
            atr_buf_mult=atr_buf_mult,
            range_low=float(range_low[i]),
            range_mid=float(range_mid[i]),
            range_high=float(range_high[i]),
            upper_third=float(upper_third[i]),
        )
        if got is None:
            continue
        sl, tg, tc, tr_mult = got
        rshare = float(close[i]) - sl
        if rshare < min_risk:
            continue
        side[i] = 1
        valid[i] = True
        stp[i] = sl
        tgtp[i] = tg
        tmc[i] = tc
        tr[i] = tr_mult
        rsk[i] = rshare
    return {
        "side": side,
        "valid": valid,
        "stop": stp,
        "target_preview": tgtp,
        "target_mode_code": tmc,
        "target_r": tr,
        "risk_preview": rsk,
    }


def signals_df_from_arrays(
    work: pd.DataFrame, strategy_name: str, arr: dict[str, Any], config: dict[str, Any]
) -> pd.DataFrame:
    out = init_standard_signal_columns(work, strategy_name=strategy_name, copy=True)
    out["sig_side"] = arr["side"]
    out["sig_valid"] = arr["valid"]
    out["sig_stop"] = arr["stop"]
    out["sig_target"] = arr["target_preview"]
    out["sig_target_mode"] = np.where(
        arr["target_mode_code"] == TM_FIXED_R, "fixed_r", ""
    )
    out["sig_target_r"] = arr["target_r"]
    out["sig_risk_per_share"] = arr["risk_preview"]
    out.loc[out["sig_valid"], "sig_reason"] = f"{strategy_name}_long"
    return apply_min_risk_filter_df(out, config=config)
