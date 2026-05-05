import pandas as pd

from src.backtest.metrics import max_drawdown


def test_max_drawdown_empty():
    assert max_drawdown(pd.Series([], dtype=float)) == 0.0


def test_max_drawdown_all_up():
    s = pd.Series([1.0, 2.0, 3.0])
    assert max_drawdown(s) == 0.0


def test_max_drawdown_first_loss_counts_from_zero():
    s = pd.Series([-1.0])
    assert max_drawdown(s) == -1.0


def test_max_drawdown_negative_then_recover():
    s = pd.Series([-1.0, -0.5, 0.2])
    assert max_drawdown(s) == -1.0


def test_max_drawdown_peak_then_crash():
    s = pd.Series([2.0, 1.0, 3.0, -1.0])
    assert max_drawdown(s) == -4.0


def test_max_drawdown_all_negative():
    s = pd.Series([-2.0, -1.0, -3.0, 0.0])
    assert max_drawdown(s) == -3.0

