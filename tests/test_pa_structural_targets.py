"""PA structural targets: document fixed-R equivalence for structural modes (Option A)."""

from __future__ import annotations

import math

import pytest

from src.backtest.fast import TM_FIXED_R
from src.strategies.strategy.pa_batch_a_utils import long_stop_target


def test_fixed_r_target_returns_tm_fixed_r():
    got = long_stop_target(
        close=100.0,
        low=99.0,
        high=101.0,
        atr=0.5,
        vwap=float("nan"),
        stop_mode="signal_low",
        target_mode="fixed_r",
        target_r=1.5,
        atr_buf_mult=0.35,
        range_low=98.0,
        range_mid=99.5,
        range_high=102.0,
        upper_third=100.5,
    )
    assert got is not None
    _sl, _tg, tmc, tr = got
    assert int(tmc) == int(TM_FIXED_R)
    assert tr == pytest.approx(1.5)


def test_range_mid_maps_to_fixed_r_code_not_literal_fixed_px():
    """Structural mode range_mid is converted to an effective R multiple at signal bar (long_stop_target)."""
    got = long_stop_target(
        close=100.0,
        low=99.5,
        high=101.0,
        atr=0.5,
        vwap=101.2,
        stop_mode="signal_low",
        target_mode="range_mid",
        target_r=1.5,
        atr_buf_mult=0.35,
        range_low=98.0,
        range_mid=103.0,
        range_high=105.0,
        upper_third=101.0,
    )
    assert got is not None
    _sl, tgt, tmc, tr = got
    assert int(tmc) == int(TM_FIXED_R)
    assert tgt > 100.0
    assert math.isfinite(tr)


def test_invalid_geometry_returns_none():
    got = long_stop_target(
        close=100.0,
        low=101.0,
        high=102.0,
        atr=0.5,
        vwap=100.0,
        stop_mode="signal_low",
        target_mode="fixed_r",
        target_r=1.5,
        atr_buf_mult=0.35,
        range_low=98.0,
        range_mid=99.0,
        range_high=102.0,
        upper_third=100.5,
    )
    assert got is None
