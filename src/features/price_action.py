"""Session-scoped price-action helpers (no lookahead on rolling priors)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from numba import njit

from src.features.build_types import PaFeatureConfig
from src.features.feature_config import FEATURE_COLUMNS
from src.features.utils import add_or_overwrite_columns, ensure_columns, safe_copy


@njit(cache=True)
def _streak_from_bool(is_pos: np.ndarray, session_id: np.ndarray, n: int) -> np.ndarray:
    out = np.zeros(n, dtype=np.int32)
    for i in range(n):
        if is_pos[i] == 0:
            out[i] = 0
            continue
        if i == 0 or session_id[i] != session_id[i - 1]:
            out[i] = 1
        else:
            out[i] = out[i - 1] + 1
    return out


@njit(cache=True)
def _micro_bull_rising_lows(
    low: np.ndarray, session_id: np.ndarray, n: int, k: int
) -> np.ndarray:
    """k-bar bull micro-channel: k consecutive lows each above prior bar low (session-scoped)."""
    out = np.zeros(n, dtype=np.int8)
    need = k - 1
    streak = 0
    for i in range(n):
        if i == 0 or session_id[i] != session_id[i - 1]:
            streak = 0
        else:
            if low[i] > low[i - 1]:
                streak += 1
            else:
                streak = 0
        out[i] = 1 if streak >= need else 0
    return out


@njit(cache=True)
def _micro_bear_falling_highs(
    high: np.ndarray, session_id: np.ndarray, n: int, k: int
) -> np.ndarray:
    """k-bar bear micro-channel: k consecutive highs each below prior bar high (session-scoped)."""
    out = np.zeros(n, dtype=np.int8)
    need = k - 1
    streak = 0
    for i in range(n):
        if i == 0 or session_id[i] != session_id[i - 1]:
            streak = 0
        else:
            if high[i] < high[i - 1]:
                streak += 1
            else:
                streak = 0
        out[i] = 1 if streak >= need else 0
    return out


def add_price_action_features(
    df: pd.DataFrame,
    *,
    windows: tuple[int, ...] = (3, 5, 10, 20, 30, 60),
    pa: PaFeatureConfig | None = None,
    copy: bool = True,
    allow_overwrite: bool = False,
) -> pd.DataFrame:
    module_name = "price_action"
    cols = FEATURE_COLUMNS[module_name]
    add_or_overwrite_columns(
        df, cols, module_name=module_name, allow_overwrite=allow_overwrite
    )

    ensure_columns(
        df, ["session_date", "open", "high", "low", "close"], context="price_action"
    )

    out = safe_copy(df, copy)
    pa_spec = pa or PaFeatureConfig()

    o = out["open"].astype(float)
    h = out["high"].astype(float)
    l = out["low"].astype(float)
    c = out["close"].astype(float)

    g = out.groupby("session_date", sort=False)

    br = h - l
    body = c - o
    body_abs = (c - o).abs()
    upper_wick = h - np.maximum(o, c)
    lower_wick = np.minimum(o, c) - l
    close_loc = np.where(br > 1e-12, (c - l) / br, 0.5)
    is_green = (c > o).astype(np.int8)
    is_red = (c < o).astype(np.int8)

    eps = 1e-12
    body_pct = body_abs / (br + eps)
    upper_wick_pct = upper_wick / (br + eps)
    lower_wick_pct = lower_wick / (br + eps)
    bull_bar = is_green
    bear_bar = is_red
    doji_thr = float(pa_spec.doji_body_pct)
    doji_bar = (body_pct < doji_thr).astype(np.int8)

    ph, pl = g["high"].shift(1), g["low"].shift(1)
    inside_bar = ((h <= ph) & (l >= pl)).astype(np.int8)
    outside_bar = ((h > ph) & (l < pl)).astype(np.int8)
    ch = float(pa_spec.close_near_high_threshold)
    clt = float(pa_spec.close_near_low_threshold)
    close_near_high = (close_loc >= ch).astype(np.int8)
    close_near_low = (close_loc <= clt).astype(np.int8)

    sbp = float(pa_spec.strong_bar_body_pct)
    strong_bull = (c > o) & (body_pct >= sbp)
    strong_bear = (c < o) & (body_pct >= sbp)
    g_low_s1 = g["low"].shift(1).fillna(l)
    g_high_s1 = g["high"].shift(1).fillna(h)
    g_open_s1 = g["open"].shift(1).fillna(o)
    bull_reversal_bar = (
        strong_bull & (l < g_low_s1) & (c > g_open_s1)
    ).astype(np.int8)
    bear_reversal_bar = (
        strong_bear & (h > g_high_s1) & (c < g_open_s1)
    ).astype(np.int8)

    sid = pd.factorize(out["session_date"], sort=False)[0].astype(np.int32)
    ig = is_green.to_numpy(dtype=np.int8)
    ir = is_red.to_numpy(dtype=np.int8)
    consecutive_green_bars = pd.Series(
        _streak_from_bool(ig, sid, len(out)), index=out.index, dtype=np.int32
    )
    consecutive_red_bars = pd.Series(
        _streak_from_bool(ir, sid, len(out)), index=out.index, dtype=np.int32
    )
    cg = consecutive_green_bars.to_numpy()
    cr = consecutive_red_bars.to_numpy()

    prev_h, prev_l = g["high"].shift(1), g["low"].shift(1)
    overlap = np.minimum(h, prev_h.fillna(h)) - np.maximum(l, prev_l.fillna(l))
    overlap_bar = (overlap > 1e-9).astype(np.int8)
    tail_bar = (
        (lower_wick > body_abs * 1.5) & (lower_wick > upper_wick)
    ).astype(np.int8)

    ch_hi = float(pa_spec.close_near_high_threshold)
    ch_lo = float(pa_spec.close_near_low_threshold)
    bull = bull_bar.to_numpy(dtype=np.int8) != 0
    bear = bear_bar.to_numpy(dtype=np.int8) != 0
    bp = body_pct.to_numpy(dtype=float)
    cloc = np.asarray(close_loc, dtype=np.float64)
    strong_bull_c = bull & (bp >= sbp) & (cloc >= ch_hi)
    strong_bear_c = bear & (bp >= sbp) & (cloc <= ch_lo)
    strong_bull_close = strong_bull_c.astype(np.int8)
    strong_bear_close = strong_bear_c.astype(np.int8)
    weak_bull_close = (bull & ~strong_bull_c).astype(np.int8)
    weak_bear_close = (bear & ~strong_bear_c).astype(np.int8)

    brv = bull_reversal_bar.to_numpy(dtype=np.int8) != 0
    berv = bear_reversal_bar.to_numpy(dtype=np.int8) != 0
    uw = upper_wick_pct.to_numpy(dtype=float)
    lw = lower_wick_pct.to_numpy(dtype=float)
    strong_bull_signal_bar = (strong_bull_c | brv).astype(np.int8)
    strong_bear_signal_bar = (strong_bear_c | berv).astype(np.int8)
    failed_bull_signal_bar = (
        bull & ~strong_bull_c & (uw > lw) & (uw >= 0.35)
    ).astype(np.int8)
    failed_bear_signal_bar = (
        bear & ~strong_bear_c & (lw > uw) & (lw >= 0.35)
    ).astype(np.int8)

    lo_np = l.to_numpy(dtype=np.float64)
    hi_np = h.to_numpy(dtype=np.float64)

    nc: dict[str, pd.Series | np.ndarray] = {
        "bar_range": br,
        "body": body,
        "body_abs": body_abs,
        "upper_wick": upper_wick,
        "lower_wick": lower_wick,
        "close_location": close_loc,
        "is_green": is_green,
        "is_red": is_red,
        "body_pct": body_pct,
        "upper_wick_pct": upper_wick_pct,
        "lower_wick_pct": lower_wick_pct,
        "bull_bar": bull_bar,
        "bear_bar": bear_bar,
        "doji_bar": doji_bar,
        "inside_bar": inside_bar,
        "outside_bar": outside_bar,
        "close_near_high": close_near_high,
        "close_near_low": close_near_low,
        "bull_reversal_bar": bull_reversal_bar,
        "bear_reversal_bar": bear_reversal_bar,
        "consecutive_green_bars": consecutive_green_bars,
        "consecutive_red_bars": consecutive_red_bars,
        "overlap_bar": overlap_bar,
        "tail_bar": tail_bar,
        "strong_bull_close": strong_bull_close,
        "strong_bear_close": strong_bear_close,
        "weak_bull_close": weak_bull_close,
        "weak_bear_close": weak_bear_close,
        "strong_bull_signal_bar": strong_bull_signal_bar,
        "strong_bear_signal_bar": strong_bear_signal_bar,
        "failed_bull_signal_bar": failed_bull_signal_bar,
        "failed_bear_signal_bar": failed_bear_signal_bar,
    }

    for k in (2, 3, 4):
        nc[f"consecutive_bull_closes_{k}"] = pd.Series(
            ((cg >= k) & (ig == 1)).astype(np.int8), index=out.index, dtype=np.int8
        )
        nc[f"consecutive_bear_closes_{k}"] = pd.Series(
            ((cr >= k) & (ir == 1)).astype(np.int8), index=out.index, dtype=np.int8
        )

    for k in (3, 4, 5):
        nc[f"bull_micro_channel_{k}"] = pd.Series(
            _micro_bull_rising_lows(lo_np, sid, len(out), k),
            index=out.index,
            dtype=np.int8,
        )
        nc[f"bear_micro_channel_{k}"] = pd.Series(
            _micro_bear_falling_highs(hi_np, sid, len(out), k),
            index=out.index,
            dtype=np.int8,
        )

    nc["prev_high_by_session"] = g["high"].shift(1)
    nc["prev_low_by_session"] = g["low"].shift(1)
    nc["prev_close_by_session"] = g["close"].shift(1)

    for n in windows:
        rh = g["high"].transform(
            lambda s, w=n: s.rolling(w, min_periods=1).max().shift(1)
        )
        rl = g["low"].transform(
            lambda s, w=n: s.rolling(w, min_periods=1).min().shift(1)
        )
        nc[f"rolling_high_{n}_prior"] = rh
        nc[f"rolling_low_{n}_prior"] = rl
        nc[f"rolling_range_{n}_prior"] = rh - rl
        nc[f"range_width_{n}"] = rh - rl

    return pd.concat([out, pd.DataFrame(nc, index=out.index)], axis=1)
