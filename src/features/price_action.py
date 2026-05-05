"""Session-scoped price-action helpers (no lookahead on rolling priors)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.feature_config import FEATURE_COLUMNS
from src.features.utils import add_or_overwrite_columns, ensure_columns, safe_copy


def add_price_action_features(
    df: pd.DataFrame,
    *,
    windows: tuple[int, ...] = (3, 5, 10, 20, 30, 60),
    copy: bool = True,
    allow_overwrite: bool = False,
) -> pd.DataFrame:
    module_name = "price_action"
    cols = FEATURE_COLUMNS[module_name]
    add_or_overwrite_columns(df, cols, module_name=module_name, allow_overwrite=allow_overwrite)

    ensure_columns(df, ["session_date", "open", "high", "low", "close"], context="price_action")

    out = safe_copy(df, copy)

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

    g = out.groupby("session_date", sort=False)
    out["prev_high_by_session"] = g["high"].shift(1)
    out["prev_low_by_session"] = g["low"].shift(1)
    out["prev_close_by_session"] = g["close"].shift(1)

    for n in windows:
        rh = g["high"].transform(lambda s, w=n: s.rolling(w, min_periods=1).max().shift(1))
        rl = g["low"].transform(lambda s, w=n: s.rolling(w, min_periods=1).min().shift(1))
        out[f"rolling_high_{n}_prior"] = rh
        out[f"rolling_low_{n}_prior"] = rl
        out[f"rolling_range_{n}_prior"] = rh - rl
        out[f"range_width_{n}"] = rh - rl

    return out
