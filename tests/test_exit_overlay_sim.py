"""Unit tests for exit_overlay_sim (no heavy panel data)."""

from __future__ import annotations

import pandas as pd
import pytest

from src.research.exit_overlay_sim import (
    AmbiguityPolicy,
    _intrabar_resolution,
    causal_atr14,
    causal_vwap,
    simulate_long_overlay,
)


def _session_bars() -> pd.DataFrame:
    # Two bars after synthetic entry at bar 0; 1R = 1.0 -> target 2.0, stop 98
    ts = pd.date_range("2024-01-02 14:31", periods=3, freq="1min", tz="UTC")
    return pd.DataFrame(
        {
            "ts_utc": ts,
            "open": [100.0, 100.5, 101.0],
            "high": [100.5, 102.0, 101.0],
            "low": [99.5, 99.0, 100.5],
            "close": [100.2, 101.5, 100.8],
            "volume": [1000.0, 1000.0, 1000.0],
        }
    )


def test_intrabar_stop_first() -> None:
    res, amb = _intrabar_resolution(low=99.0, high=101.0, stop=99.5, target=100.5, policy=AmbiguityPolicy.stop_first)
    assert amb
    assert res == "stop"


def test_intrabar_target_first_sensitivity() -> None:
    res, amb = _intrabar_resolution(low=99.0, high=101.0, stop=99.5, target=100.5, policy=AmbiguityPolicy.target_first)
    assert amb
    assert res == "target"


def test_causal_vwap_monotone_weights() -> None:
    h = pd.Series([10.0, 10.0])
    l = pd.Series([10.0, 10.0])
    c = pd.Series([10.0, 10.0])
    v = pd.Series([1.0, 1.0])
    out = causal_vwap(h.to_numpy(), l.to_numpy(), c.to_numpy(), v.to_numpy())
    assert out[0] == pytest.approx(10.0)
    assert out[1] == pytest.approx(10.0)


def test_causal_atr_positive() -> None:
    h = [10.0, 11.0]
    l = [9.0, 10.0]
    c = [9.5, 10.5]
    out = causal_atr14(pd.Series(h).to_numpy(), pd.Series(l).to_numpy(), pd.Series(c).to_numpy())
    assert out[0] > 0 and out[1] > 0


def test_fixed_target_hit_target_before_stop() -> None:
    bars = _session_bars()
    r = simulate_long_overlay(
        session_bars=bars,
        entry_ts_utc=bars["ts_utc"].iloc[0],
        entry_price=100.0,
        stop_price=98.0,
        target_price=101.0,
        risk_per_share=1.0,
        overlay_id="fixed_target_replay",
        ambiguity=AmbiguityPolicy.stop_first,
        row=None,
    )
    assert r.exit_reason == "target"
    assert r.r_multiple == pytest.approx(1.0)


def test_fixed_target_stop_first_same_bar() -> None:
    bars = pd.DataFrame(
        {
            "ts_utc": pd.date_range("2024-01-02 14:31", periods=2, freq="1min", tz="UTC"),
            "open": [100.0, 100.0],
            "high": [101.0, 100.0],
            "low": [97.0, 100.0],
            "close": [99.0, 100.0],
            "volume": [1000.0, 1000.0],
        }
    )
    # stop 98, target 101 — same bar hits both
    r = simulate_long_overlay(
        session_bars=bars,
        entry_ts_utc=bars["ts_utc"].iloc[0],
        entry_price=100.0,
        stop_price=98.0,
        target_price=101.0,
        risk_per_share=1.0,
        overlay_id="fixed_target_replay",
        ambiguity=AmbiguityPolicy.stop_first,
        row=None,
    )
    assert r.exit_reason == "stop"
    assert r.ambiguous_bar is True


def test_max_hold_tighten_exits_at_cap() -> None:
    ts = pd.date_range("2024-01-02 14:31", periods=40, freq="1min", tz="UTC")
    bars = pd.DataFrame(
        {
            "ts_utc": ts,
            "open": [100.0] * 40,
            "high": [100.2] * 40,
            "low": [99.9] * 40,
            "close": [100.1] * 40,
            "volume": [100.0] * 40,
        }
    )
    r = simulate_long_overlay(
        session_bars=bars,
        entry_ts_utc=bars["ts_utc"].iloc[0],
        entry_price=100.0,
        stop_price=98.0,
        target_price=200.0,
        risk_per_share=1.0,
        overlay_id="max_hold_tighten_30",
        ambiguity=AmbiguityPolicy.stop_first,
        row=None,
    )
    assert r.exit_reason == "max_hold_tighten"
    assert r.bars_held == 30


def test_no_followthrough_triggers() -> None:
    ts = pd.date_range("2024-01-02 14:31", periods=8, freq="1min", tz="UTC")
    bars = pd.DataFrame(
        {
            "ts_utc": ts,
            "open": [100.0] * 8,
            "high": [100.05] * 8,
            "low": [99.95] * 8,
            "close": [100.0] * 8,
            "volume": [100.0] * 8,
        }
    )
    r = simulate_long_overlay(
        session_bars=bars,
        entry_ts_utc=bars["ts_utc"].iloc[0],
        entry_price=100.0,
        stop_price=98.0,
        target_price=200.0,
        risk_per_share=1.0,
        overlay_id="no_followthrough_exit_3bars",
        ambiguity=AmbiguityPolicy.stop_first,
        row=None,
    )
    assert r.exit_reason == "no_followthrough"
    assert r.bars_held == 3
