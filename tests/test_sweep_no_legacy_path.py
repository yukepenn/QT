"""Mainline sweep must not invoke archived Numba sweep."""

from __future__ import annotations

import pytest

import src.backtest.sweep as sweep


def test_default_main_returns_nonzero():
    assert sweep.main([]) != 0


def test_validate_testing_grid_runs_without_archive_import():
    from src.strategies.loader import load_testing_config

    testing = load_testing_config("orb_continuation")
    sweep.validate_testing_grid_for_strategy("orb_continuation", testing)


def test_strategy_registry_count_and_priority_strategies_load():
    from src.strategies.loader import available_strategies, load_strategy

    names = available_strategies()
    assert len(names) == 35
    for sid in ("pa_buy_sell_close_trend", "gap_acceptance_failure", "cci_extreme_snapback"):
        cls = load_strategy(sid)
        assert cls.name == sid
