"""Session OHLC and prior-session level features."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.feature_config import FEATURE_COLUMNS
from src.features.utils import add_or_overwrite_columns, ensure_columns, safe_copy


def add_pa_proximity_features(
    df: pd.DataFrame,
    *,
    atr_col: str = "atr_like_20",
    copy: bool = True,
    allow_overwrite: bool = False,
) -> pd.DataFrame:
    """Distance-to-level in ATR units (lower = closer); requires prior-day + VWAP + ATR."""
    cols = FEATURE_COLUMNS["pa_proximity"]
    add_or_overwrite_columns(
        df, cols, module_name="pa_proximity", allow_overwrite=allow_overwrite
    )
    need = [
        "session_date",
        "close",
        "vwap",
        "prior_day_high",
        "prior_day_low",
        "prior_day_close",
        "session_open",
        atr_col,
    ]
    for c in need:
        if c not in df.columns:
            raise ValueError(f"add_pa_proximity_features missing {c!r}")
    ensure_columns(df, need, context="pa_proximity")
    rh20 = "rolling_high_20_prior"
    rl20 = "rolling_low_20_prior"
    if rh20 not in df.columns or rl20 not in df.columns:
        raise ValueError(
            "add_pa_proximity_features requires rolling_high_20_prior / rolling_low_20_prior"
        )

    out = safe_copy(df, copy)
    c = out["close"].astype(float)
    atr = out[atr_col].astype(float).replace(0.0, np.nan) + 1e-12

    def dist(x: pd.Series) -> pd.Series:
        return (c - x.astype(float)).abs() / atr

    newc = {
        "near_prior_day_high_atr": dist(out["prior_day_high"]),
        "near_prior_day_low_atr": dist(out["prior_day_low"]),
        "near_prior_close_atr": dist(out["prior_day_close"]),
        "near_session_open_atr": dist(out["session_open"]),
        "near_vwap_atr": dist(out["vwap"]),
        "near_rolling_high_20_atr": dist(out[rh20]),
        "near_rolling_low_20_atr": dist(out[rl20]),
    }
    return pd.concat([out, pd.DataFrame(newc)], axis=1)


def add_prior_day_levels(
    df: pd.DataFrame,
    *,
    copy: bool = True,
    allow_overwrite: bool = False,
) -> pd.DataFrame:
    """
    Notes on lookahead:

    - `full_session_*_LOOKAHEAD` columns are **full-session aggregates** (unsafe intraday).
      They are retained only for offline diagnostics and must not be required by intraday strategies.
    - `intraday_*_so_far` columns are safe intraday (cumulative by `session_date`).
    """
    module_name = "levels"
    cols = FEATURE_COLUMNS[module_name]
    add_or_overwrite_columns(
        df, cols, module_name=module_name, allow_overwrite=allow_overwrite
    )

    ensure_columns(
        df, ["session_date", "open", "high", "low", "close"], context="levels"
    )

    out = safe_copy(df, copy)

    sess = (
        out.groupby("session_date", sort=False)
        .agg(
            session_open=("open", "first"),
            full_session_high_LOOKAHEAD=("high", "max"),
            full_session_low_LOOKAHEAD=("low", "min"),
            full_session_close_LOOKAHEAD=("close", "last"),
        )
        .reset_index()
        .sort_values("session_date")
    )

    sess["prior_day_open"] = sess["session_open"].shift(1)
    sess["prior_day_high"] = sess["full_session_high_LOOKAHEAD"].shift(1)
    sess["prior_day_low"] = sess["full_session_low_LOOKAHEAD"].shift(1)
    sess["prior_day_close"] = sess["full_session_close_LOOKAHEAD"].shift(1)
    sess["prior_day_range"] = sess["prior_day_high"] - sess["prior_day_low"]

    merge_cols = [
        "session_date",
        "session_open",
        "full_session_high_LOOKAHEAD",
        "full_session_low_LOOKAHEAD",
        "full_session_close_LOOKAHEAD",
        "prior_day_open",
        "prior_day_high",
        "prior_day_low",
        "prior_day_close",
        "prior_day_range",
    ]
    sess = sess[merge_cols]

    out = out.merge(sess, on="session_date", how="left")

    g = out.groupby("session_date", sort=False)
    out["intraday_high_so_far"] = g["high"].cummax().astype(float)
    out["intraday_low_so_far"] = g["low"].cummin().astype(float)

    out["gap_from_prior_close"] = out["session_open"] - out["prior_day_close"]
    out["gap_pct_from_prior_close"] = (
        out["gap_from_prior_close"] / out["prior_day_close"]
    )

    pr = out["prior_day_range"].replace(0.0, np.nan)
    out["gap_prior_range_norm"] = out["gap_from_prior_close"].astype(float) / pr

    day_low_tbl = (
        out.groupby("session_date", sort=False)["low"]
        .min()
        .reset_index(name="_day_session_low")
        .sort_values("session_date")
    )
    dl = day_low_tbl["_day_session_low"].astype(float)
    day_low_tbl["prior_3day_low"] = dl.shift(1).rolling(3, min_periods=1).min()
    day_low_tbl["prior_5day_low"] = dl.shift(1).rolling(5, min_periods=1).min()
    wp = pd.to_datetime(day_low_tbl["session_date"]).dt.to_period("W-MON")
    week_min_low = day_low_tbl.groupby(wp, sort=False)["_day_session_low"].min()
    prev_week_min_low = week_min_low.sort_index().shift(1)
    day_low_tbl["previous_week_low"] = wp.map(prev_week_min_low).astype(float)

    out = out.merge(
        day_low_tbl[
            ["session_date", "prior_3day_low", "prior_5day_low", "previous_week_low"]
        ],
        on="session_date",
        how="left",
    )

    return out
