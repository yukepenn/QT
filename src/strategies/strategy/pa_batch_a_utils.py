"""Backward-compatible re-exports for PA Batch A helpers.

.. deprecated::
    Import from ``src.strategies.common.pa`` in new code. This module remains so existing
    strategy plugins and scripts keep working without import churn.
"""

from __future__ import annotations

from src.strategies.common.pa import (
    atr_col_name,
    finalize_long_signals_df,
    long_stop_target,
    pa_range_window,
    pa_regime_window,
    signals_df_from_arrays,
)

__all__ = [
    "atr_col_name",
    "finalize_long_signals_df",
    "long_stop_target",
    "pa_range_window",
    "pa_regime_window",
    "signals_df_from_arrays",
]
