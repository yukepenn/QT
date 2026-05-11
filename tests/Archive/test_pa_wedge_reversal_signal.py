"""Synthetic cases for pa_wedge_reversal."""

from __future__ import annotations

import numpy as np

from src.strategies.loader import load_strategy
from tests.pa_batch_a_fixtures import build_pa_features


def _idx(feat) -> int:
    return len(feat) - 12


def _patch(feat, idx: int) -> None:
    rw = 60
    feat.loc[idx, "minute_from_open"] = 110
    feat.loc[idx, f"pa_wedge_push_count_{rw}"] = 3.0
    feat.loc[idx, f"pa_broad_bear_channel_score_{rw}"] = 0.3
    feat.loc[idx, f"pa_tight_bear_channel_score_{rw}"] = 0.25
    feat.loc[idx, f"pa_broad_bear_channel_score_30"] = 0.3
    feat.loc[idx, f"pa_tight_bear_channel_score_30"] = 0.25
    feat.loc[idx, f"pa_leg_direction_{rw}"] = np.int8(-1)
    feat.loc[idx, f"pa_range_high_{rw}"] = 103.0
    feat.loc[idx, f"pa_range_low_{rw}"] = 95.0
    feat.loc[idx, f"pa_range_mid_{rw}"] = 99.0
    feat.loc[idx, f"pa_range_upper_third_{rw}"] = 101.67
    feat.loc[idx, "close"] = 97.0
    feat.loc[idx, "low"] = 96.2
    feat.loc[idx, "high"] = 97.8
    feat.loc[idx, "vwap"] = 100.0
    feat.loc[idx, "bull_reversal_bar"] = np.int8(1)


def test_long_signal_fires() -> None:
    st = load_strategy("pa_wedge_reversal")
    feat, cfg = build_pa_features("pa_wedge_reversal")
    idx = _idx(feat)
    _patch(feat, idx)
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert arr["valid"][idx]


def test_up_leg_blocks() -> None:
    st = load_strategy("pa_wedge_reversal")
    feat, cfg = build_pa_features("pa_wedge_reversal")
    idx = _idx(feat)
    _patch(feat, idx)
    feat.loc[idx, f"pa_leg_direction_60"] = np.int8(1)
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert not arr["valid"][idx]
