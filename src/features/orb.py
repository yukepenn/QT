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
    base = out.merge(agg, on="session_date", how="left")

    clo = base["close"].astype(float)
    orb_high = base["orb_high"].astype(float)
    orb_low = base["orb_low"].astype(float)
    after_orb = base["minute_from_open"] >= open_minutes
    m_known = after_orb.astype(bool)
    nan = float("nan")

    orb_mid = (orb_high + orb_low) / 2.0
    orb_width = orb_high - orb_low
    orb_width_pct = orb_width / orb_mid

    above_orb_high = clo > orb_high
    below_orb_low = clo < orb_low
    in_orb_range = (clo >= orb_low) & (clo <= orb_high)

    orb_high_known = np.where(m_known, orb_high, nan)
    orb_low_known = np.where(m_known, orb_low, nan)
    orb_mid_known = np.where(m_known, orb_mid, nan)
    orb_width_pct_known = np.where(m_known, orb_width_pct.astype(float), nan)
    above_orb_high_known = (m_known & above_orb_high.astype(bool))
    below_orb_low_known = (m_known & below_orb_low.astype(bool))

    m_after = after_orb
    orb_breakout_dir = np.zeros(len(base), dtype=np.int64)
    orb_breakout_dir = np.where(m_after & (clo > orb_high), 1, orb_breakout_dir)
    orb_breakout_dir = np.where(m_after & (clo < orb_low), -1, orb_breakout_dir)

    new_cols: dict[str, pd.Series | np.ndarray] = {
        "orb_open_minutes": pd.Series(int(open_minutes), index=base.index, dtype=np.int64),
        "orb_mid": orb_mid,
        "orb_width": orb_width,
        "orb_width_pct": orb_width_pct,
        "after_orb": after_orb,
        "above_orb_high": above_orb_high,
        "below_orb_low": below_orb_low,
        "in_orb_range": in_orb_range,
        "orb_high_known": orb_high_known,
        "orb_low_known": orb_low_known,
        "orb_mid_known": orb_mid_known,
        "orb_width_pct_known": orb_width_pct_known,
        "above_orb_high_known": above_orb_high_known,
        "below_orb_low_known": below_orb_low_known,
        "orb_breakout_dir": orb_breakout_dir,
        "orb_high_dist": clo - orb_high,
        "orb_low_dist": clo - orb_low,
    }

    return pd.concat([base, pd.DataFrame(new_cols)], axis=1)
