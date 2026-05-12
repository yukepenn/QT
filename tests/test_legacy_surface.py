"""Surface checks for removed shims and relocated helpers."""

import importlib.util

import pandas as pd

from src.combiner.precompute import prepare_backtest_arrays
from src.execution.types import TM_FIXED_PX, TM_FIXED_R, TM_NONE


def test_target_mode_codes_from_execution_types():
    assert TM_FIXED_R is not None
    assert TM_NONE is not None
    assert TM_FIXED_PX is not None


def test_backtest_fast_module_removed():
    spec = importlib.util.find_spec("src.backtest.fast")
    assert spec is None


def test_prepare_backtest_arrays_on_precompute():
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
