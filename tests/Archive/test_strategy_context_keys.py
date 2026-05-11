"""Context cache keys change when prepare_signal_context-driving params change."""

from __future__ import annotations

import copy

from src.strategies.loader import load_strategy, load_strategy_config


def _cfg(name: str) -> dict:
    return copy.deepcopy(load_strategy_config(name))


def test_failed_orb_context_key_atr_column():
    s = load_strategy("failed_orb")
    a = _cfg("failed_orb")
    b = copy.deepcopy(a)
    b.setdefault("signal", {})["atr_column"] = "atr_like_5"
    assert s.context_key(a) != s.context_key(b)


def test_gap_acceptance_context_key_atr():
    s = load_strategy("gap_acceptance_failure")
    a = _cfg("gap_acceptance_failure")
    b = copy.deepcopy(a)
    b.setdefault("signal", {})["atr_column"] = "atr_like_5"
    assert s.context_key(a) != s.context_key(b)


def test_prior_day_context_key_level_buffer():
    s = load_strategy("prior_day_level_trap")
    a = _cfg("prior_day_level_trap")
    b = copy.deepcopy(a)
    b.setdefault("signal", {})["level_buffer_atr"] = 0.25
    assert s.context_key(a) != s.context_key(b)


def test_afternoon_context_key_morning_end_and_atr():
    s = load_strategy("afternoon_continuation")
    a = _cfg("afternoon_continuation")
    b = copy.deepcopy(a)
    b.setdefault("features", {})["morning_end_minute"] = 99
    assert s.context_key(a) != s.context_key(b)
    c = copy.deepcopy(a)
    c.setdefault("signal", {})["atr_column"] = "atr_like_5"
    assert s.context_key(a) != s.context_key(c)


def test_vwap_reclaim_context_key_mb():
    s = load_strategy("vwap_reclaim_reject")
    a = _cfg("vwap_reclaim_reject")
    b = copy.deepcopy(a)
    b.setdefault("signal", {})["min_bars_wrong_side"] = 20
    assert s.context_key(a) != s.context_key(b)


def test_vwap_trend_context_key_trend_window():
    s = load_strategy("vwap_trend_pullback")
    a = _cfg("vwap_trend_pullback")
    b = copy.deepcopy(a)
    b.setdefault("signal", {})["trend_window"] = 30
    assert s.context_key(a) != s.context_key(b)


def test_orb_retest_context_key_bars():
    s = load_strategy("orb_retest_continuation")
    a = _cfg("orb_retest_continuation")
    b = copy.deepcopy(a)
    b.setdefault("signal", {})["max_retest_bars"] = 20
    assert s.context_key(a) != s.context_key(b)


def test_vwap_reversal_context_key_swing():
    s = load_strategy("vwap_reversal")
    a = _cfg("vwap_reversal")
    b = copy.deepcopy(a)
    b.setdefault("risk", {})["swing_lookback"] = 10
    assert s.context_key(a) != s.context_key(b)


def test_midday_compression_context_key_window():
    s = load_strategy("midday_compression_breakout")
    a = _cfg("midday_compression_breakout")
    b = copy.deepcopy(a)
    b.setdefault("features", {})["compression_window"] = 45
    assert s.context_key(a) != s.context_key(b)


def test_normalized_param_gating_changes_failed_orb():
    s = load_strategy("failed_orb")
    a = _cfg("failed_orb")
    b = copy.deepcopy(a)
    b.setdefault("signal", {})["require_vwap_reclaim"] = True
    assert s.normalized_param_key(a) != s.normalized_param_key(b)


def test_afternoon_normalized_no_midday_window_in_key():
    s = load_strategy("afternoon_continuation")
    a = _cfg("afternoon_continuation")
    b = copy.deepcopy(a)
    b.setdefault("features", {})["midday_window"] = 999
    assert s.normalized_param_key(a) == s.normalized_param_key(b)
