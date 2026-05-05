"""Session OHLC and prior-session level features."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.feature_config import FEATURE_COLUMNS
from src.features.utils import add_or_overwrite_columns, ensure_columns, safe_copy


def add_prior_day_levels(
    df: pd.DataFrame,
    *,
    copy: bool = True,
    allow_overwrite: bool = False,
) -> pd.DataFrame:
    module_name = "levels"
    cols = FEATURE_COLUMNS[module_name]
    add_or_overwrite_columns(df, cols, module_name=module_name, allow_overwrite=allow_overwrite)

    ensure_columns(df, ["session_date", "open", "high", "low", "close"], context="levels")

    out = safe_copy(df, copy)

    sess = (
        out.groupby("session_date", sort=False)
        .agg(
            session_open=("open", "first"),
            session_high=("high", "max"),
            session_low=("low", "min"),
            session_close=("close", "last"),
        )
        .reset_index()
        .sort_values("session_date")
    )

    sess["prior_day_open"] = sess["session_open"].shift(1)
    sess["prior_day_high"] = sess["session_high"].shift(1)
    sess["prior_day_low"] = sess["session_low"].shift(1)
    sess["prior_day_close"] = sess["session_close"].shift(1)
    sess["prior_day_range"] = sess["prior_day_high"] - sess["prior_day_low"]

    merge_cols = [
        "session_date",
        "session_open",
        "session_high",
        "session_low",
        "session_close",
        "prior_day_open",
        "prior_day_high",
        "prior_day_low",
        "prior_day_close",
        "prior_day_range",
    ]
    sess = sess[merge_cols]

    out = out.merge(sess, on="session_date", how="left")

    out["gap_from_prior_close"] = out["session_open"] - out["prior_day_close"]
    out["gap_pct_from_prior_close"] = out["gap_from_prior_close"] / out["prior_day_close"]

    pr = out["prior_day_range"].replace(0.0, np.nan)
    out["gap_prior_range_norm"] = out["gap_from_prior_close"].astype(float) / pr

    return out
