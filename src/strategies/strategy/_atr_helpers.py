"""Small helpers for ATR-like columns used across MVP strategies."""

from __future__ import annotations

from typing import Any

import pandas as pd


def atr_series(df: pd.DataFrame, config: dict[str, Any]) -> pd.Series:
    sig = config.get("signal") or {}
    col = str(sig.get("atr_column", "atr_like_15"))
    if col in df.columns:
        return df[col].astype(float)
    for fallback in ("atr_like_15", "atr_like_5", "tr", "range_15"):
        if fallback in df.columns:
            return df[fallback].astype(float)
    return (df["high"].astype(float) - df["low"].astype(float)).abs()
