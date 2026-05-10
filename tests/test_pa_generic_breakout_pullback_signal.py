"""Synthetic cases for pa_generic_breakout_pullback."""

from __future__ import annotations

import numpy as np

from src.strategies.loader import load_strategy
from tests.pa_batch_a_fixtures import build_pa_features


def _idx(feat) -> int:
    return len(feat) - 15


def _patch(feat, idx: int) -> None:
    rw = 60
    regw = 30
    rh = 100.0
    atr = float(feat.loc[idx, "atr_like_20"])
    if not np.isfinite(atr) or atr < 0.1:
        atr = 0.5
    feat.loc[idx, "minute_from_open"] = 200
    feat.loc[idx, f"pa_prior_high_{rw}"] = rh
    feat.loc[idx, f"pa_breakout_up_{rw}"] = np.int8(0)
    feat.loc[idx, f"pa_pullback_depth_atr_{rw}"] = 0.35
    feat.loc[idx, f"pa_followthrough_up_{rw}"] = np.int8(0)
    feat.loc[idx, f"pa_overlap_score_{regw}"] = 0.35
    feat.loc[idx, f"pa_range_high_{rw}"] = rh + 1.0
    feat.loc[idx, f"pa_range_low_{rw}"] = rh - 4.0
    feat.loc[idx, f"pa_range_mid_{rw}"] = rh - 1.5
    feat.loc[idx, f"pa_range_upper_third_{rw}"] = rh - 0.33
    feat.loc[idx, "close"] = rh - 0.2 * atr
    feat.loc[idx, "low"] = rh - 0.35 * atr
    feat.loc[idx, "high"] = rh + 0.1 * atr
    feat.loc[idx, "bull_reversal_bar"] = np.int8(1)
    for j in range(max(0, idx - 5), idx):
        feat.loc[feat.index[j], f"pa_breakout_up_{rw}"] = np.int8(1)
        feat.loc[feat.index[j], f"pa_followthrough_up_{rw}"] = np.int8(1)


def test_long_signal_fires() -> None:
    st = load_strategy("pa_generic_breakout_pullback")
    feat, cfg = build_pa_features("pa_generic_breakout_pullback")
    idx = _idx(feat)
    _patch(feat, idx)
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert arr["valid"][idx]


def test_no_recent_breakout_blocks() -> None:
    st = load_strategy("pa_generic_breakout_pullback")
    feat, cfg = build_pa_features("pa_generic_breakout_pullback")
    idx = _idx(feat)
    _patch(feat, idx)
    rw = 60
    for j in range(max(0, idx - 12), idx):
        feat.loc[feat.index[j], f"pa_breakout_up_{rw}"] = np.int8(0)
        feat.loc[feat.index[j], f"pa_followthrough_up_{rw}"] = np.int8(0)
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert not arr["valid"][idx]
