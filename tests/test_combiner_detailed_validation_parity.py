"""Combiner legacy path should reject setups consistently with validate_trade_setup."""

from __future__ import annotations

import numpy as np
import pytest

from src.backtest.execution import validate_trade_setup


def test_validate_trade_setup_long_wrong_side_stop():
    ok, reason, _, _ = validate_trade_setup(
        side=1,
        entry=100.0,
        stop=101.0,
        target_mode="fixed_r",
        target_preview=105.0,
        target_r=1.5,
        min_risk_per_share=0.0,
    )
    assert not ok
    assert reason == "invalid_stop_side"


def test_validate_trade_setup_short_wrong_side_stop():
    ok, reason, _, _ = validate_trade_setup(
        side=-1,
        entry=100.0,
        stop=99.0,
        target_mode="fixed_r",
        target_preview=95.0,
        target_r=1.5,
        min_risk_per_share=0.0,
    )
    assert not ok
    assert reason == "invalid_stop_side"


def test_validate_trade_setup_invalid_target_r():
    ok, reason, _, _ = validate_trade_setup(
        side=1,
        entry=100.0,
        stop=99.0,
        target_mode="fixed_r",
        target_preview=105.0,
        target_r=-1.0,
        min_risk_per_share=0.0,
    )
    assert not ok
    assert reason == "invalid_target_r"


def test_validate_trade_setup_fixed_price_wrong_side_target():
    ok, reason, _, _ = validate_trade_setup(
        side=1,
        entry=100.0,
        stop=99.0,
        target_mode="fixed_price",
        target_preview=99.5,
        target_r=None,
        min_risk_per_share=0.0,
    )
    assert not ok
    assert reason == "invalid_target_side"


def test_validate_trade_setup_risk_too_small():
    ok, reason, risk, _ = validate_trade_setup(
        side=1,
        entry=100.0,
        stop=99.9,
        target_mode="fixed_r",
        target_preview=101.0,
        target_r=1.5,
        min_risk_per_share=0.5,
    )
    assert not ok
    assert reason == "risk_too_small"
    assert np.isfinite(risk)


def test_validate_trade_setup_ok_fixed_r_matches_manual_risk():
    ok, reason, risk, tgt = validate_trade_setup(
        side=1,
        entry=100.0,
        stop=99.0,
        target_mode="fixed_r",
        target_preview=0.0,
        target_r=2.0,
        min_risk_per_share=0.0,
    )
    assert ok and reason == "ok"
    assert risk == pytest.approx(1.0)
    assert tgt == pytest.approx(102.0)
