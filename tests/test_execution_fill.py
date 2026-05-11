import pytest

from src.execution.fill import entry_fill_price, exit_fill_price
from src.execution.types import ExitReason, Side


def test_long_entry_slip():
    assert entry_fill_price(100.0, Side.LONG, 0.25) == 100.25


def test_short_entry_slip():
    assert entry_fill_price(100.0, Side.SHORT, 0.25) == 99.75


def test_long_stop_exit_slip():
    assert exit_fill_price(99.0, Side.LONG, ExitReason.STOP, 0.1) == pytest.approx(98.9)


def test_long_target_exit_slip():
    assert exit_fill_price(110.0, Side.LONG, ExitReason.TARGET, 0.1) == pytest.approx(109.9)


def test_long_time_exit_slip():
    assert exit_fill_price(105.0, Side.LONG, ExitReason.EOD, 0.2) == pytest.approx(104.8)


def test_short_mirror_stop():
    assert exit_fill_price(101.0, Side.SHORT, ExitReason.STOP, 0.1) == pytest.approx(101.1)


def test_short_mirror_target():
    assert exit_fill_price(90.0, Side.SHORT, ExitReason.TARGET, 0.1) == pytest.approx(90.1)
