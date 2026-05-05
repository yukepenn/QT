"""Calendar and session clock features from ts_ny (derived from ts_utc)."""

from __future__ import annotations

import pandas as pd

from src.features.feature_config import FEATURE_COLUMNS
from src.features.utils import add_or_overwrite_columns, ensure_ts_ny, safe_copy


def _hm_to_minutes(hm: str) -> int:
    h, m = hm.strip().split(":")
    return int(h) * 60 + int(m)


def add_time_features(
    df: pd.DataFrame,
    *,
    session_tz: str = "America/New_York",
    session_start: str = "09:30",
    session_end: str = "16:00",
    copy: bool = True,
    allow_overwrite: bool = False,
) -> pd.DataFrame:
    module_name = "time_features"
    cols = FEATURE_COLUMNS[module_name]
    add_or_overwrite_columns(df, cols, module_name=module_name, allow_overwrite=allow_overwrite)

    out = safe_copy(df, copy)
    out = ensure_ts_ny(out)

    if session_tz != "America/New_York":
        out["ts_ny"] = out["ts_utc"].dt.tz_convert(session_tz)

    start_m = _hm_to_minutes(session_start)
    end_m = _hm_to_minutes(session_end)
    session_len = end_m - start_m

    ts = out["ts_ny"]
    out["session_date"] = ts.dt.strftime("%Y-%m-%d")
    out["time_ny"] = ts.dt.strftime("%H:%M")
    out["minute_of_day"] = ts.dt.hour * 60 + ts.dt.minute
    out["minute_from_open"] = out["minute_of_day"] - start_m
    out["minutes_to_close"] = end_m - out["minute_of_day"]

    mod = out["minute_of_day"]
    out["is_rth_calc"] = (mod >= start_m) & (mod < end_m)

    mfo = out["minute_from_open"]
    out["is_opening_30m"] = out["is_rth_calc"] & (mfo >= 0) & (mfo < 30)
    out["is_closing_30m"] = out["is_rth_calc"] & (mfo >= session_len - 30)

    out["day_of_week"] = ts.dt.weekday.astype(int)
    out["date_id"] = out["session_date"].str.replace("-", "", regex=False).astype(int)

    return out
