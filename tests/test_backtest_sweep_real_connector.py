"""Real-symbol canonical sweep wiring (no QQQ parquet in CI)."""

from __future__ import annotations

from unittest import mock

import numpy as np
import pandas as pd
import pytest

import src.backtest.sweep as sweep
from src.backtest.sweep import CanonicalSweepConfig, run_canonical_real_symbol_sweep


def _fake_bars_qqq(*, rows: int = 220) -> pd.DataFrame:
    rng = pd.date_range("2024-01-02 14:30", periods=rows, freq="min", tz="UTC")
    o = np.linspace(100.0, 101.0, rows)
    return pd.DataFrame(
        {
            "ts_utc": rng,
            "symbol": ["QQQ"] * rows,
            "open": o,
            "high": o + 0.4,
            "low": o - 0.4,
            "close": o + 0.05,
            "volume": np.full(rows, 1000, dtype=np.int64),
        }
    )


def test_run_canonical_real_symbol_sweep_dry_run_uses_monkeypatched_bars(monkeypatch):
    monkeypatch.setattr(sweep, "read_bars", lambda **kwargs: _fake_bars_qqq())

    cfg = CanonicalSweepConfig(strategy="orb_continuation", symbol="QQQ", start="2024-01-02", end="2024-01-02")
    with mock.patch("src.backtest.engine.run_strategy_backtest") as eng:
        df = run_canonical_real_symbol_sweep(
            strategy_name="orb_continuation",
            symbol="QQQ",
            asset="equity",
            start="2024-01-02",
            end="2024-01-02",
            data_dir="data/raw/ibkr",
            config_path=None,
            grid_path=None,
            max_combos=None,
            dry_run=True,
            sweep_cfg=cfg,
        )
    eng.assert_not_called()
    assert len(df) == 1
    assert df["notes"].iloc[0] == "dry_run"
    assert (df["engine"] == sweep.CANONICAL_ENGINE_LABEL).all()


def test_run_canonical_real_invokes_engine_when_not_dry_run(monkeypatch):
    monkeypatch.setattr(sweep, "read_bars", lambda **kwargs: _fake_bars_qqq())

    cfg = CanonicalSweepConfig(strategy="orb_continuation", symbol="QQQ", start="2024-01-02", end="2024-01-02")
    real = __import__("src.backtest.engine", fromlist=["run_strategy_backtest"]).run_strategy_backtest

    with mock.patch("src.backtest.sweep.run_strategy_backtest", wraps=real) as spy:
        run_canonical_real_symbol_sweep(
            strategy_name="orb_continuation",
            symbol="QQQ",
            asset="equity",
            start="2024-01-02",
            end="2024-01-02",
            data_dir="data/raw/ibkr",
            config_path=None,
            grid_path=None,
            max_combos=1,
            dry_run=False,
            sweep_cfg=cfg,
        )
    assert spy.call_count >= 1


def test_empty_bars_raises():
    cfg = CanonicalSweepConfig(strategy="orb_continuation", symbol="QQQ", start="2024-01-02", end="2024-01-02")
    with mock.patch("src.backtest.sweep.read_bars", lambda **kwargs: pd.DataFrame()):
        with pytest.raises(ValueError, match="No bars"):
            run_canonical_real_symbol_sweep(
                strategy_name="orb_continuation",
                symbol="QQQ",
                asset="equity",
                start="2024-01-02",
                end="2024-01-02",
                data_dir="data/raw/ibkr",
                config_path=None,
                grid_path=None,
                max_combos=None,
                dry_run=True,
                sweep_cfg=cfg,
            )


def test_max_combos_limits_grid(tmp_path, monkeypatch):
    monkeypatch.setattr(sweep, "read_bars", lambda **kwargs: _fake_bars_qqq())
    g = tmp_path / "grid.yaml"
    g.write_text("grid:\n  risk.target_r: [1.0, 1.5, 2.0]\n", encoding="utf-8")
    cfg = CanonicalSweepConfig(strategy="orb_continuation", symbol="QQQ", start="2024-01-02", end="2024-01-02")
    with mock.patch("src.backtest.engine.run_strategy_backtest"):
        df = run_canonical_real_symbol_sweep(
            strategy_name="orb_continuation",
            symbol="QQQ",
            asset="equity",
            start="2024-01-02",
            end="2024-01-02",
            data_dir="data/raw/ibkr",
            config_path=None,
            grid_path=str(g),
            max_combos=2,
            dry_run=True,
            sweep_cfg=cfg,
        )
    assert len(df) == 2
