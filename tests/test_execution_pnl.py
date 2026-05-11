import pytest

from src.execution.pnl import apply_commission_per_share, cost_as_r, leg_r, weighted_r
from src.execution.types import ExitReason, FillLeg, Side


def test_leg_r_long():
    assert leg_r(Side.LONG, entry=100.0, exit_px=102.0, risk=1.0) == 2.0


def test_leg_r_short():
    assert leg_r(Side.SHORT, entry=100.0, exit_px=98.0, risk=1.0) == 2.0


def test_commission():
    net = apply_commission_per_share(2.0, commission_per_trade=1.0, qty=2.0)
    assert net == 1.5


def test_cost_as_r():
    assert cost_as_r(1.0, 2.0, 0.5) == 1.0


def test_weighted_partial():
    legs = (
        FillLeg(0.5, 100.0, 102.0, 2.0, ExitReason.SCALE_OUT),
        FillLeg(0.5, 100.0, 104.0, 4.0, ExitReason.TARGET),
    )
    assert weighted_r(legs) == pytest.approx(3.0)
