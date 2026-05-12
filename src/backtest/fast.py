"""Shim: re-export target-mode codes only (strategies use int8 array labels).

For bar-array prep use ``src.combiner.bar_arrays.prepare_backtest_arrays``.
"""

from __future__ import annotations

from src.backtest.constants import TM_FIXED_PX, TM_FIXED_R, TM_NONE

__all__ = ["TM_FIXED_PX", "TM_FIXED_R", "TM_NONE"]
