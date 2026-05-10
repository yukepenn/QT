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

    br = h - l
    out["bar_range"] = br
    out["body"] = c - o
    out["body_abs"] = (c - o).abs()
    out["upper_wick"] = h - np.maximum(o, c)
    out["lower_wick"] = np.minimum(o, c) - l
    close_loc = np.where(br > 1e-12, (c - l) / br, 0.5)
    out["close_location"] = close_loc
    out["is_green"] = (c > o).astype(np.int8)
    out["is_red"] = (c < o).astype(np.int8)

    eps = 1e-12
    out["body_pct"] = out["body_abs"] / (br + eps)
    out["upper_wick_pct"] = out["upper_wick"] / (br + eps)
    out["lower_wick_pct"] = out["lower_wick"] / (br + eps)
    out["bull_bar"] = out["is_green"]
    out["bear_bar"] = out["is_red"]
    doji_thr = float(pa_spec.doji_body_pct)
    out["doji_bar"] = (out["body_pct"] < doji_thr).astype(np.int8)

    g = out.groupby("session_date", sort=False)
    ph, pl = g["high"].shift(1), g["low"].shift(1)
    out["inside_bar"] = ((h <= ph) & (l >= pl)).astype(np.int8)
    out["outside_bar"] = ((h > ph) & (l < pl)).astype(np.int8)
    ch = float(pa_spec.close_near_high_threshold)
    clt = float(pa_spec.close_near_low_threshold)
    out["close_near_high"] = (close_loc >= ch).astype(np.int8)
    out["close_near_low"] = (close_loc <= clt).astype(np.int8)

    sbp = float(pa_spec.strong_bar_body_pct)
    strong_bull = (c > o) & (out["body_pct"] >= sbp)
    strong_bear = (c < o) & (out["body_pct"] >= sbp)
    out["bull_reversal_bar"] = (
        strong_bull
        & (l < g["low"].shift(1).fillna(l))
        & (c > g["open"].shift(1).fillna(o))
    ).astype(np.int8)
    out["bear_reversal_bar"] = (
        strong_bear
        & (h > g["high"].shift(1).fillna(h))
        & (c < g["open"].shift(1).fillna(o))
    ).astype(np.int8)

    sid = pd.factorize(out["session_date"], sort=False)[0].astype(np.int32)
    ig = out["is_green"].to_numpy(dtype=np.int8)
    ir = out["is_red"].to_numpy(dtype=np.int8)
    out["consecutive_green_bars"] = pd.Series(
        _streak_from_bool(ig, sid, len(out)), index=out.index, dtype=np.int32
    )
    out["consecutive_red_bars"] = pd.Series(
        _streak_from_bool(ir, sid, len(out)), index=out.index, dtype=np.int32
    )
    cg = out["consecutive_green_bars"].to_numpy()
    cr = out["consecutive_red_bars"].to_numpy()
    for k in (2, 3, 4):
        out[f"consecutive_bull_closes_{k}"] = ((cg >= k) & (ig == 1)).astype(np.int8)
        out[f"consecutive_bear_closes_{k}"] = ((cr >= k) & (ir == 1)).astype(np.int8)

    prev_h, prev_l = g["high"].shift(1), g["low"].shift(1)
    overlap = np.minimum(h, prev_h.fillna(h)) - np.maximum(l, prev_l.fillna(l))
    out["overlap_bar"] = (overlap > 1e-9).astype(np.int8)
    out["tail_bar"] = (
        (out["lower_wick"] > out["body_abs"] * 1.5)
        & (out["lower_wick"] > out["upper_wick"])
    ).astype(np.int8)

    out["prev_high_by_session"] = g["high"].shift(1)
    out["prev_low_by_session"] = g["low"].shift(1)
    out["prev_close_by_session"] = g["close"].shift(1)

    for n in windows:
        rh = g["high"].transform(
            lambda s, w=n: s.rolling(w, min_periods=1).max().shift(1)
        )
        rl = g["low"].transform(
            lambda s, w=n: s.rolling(w, min_periods=1).min().shift(1)
        )
        out[f"rolling_high_{n}_prior"] = rh
        out[f"rolling_low_{n}_prior"] = rl
        out[f"rolling_range_{n}_prior"] = rh - rl
        out[f"range_width_{n}"] = rh - rl

    return out
