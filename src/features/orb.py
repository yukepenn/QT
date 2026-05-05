"""Opening range (ORB) features.

ORB high/low are computed from bars with 0 <= minute_from_open < open_minutes and
broadcast to all rows in that session. Use after_orb for timing-safe research.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.feature_config import FEATURE_COLUMNS
from src.features.utils import add_or_overwrite_columns, ensure_columns, safe_copy


def add_orb(
    df: pd.DataFrame,
    *,
    open_minutes: int = 15,
    copy: bool = True,
    allow_overwrite: bool = False,
) -> pd.DataFrame:
    if open_minutes <= 0:
        raise ValueError("open_minutes must be positive")

    module_name = "orb"
    cols = FEATURE_COLUMNS[module_name]
    add_or_overwrite_columns(df, cols, module_name=module_name, allow_overwrite=allow_overwrite)

    ensure_columns(df, ["session_date", "minute_from_open", "high", "low", "close"], context="orb")

    out = safe_copy(df, copy)

    or_mask = (out["minute_from_open"] >= 0) & (out["minute_from_open"] < open_minutes)
    agg = (
        out.loc[or_mask]
        .groupby("session_date", sort=False)
        .agg(orb_high=("high", "max"), orb_low=("low", "min"))
        .reset_index()
    )
    out = out.merge(agg, on="session_date", how="left")

    out["orb_open_minutes"] = int(open_minutes)
    out["orb_mid"] = (out["orb_high"] + out["orb_low"]) / 2.0
    out["orb_width"] = out["orb_high"] - out["orb_low"]
    out["orb_width_pct"] = out["orb_width"] / out["orb_mid"]

    out["after_orb"] = out["minute_from_open"] >= open_minutes

    clo = out["close"].astype(float)
    out["above_orb_high"] = clo > out["orb_high"]
    out["below_orb_low"] = clo < out["orb_low"]
    out["in_orb_range"] = (clo >= out["orb_low"]) & (clo <= out["orb_high"])

    # Known-safe ORB anchors: NaN/False until ORB is complete (after_orb).
    m_known = out["after_orb"].astype(bool)
    nan = float("nan")
    out["orb_high_known"] = np.where(m_known, out["orb_high"].astype(float), nan)
    out["orb_low_known"] = np.where(m_known, out["orb_low"].astype(float), nan)
    out["orb_mid_known"] = np.where(m_known, out["orb_mid"].astype(float), nan)
    out["orb_width_pct_known"] = np.where(m_known, out["orb_width_pct"].astype(float), nan)
    out["above_orb_high_known"] = (m_known & out["above_orb_high"].astype(bool)).astype(bool)
    out["below_orb_low_known"] = (m_known & out["below_orb_low"].astype(bool)).astype(bool)

    out["orb_breakout_dir"] = 0
    m_after = out["after_orb"]
    out.loc[m_after & (clo > out["orb_high"]), "orb_breakout_dir"] = 1
    out.loc[m_after & (clo < out["orb_low"]), "orb_breakout_dir"] = -1

    out["orb_high_dist"] = clo - out["orb_high"]
    out["orb_low_dist"] = clo - out["orb_low"]

    return out
