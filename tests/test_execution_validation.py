import math

from src.backtest.execution import (
    actual_risk_per_share,
    is_finite_price,
    valid_fixed_price_target_side,
    valid_stop_side,
    valid_target_r,
    validate_trade_setup,
)


def test_is_finite_price():
    assert is_finite_price(1.0)
    assert not is_finite_price(float("nan"))
    assert not is_finite_price(float("inf"))


def test_stop_side_validation():
    assert valid_stop_side(1, entry=10.0, stop=9.0)
    assert not valid_stop_side(1, entry=10.0, stop=10.0)
    assert not valid_stop_side(1, entry=10.0, stop=11.0)
    assert valid_stop_side(-1, entry=10.0, stop=11.0)
    assert not valid_stop_side(-1, entry=10.0, stop=10.0)
    assert not valid_stop_side(-1, entry=10.0, stop=9.0)


def test_fixed_price_target_side_validation():
    assert valid_fixed_price_target_side(1, entry=10.0, target=11.0)
    assert not valid_fixed_price_target_side(1, entry=10.0, target=9.0)
    assert valid_fixed_price_target_side(-1, entry=10.0, target=9.0)
    assert not valid_fixed_price_target_side(-1, entry=10.0, target=11.0)


def test_target_r_validation():
    assert valid_target_r(1.0)
    assert not valid_target_r(0.0)
    assert not valid_target_r(-1.0)
    assert not valid_target_r(float("nan"))


def test_actual_risk_per_share():
    assert actual_risk_per_share(1, 10.0, 9.5) == 0.5
    assert math.isnan(actual_risk_per_share(1, 10.0, 10.5))
    assert actual_risk_per_share(-1, 10.0, 10.5) == 0.5
    assert math.isnan(actual_risk_per_share(-1, 10.0, 9.5))


def test_validate_trade_setup_fixed_r():
    ok, reason, risk, tgt = validate_trade_setup(
        side=1,
        entry=10.0,
        stop=9.5,
        target_mode="fixed_r",
        target_preview=0.0,
        target_r=2.0,
        min_risk_per_share=0.0,
    )
    assert ok and reason == "ok"
    assert risk == 0.5
    assert tgt == 11.0


def test_validate_trade_setup_fixed_price_wrong_side():
    ok, reason, risk, tgt = validate_trade_setup(
        side=1,
        entry=10.0,
        stop=9.5,
        target_mode="fixed_price",
        target_preview=9.0,
        target_r=None,
        min_risk_per_share=0.0,
    )
    assert not ok
    assert reason == "invalid_target_side"
    assert risk == 0.5
    assert math.isnan(tgt)


def test_validate_trade_setup_rejects_wrong_side_stop():
    ok, reason, _, _ = validate_trade_setup(
        side=1,
        entry=10.0,
        stop=10.1,
        target_mode="fixed_r",
        target_preview=0.0,
        target_r=1.0,
        min_risk_per_share=0.0,
    )
    assert not ok
    assert reason == "invalid_stop_side"

