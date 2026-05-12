"""Top-level backtest ``fast`` must not wildcard-export legacy accounting."""

import pytest


def test_backtest_fast_exposes_only_tm_constants():
    from src.backtest.fast import TM_FIXED_PX, TM_FIXED_R, TM_NONE

    assert TM_FIXED_R is not None
    assert TM_NONE is not None
    assert TM_FIXED_PX is not None


def test_backtest_fast_rejects_prepare_backtest_arrays():
    import src.backtest.fast as fast

    with pytest.raises(AttributeError, match="legacy.fast_legacy"):
        _ = fast.prepare_backtest_arrays  # type: ignore[attr-defined]


def test_legacy_fast_legacy_importable():
    from src.backtest.legacy import fast_legacy as fl

    assert callable(fl.prepare_backtest_arrays)
    assert callable(fl.run_fast_backtest_from_arrays)
