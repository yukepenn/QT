"""Backtest package. Prefer ``src.backtest.engine`` for canonical runs; legacy Numba under ``src.backtest.legacy``."""

from __future__ import annotations

from typing import Any

__all__ = [
    "BacktestConfig",
    "run_backtest",
    "run_strategy_backtest",
    "summarize_trades",
]


def __getattr__(name: str) -> Any:
    if name in ("BacktestConfig", "run_backtest", "run_strategy_backtest"):
        from src.backtest import engine as _engine

        return getattr(_engine, name)
    if name == "summarize_trades":
        from src.backtest import metrics as _metrics

        return getattr(_metrics, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
