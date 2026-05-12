"""Target-mode integer codes for legacy Numba signal arrays (strategy layer).

**Do not** use this module for backtest accounting. Canonical execution is
``src.execution.path.simulate_trade_path``. Numba array kernels live in
``src.backtest.legacy.fast_legacy``; future acceleration belongs in
``src.execution.fast_path`` after parity tests.

This file exposes only the three ``TM_*`` constants strategies embed in
signal arrays. For ``prepare_backtest_arrays`` / ``run_fast_backtest_from_arrays``
import ``src.backtest.legacy.fast_legacy`` explicitly.
"""

from __future__ import annotations

from src.backtest.legacy.fast_legacy import TM_FIXED_PX, TM_FIXED_R, TM_NONE

__all__ = ["TM_FIXED_PX", "TM_FIXED_R", "TM_NONE"]


def __getattr__(name: str):
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}. "
        "Import prepare_backtest_arrays / run_fast_backtest_from_arrays from "
        "src.backtest.legacy.fast_legacy, or use src.execution for canonical accounting."
    )
