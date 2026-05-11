"""Synthetic cases for pa_climax_reversal."""

from __future__ import annotations

import numpy as np

from src.strategies.loader import load_strategy
from tests.pa_batch_a_fixtures import build_pa_features


def _idx(feat) -> int:
    return len(feat) - 12


def _patch(feat, idx: int) -> None:
    rw = 60
    feat.loc[idx, "minute_from_open"] = 100
    feat.loc[idx, f"pa_tight_bear_channel_score_{rw}"] = 0.35
    feat.loc[idx, f"pa_broad_bear_channel_score_{rw}"] = 0.2
    feat.loc[idx, f"pa_tight_bear_channel_score_30"] = 0.35
    feat.loc[idx, f"pa_broad_bear_channel_score_30"] = 0.2
    feat.loc[idx, f"pa_climax_score_{rw}"] = 0.62
    feat.loc[idx, f"pa_bar_range_expansion_{rw}"] = 1.5
    feat.loc[idx, "pa_distance_from_vwap_atr"] = -0.4
    feat.loc[idx, f"pa_followthrough_down_{rw}"] = np.int8(0)
    feat.loc[idx, f"pa_close_back_inside_{rw}"] = np.int8(1)
    feat.loc[idx, f"pa_range_high_{rw}"] = 102.0
    feat.loc[idx, f"pa_range_low_{rw}"] = 94.0
    feat.loc[idx, f"pa_range_mid_{rw}"] = 98.0
    feat.loc[idx, f"pa_range_upper_third_{rw}"] = 100.67
    feat.loc[idx, "close"] = 96.5
    feat.loc[idx, "low"] = 95.8
    feat.loc[idx, "high"] = 97.0
    feat.loc[idx, "vwap"] = 99.0
    feat.loc[idx, "bull_reversal_bar"] = np.int8(1)


def test_long_signal_fires() -> None:
    st = load_strategy("pa_climax_reversal")
    feat, cfg = build_pa_features("pa_climax_reversal")
    idx = _idx(feat)
    _patch(feat, idx)
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert arr["valid"][idx]
    assert arr["side"][idx] == 1


def test_bear_context_blocks() -> None:
    st = load_strategy("pa_climax_reversal")
    feat, cfg = build_pa_features("pa_climax_reversal")
    idx = _idx(feat)
    _patch(feat, idx)
    feat.loc[idx, f"pa_tight_bear_channel_score_60"] = 0.0
    feat.loc[idx, f"pa_broad_bear_channel_score_60"] = 0.0
    feat.loc[idx, f"pa_tight_bear_channel_score_30"] = 0.0
    feat.loc[idx, f"pa_broad_bear_channel_score_30"] = 0.0
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert not arr["valid"][idx]
