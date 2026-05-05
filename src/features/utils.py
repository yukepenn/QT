"""Shared helpers for feature modules."""

from __future__ import annotations

import pandas as pd

NY_TZ = "America/New_York"
UTC_TZ = "UTC"


def ensure_columns(df: pd.DataFrame, cols: list[str], *, context: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{context}: missing columns {missing}")


def safe_copy(df: pd.DataFrame, copy: bool) -> pd.DataFrame:
    return df.copy() if copy else df


def add_or_overwrite_columns(
    df: pd.DataFrame,
    new_cols: list[str],
    *,
    module_name: str,
    allow_overwrite: bool = False,
) -> None:
    dup = [c for c in new_cols if c in df.columns]
    if dup and not allow_overwrite:
        raise ValueError(f"{module_name}: columns already exist (set allow_overwrite=True to replace): {dup}")


def ensure_ts_ny(df: pd.DataFrame) -> pd.DataFrame:
    if "ts_utc" not in df.columns:
        raise ValueError("ensure_ts_ny requires ts_utc")
    df = df.copy()
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    df["ts_ny"] = df["ts_utc"].dt.tz_convert(NY_TZ)
    return df
