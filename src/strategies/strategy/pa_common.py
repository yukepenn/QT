"""Shared PA helpers (config parsing, naming). No signal gating — strategies stay explicit."""

from __future__ import annotations

from typing import Any

import numpy as np

from src.strategies.strategy.pa_batch_a_utils import (
    atr_col_name,
    pa_range_window,
    pa_regime_window,
)


def pa_context_windows(config: dict[str, Any]) -> tuple[int, int, str]:
    """Return (pa_range_window, pa_regime_window, atr_column_name) from merged strategy config."""
    return (
        int(pa_range_window(config)),
        int(pa_regime_window(config)),
        str(atr_col_name(config)),
    )


def pa_family_from_strategy_name(name: str) -> str:
    """Coarse PA plugin family label for logging / reasons (not used in feature_key)."""
    if name.startswith("pa_"):
        return "pa_mvp"
    return "other"


def build_pa_reason(
    strategy_name: str,
    setup_name: str,
    regime_tag: str | None = None,
    extra: str | None = None,
) -> str:
    parts = [strategy_name, setup_name]
    if regime_tag:
        parts.append(regime_tag)
    if extra:
        parts.append(extra)
    return "|".join(parts)


def safe_bool_array(x: Any, n: int) -> np.ndarray:
    """Coerce to int8 0/1 array length n (fills False on bad input)."""
    if isinstance(x, np.ndarray) and x.dtype == np.bool_:
        return x.astype(np.int8)
    if isinstance(x, np.ndarray):
        return (x != 0).astype(np.int8)
    try:
        arr = np.asarray(x, dtype=np.float64)
        return (arr != 0.0).astype(np.int8)
    except Exception:
        return np.zeros(n, dtype=np.int8)


def safe_float_array(x: Any, n: int) -> np.ndarray:
    """Coerce to float64 length n (NaN on failure)."""
    try:
        arr = np.asarray(x, dtype=np.float64)
        if arr.size != n:
            return np.full(n, np.nan, dtype=np.float64)
        return arr
    except Exception:
        return np.full(n, np.nan, dtype=np.float64)
