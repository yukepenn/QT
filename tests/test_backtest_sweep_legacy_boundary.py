"""Mainline sweep CLI must not run legacy Numba unless ``--legacy``."""

import pytest

import src.backtest.sweep as sweep


def test_default_main_returns_nonzero_without_legacy():
    assert sweep.main([]) != 0


def test_canonical_help_returns_zero():
    assert sweep.main(["--canonical-help"]) == 0


def test_run_canonical_sweep_placeholder_raises():
    with pytest.raises(NotImplementedError, match="Canonical sweep"):
        sweep.run_canonical_sweep_placeholder()


def test_validate_testing_grid_delegates_to_legacy():
    """Compatibility wrapper still reaches legacy implementation."""
    from src.strategies.loader import load_testing_config

    testing = load_testing_config("orb_continuation")
    sweep.validate_testing_grid_for_strategy("orb_continuation", testing)
