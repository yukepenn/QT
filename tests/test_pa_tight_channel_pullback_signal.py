"""Synthetic long signal / block cases for pa_tight_channel_pullback."""

from __future__ import annotations

import numpy as np

from src.strategies.loader import load_strategy
from tests.pa_batch_a_fixtures import build_pa_features


def _patch_signal_row(feat, idx: int) -> None:
    rw = 30
    feat.loc[idx, "minute_from_open"] = 140
    feat.loc[idx, f"pa_tight_bull_channel_score_{rw}"] = 0.55
    feat.loc[idx, f"pa_pullback_depth_atr_{rw}"] = 0.4
    feat.loc[idx, f"pa_climax_score_{rw}"] = 0.2
    feat.loc[idx, f"pa_range_high_{rw}"] = 103.0
    feat.loc[idx, f"pa_range_low_{rw}"] = 99.0
    feat.loc[idx, f"pa_range_mid_{rw}"] = 101.0
    feat.loc[idx, f"pa_range_upper_third_{rw}"] = 102.33
    feat.loc[idx, "bull_reversal_bar"] = np.int8(1)
    feat.loc[idx, "close_near_high"] = np.int8(0)
    feat.loc[idx, "close"] = 101.0
    feat.loc[idx, "low"] = 100.4
    feat.loc[idx, "high"] = 101.2
    feat.loc[idx, "vwap"] = 100.0


def test_long_signal_in_tight_channel_pullback() -> None:
    st = load_strategy("pa_tight_channel_pullback")
    feat, cfg = build_pa_features("pa_tight_channel_pullback")
    idx = len(feat) - 7
    feat["minute_from_open"] = 30
    _patch_signal_row(feat, idx)
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert arr["valid"][idx]
    assert float(arr["stop"][idx]) < float(feat.loc[idx, "close"])
    assert float(arr["target_preview"][idx]) > float(feat.loc[idx, "close"])


def test_climax_block_when_enabled() -> None:
    st = load_strategy("pa_tight_channel_pullback")
    feat, cfg = build_pa_features("pa_tight_channel_pullback")
    idx = len(feat) - 7
    feat["minute_from_open"] = 30
    _patch_signal_row(feat, idx)
    feat.loc[idx, "pa_climax_score_30"] = 0.99
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert not arr["valid"][idx]
