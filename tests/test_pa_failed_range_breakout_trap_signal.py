"""Synthetic long signal / block cases for pa_failed_range_breakout_trap."""

from __future__ import annotations

import numpy as np

from src.strategies.loader import load_strategy
from tests.pa_batch_a_fixtures import build_pa_features


def _patch_signal_row(feat, idx: int) -> None:
    rw = 60
    feat.loc[idx, "minute_from_open"] = 150
    feat.loc[idx, f"pa_followthrough_down_{rw}"] = np.int8(0)
    feat.loc[idx, f"pa_failed_breakout_down_{rw}"] = np.int8(1)
    feat.loc[idx, f"pa_close_back_inside_{rw}"] = np.int8(0)
    feat.loc[idx, "bull_reversal_bar"] = np.int8(0)
    feat.loc[idx, f"pa_trading_range_score_{rw}"] = 0.5
    feat.loc[idx, f"pa_range_high_{rw}"] = 102.0
    feat.loc[idx, f"pa_range_low_{rw}"] = 98.0
    feat.loc[idx, f"pa_range_mid_{rw}"] = 100.0
    feat.loc[idx, f"pa_range_upper_third_{rw}"] = 101.33
    feat.loc[idx, "close"] = 99.5
    feat.loc[idx, "low"] = 97.8
    feat.loc[idx, "high"] = 99.8


def test_long_signal_on_failed_breakdown_flag() -> None:
    st = load_strategy("pa_failed_range_breakout_trap")
    feat, cfg = build_pa_features("pa_failed_range_breakout_trap")
    idx = len(feat) - 8
    _patch_signal_row(feat, idx)
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert arr["valid"][idx]
    assert arr["side"][idx] == 1
    assert float(arr["stop"][idx]) < float(feat.loc[idx, "close"])
    assert float(arr["target_preview"][idx]) > float(feat.loc[idx, "close"])


def test_followthrough_down_blocks() -> None:
    st = load_strategy("pa_failed_range_breakout_trap")
    feat, cfg = build_pa_features("pa_failed_range_breakout_trap")
    idx = len(feat) - 8
    _patch_signal_row(feat, idx)
    feat.loc[idx, f"pa_followthrough_down_60"] = np.int8(1)
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert not arr["valid"][idx]
