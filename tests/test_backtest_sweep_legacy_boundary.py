"""Mainline sweep CLI must not run legacy Numba unless ``--legacy`` is first."""

from __future__ import annotations

from unittest import mock

import pytest

import src.backtest.sweep as sweep


def test_default_main_returns_nonzero_without_legacy():
    assert sweep.main([]) != 0


def test_canonical_help_returns_zero():
    assert sweep.main(["--canonical-help"]) == 0


def test_validate_testing_grid_delegates_to_legacy():
    """Compatibility wrapper still reaches legacy implementation."""
    from src.strategies.loader import load_testing_config

    testing = load_testing_config("orb_continuation")
    sweep.validate_testing_grid_for_strategy("orb_continuation", testing)


def test_legacy_first_argv_token_delegates_with_remaining_args():
    with mock.patch("src.backtest.legacy.sweep_legacy.main", return_value=0) as leg:
        rc = sweep.main(["--legacy", "--help"])
    assert rc == 0
    leg.assert_called_once_with(["--help"])


def test_default_argv_does_not_touch_legacy_sweep_main():
    with mock.patch("src.backtest.legacy.sweep_legacy.main") as leg:
        sweep.main([])
    leg.assert_not_called()


def test_strategy_registry_count_and_priority_strategies_load():
    from src.strategies.loader import available_strategies, load_strategy

    names = available_strategies()
    assert len(names) == 35
    for sid in ("pa_buy_sell_close_trend", "gap_acceptance_failure", "cci_extreme_snapback"):
        cls = load_strategy(sid)
        assert cls.name == sid
