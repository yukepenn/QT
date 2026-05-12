"""Active ``src/backtest`` must match the agreed five-module layout."""

from __future__ import annotations

from pathlib import Path

_ALLOWED = {
    "__init__.py",
    "engine.py",
    "sweep.py",
    "signal_adapter.py",
    "strategy_runner.py",
    "metrics.py",
}


def test_backtest_dir_only_allowed_py_files():
    root = Path(__file__).resolve().parents[1] / "src" / "backtest"
    py_files = {p.name for p in root.iterdir() if p.suffix == ".py"}
    assert py_files == _ALLOWED, py_files - _ALLOWED
