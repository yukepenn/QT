"""Synthetic cases for pa_broad_channel_zone."""

from __future__ import annotations

import numpy as np

from src.strategies.loader import load_strategy
from tests.pa_batch_a_fixtures import build_pa_features


def _base_idx(feat) -> int:
    return len(feat) - 12


def _patch(feat, idx: int, *, minute: int = 120, bbull: float = 0.45, close: float = 97.0) -> None:
    rw = 60
    feat.loc[idx, "minute_from_open"] = minute
    feat.loc[idx, f"pa_broad_bull_channel_score_{rw}"] = bbull
    feat.loc[idx, f"pa_broad_bull_channel_score_30"] = bbull
    feat.loc[idx, f"pa_range_high_{rw}"] = 104.0
    feat.loc[idx, f"pa_range_low_{rw}"] = 95.0
    feat.loc[idx, f"pa_range_lower_third_{rw}"] = 98.0
    feat.loc[idx, f"pa_pullback_depth_atr_{rw}"] = 0.35
    feat.loc[idx, f"pa_climax_score_{rw}"] = 0.2
    feat.loc[idx, "close"] = close
    feat.loc[idx, "low"] = close - 0.6
    feat.loc[idx, "high"] = close + 0.4
    feat.loc[idx, "bull_reversal_bar"] = np.int8(1)


def test_long_signal_fires() -> None:
    st = load_strategy("pa_broad_channel_zone")
    feat, cfg = build_pa_features("pa_broad_channel_zone")
    idx = _base_idx(feat)
    _patch(feat, idx)
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert arr["valid"][idx]
    assert arr["side"][idx] == 1
    assert float(arr["stop"][idx]) < float(feat.loc[idx, "close"])


def test_low_broad_score_blocks() -> None:
    st = load_strategy("pa_broad_channel_zone")
    feat, cfg = build_pa_features("pa_broad_channel_zone")
    idx = _base_idx(feat)
    _patch(feat, idx, bbull=0.05)
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert not arr["valid"][idx]


def test_pre_window_blocks() -> None:
    st = load_strategy("pa_broad_channel_zone")
    feat, cfg = build_pa_features("pa_broad_channel_zone")
    idx = _base_idx(feat)
    _patch(feat, idx, minute=30)
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert not arr["valid"][idx]
