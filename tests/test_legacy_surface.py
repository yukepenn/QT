"""Top-level backtest ``fast`` re-exports target-mode codes only."""

import pytest

from src.combiner.bar_arrays import prepare_backtest_arrays


def test_backtest_fast_exposes_only_tm_constants():
    from src.backtest.fast import TM_FIXED_PX, TM_FIXED_R, TM_NONE

    assert TM_FIXED_R is not None
    assert TM_NONE is not None
    assert TM_FIXED_PX is not None


def test_backtest_fast_rejects_unknown_attributes():
    import src.backtest.fast as fast

    with pytest.raises(AttributeError):
        _ = fast.prepare_backtest_arrays  # type: ignore[attr-defined]


def test_prepare_backtest_arrays_importable_from_combiner_bar_arrays():
    import pandas as pd

    df = pd.DataFrame(
        {
            "ts_utc": pd.date_range("2024-01-02", periods=3, freq="min", tz="UTC"),
            "ts_ny": pd.date_range("2024-01-02", periods=3, freq="min"),
            "session_date": ["2024-01-02"] * 3,
            "minute_from_open": [0, 1, 2],
            "open": [1.0, 1.0, 1.0],
            "high": [1.1, 1.1, 1.1],
            "low": [0.9, 0.9, 0.9],
            "close": [1.0, 1.0, 1.0],
        }
    )
    ar = prepare_backtest_arrays(df)
    assert int(ar["n"]) == 3
