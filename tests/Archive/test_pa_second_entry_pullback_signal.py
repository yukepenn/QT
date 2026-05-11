"""Synthetic cases for pa_second_entry_pullback."""

from __future__ import annotations

import numpy as np

from src.strategies.loader import load_strategy
from tests.pa_batch_a_fixtures import build_pa_features


def _idx(feat) -> int:
    return len(feat) - 12


def _patch(feat, idx: int) -> None:
    rw = 60
    feat.loc[idx, "minute_from_open"] = 120
    feat.loc[idx, f"pa_broad_bull_channel_score_{rw}"] = 0.42
    feat.loc[idx, f"pa_tight_bull_channel_score_{rw}"] = 0.35
    feat.loc[idx, f"pa_broad_bull_channel_score_30"] = 0.42
    feat.loc[idx, f"pa_tight_bull_channel_score_30"] = 0.35
    feat.loc[idx, f"pa_pullback_depth_atr_{rw}"] = 0.4
    feat.loc[idx, f"pa_higher_low_proxy_{rw}"] = np.int8(1)
    feat.loc[idx, f"pa_wedge_push_count_{rw}"] = 1.0
    feat.loc[idx, f"pa_range_high_{rw}"] = 104.0
    feat.loc[idx, f"pa_range_low_{rw}"] = 96.0
    feat.loc[idx, f"pa_range_mid_{rw}"] = 100.0
    feat.loc[idx, f"pa_range_upper_third_{rw}"] = 102.67
    feat.loc[idx, "close"] = 99.0
    feat.loc[idx, "low"] = 98.2
    feat.loc[idx, "high"] = 99.5
    feat.loc[idx, "bull_reversal_bar"] = np.int8(1)


def test_long_signal_fires() -> None:
    st = load_strategy("pa_second_entry_pullback")
    feat, cfg = build_pa_features("pa_second_entry_pullback")
    idx = _idx(feat)
    _patch(feat, idx)
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert arr["valid"][idx]


def test_no_two_leg_blocks() -> None:
    st = load_strategy("pa_second_entry_pullback")
    feat, cfg = build_pa_features("pa_second_entry_pullback")
    idx = _idx(feat)
    _patch(feat, idx)
    feat.loc[idx, f"pa_higher_low_proxy_60"] = np.int8(0)
    feat.loc[idx, f"pa_wedge_push_count_60"] = 0.5
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert not arr["valid"][idx]
