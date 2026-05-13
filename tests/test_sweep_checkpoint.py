"""Checkpoint / resume and per-combo timing for real-symbol sweeps."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.backtest import sweep
from src.backtest.sweep import (
    SWEEP_PARTIAL_CSV,
    SWEEP_PROGRESS_JSON,
    SweepRunConfig,
    run_real_symbol_sweep,
    run_single_combo_from_signals,
)


def _tiny_pa_grid(tmp_path: Path) -> Path:
    p = tmp_path / "tiny_pa.yaml"
    p.write_text(
        """
strategy: pa_buy_sell_close_trend
fixed:
  features.orb_open_minutes: 15
  features.pa_regime_window: 30
  signal.require_vwap_side: false
  signal.block_climax: true
  signal.side: long_only
  signal.entry_start_minute: 60
  signal.entry_end_minute: 210
  signal.body_pct_min: 0.48
  signal.trend_score_min: 0.28
  risk.target_mode: fixed_r
  risk.atr_buffer_mult: 0.35
  risk.min_risk_per_share: 0.03
  risk.max_trades_per_day: 1
  risk.stop_mode: signal_low
  backtest.eod_exit_minute: 389
  backtest.quantity: 1.0
  backtest.commission_per_trade: 0.0
  backtest.slippage_per_share: 0.01
  backtest.recompute_target_from_entry: true
  backtest.max_hold_minutes: 55
grid:
  risk.target_r: [1.0, 1.35, 1.7]
""".strip(),
        encoding="utf-8",
    )
    return p


def test_real_sweep_timing_columns_qqq_short_window(tmp_path: Path) -> None:
    grid = _tiny_pa_grid(tmp_path)
    out = tmp_path / "s1"
    cfg = SweepRunConfig(
        strategy="pa_buy_sell_close_trend",
        symbol="QQQ",
        start="2024-01-02",
        end="2024-01-05",
        data_root="data/raw/ibkr",
        output_root=out,
        no_save=False,
        asset="equity",
        checkpoint_every=1,
        resume=False,
    )
    df = run_real_symbol_sweep(
        strategy_name="pa_buy_sell_close_trend",
        symbol="QQQ",
        asset="equity",
        start="2024-01-02",
        end="2024-01-05",
        data_dir="data/raw/ibkr",
        config_path=None,
        grid_path=str(grid),
        max_combos=None,
        dry_run=False,
        sweep_cfg=cfg,
    )
    assert len(df) == 3
    for col in (
        "combo_elapsed_sec",
        "combo_started_at_utc",
        "combo_finished_at_utc",
        "combo_index",
        "combo_count_total",
    ):
        assert col in df.columns
    assert all(df["combo_count_total"] == 3)
    assert (out / SWEEP_PROGRESS_JSON).is_file()
    prog = json.loads((out / SWEEP_PROGRESS_JSON).read_text(encoding="utf-8"))
    assert prog["status"] == "completed"
    assert not (out / SWEEP_PARTIAL_CSV).is_file()


def test_checkpoint_resume_skips_completed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    grid = _tiny_pa_grid(tmp_path)
    out = tmp_path / "s2"
    calls = {"n": 0}
    orig = run_single_combo_from_signals

    def boom(*a, **k):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("simulated_interrupt")
        return orig(*a, **k)

    monkeypatch.setattr(sweep, "run_single_combo_from_signals", boom)
    cfg = SweepRunConfig(
        output_root=out,
        no_save=False,
        checkpoint_every=1,
        resume=False,
    )
    with pytest.raises(RuntimeError, match="simulated_interrupt"):
        run_real_symbol_sweep(
            strategy_name="pa_buy_sell_close_trend",
            symbol="QQQ",
            asset="equity",
            start="2024-01-02",
            end="2024-01-05",
            data_dir="data/raw/ibkr",
            config_path=None,
            grid_path=str(grid),
            max_combos=None,
            dry_run=False,
            sweep_cfg=cfg,
        )
    monkeypatch.setattr(sweep, "run_single_combo_from_signals", orig)

    partial = out / SWEEP_PARTIAL_CSV
    assert partial.is_file()
    prev = pd.read_csv(partial)
    assert len(prev) == 1

    calls["n"] = 0

    def counting(*a, **k):
        calls["n"] += 1
        return orig(*a, **k)

    monkeypatch.setattr(sweep, "run_single_combo_from_signals", counting)
    cfg2 = SweepRunConfig(
        output_root=out,
        no_save=False,
        checkpoint_every=1,
        resume=True,
    )
    df = run_real_symbol_sweep(
        strategy_name="pa_buy_sell_close_trend",
        symbol="QQQ",
        asset="equity",
        start="2024-01-02",
        end="2024-01-05",
        data_dir="data/raw/ibkr",
        config_path=None,
        grid_path=str(grid),
        max_combos=None,
        dry_run=False,
        sweep_cfg=cfg2,
    )
    assert len(df) == 3
    assert calls["n"] == 2
