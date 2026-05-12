"""Canonical Layer 1 sweep (reference engine), no legacy Numba."""

from __future__ import annotations

from unittest import mock

import pandas as pd
import pytest

import src.backtest.sweep as sweep
from src.backtest.sweep import CanonicalSweepConfig, expand_param_grid, run_synthetic_canonical_smoke


def test_expand_param_grid_deterministic_order():
    g = {"a": [1, 2], "b": [10, 20]}
    rows = expand_param_grid(g)
    assert rows == [
        {"a": 1, "b": 10},
        {"a": 1, "b": 20},
        {"a": 2, "b": 10},
        {"a": 2, "b": 20},
    ]


def test_config_hash_order_independent():
    h1 = sweep.config_hash({"z": 1, "a": 2})
    h2 = sweep.config_hash({"a": 2, "z": 1})
    assert h1 == h2


def test_synthetic_canonical_sweep_at_least_two_rows():
    df = run_synthetic_canonical_smoke()
    assert len(df) >= 2
    assert list(df["combo_id"]) == ["combo_0000", "combo_0001"]


def test_synthetic_sweep_invokes_canonical_execution_path():
    import src.backtest.engine as eng

    real_sim = eng.simulate_trade_path

    with mock.patch.object(eng, "simulate_trade_path", wraps=real_sim) as spy:
        run_synthetic_canonical_smoke()
    assert spy.call_count == 2


def test_main_smoke_exit_zero():
    assert sweep.main(["--smoke"]) == 0


def test_run_single_combo_requires_valid_canonical_frame():
    bad = sweep._synthetic_ohlcv_and_signals(target_r=2.0).copy()
    bad.loc[sweep.SYNTHETIC_SIGNAL_ROW, "sig_target_mode"] = "bogus"
    with pytest.raises(ValueError, match="canonical signal validation failed"):
        sweep.run_single_canonical_combo(
            bad,
            {"sig_target_r": 1.0},
            combo_id="x",
            strategy="synthetic_smoke",
            sweep_cfg=CanonicalSweepConfig(),
        )


def test_data_root_without_smoke_returns_nonzero():
    assert sweep.main(["--data-root", "C:/fake"]) == 3
