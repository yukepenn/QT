"""Synthetic long signal / block cases for pa_mtr_reversal."""

from __future__ import annotations

import numpy as np

from src.strategies.loader import load_strategy
from tests.pa_batch_a_fixtures import build_pa_features


def _patch_signal_row(feat, idx: int) -> None:
    rw = 60
    feat.loc[idx, "minute_from_open"] = 160
    feat.loc[idx, f"pa_tight_bear_channel_score_{rw}"] = 0.55
    feat.loc[idx, f"pa_tight_bear_channel_score_30"] = 0.55
    feat.loc[idx, f"pa_failed_breakout_down_{rw}"] = np.int8(1)
    feat.loc[idx, f"pa_prior_low_{rw}"] = 100.0
    feat.loc[idx, f"pa_prior_high_{rw}"] = 104.0
    feat.loc[idx, f"pa_wedge_push_count_{rw}"] = 1.0
    feat.loc[idx, f"pa_range_high_{rw}"] = 104.0
    feat.loc[idx, f"pa_range_low_{rw}"] = 98.0
    feat.loc[idx, f"pa_range_mid_{rw}"] = 101.0
    feat.loc[idx, f"pa_range_upper_third_{rw}"] = 102.0
    feat.loc[idx, "bull_reversal_bar"] = np.int8(1)
    feat.loc[idx, "close"] = 101.0
    feat.loc[idx, "low"] = 99.9
    feat.loc[idx, "high"] = 101.3


def test_long_signal_after_bear_proxy_and_failed_break() -> None:
    st = load_strategy("pa_mtr_reversal")
    feat, cfg = build_pa_features("pa_mtr_reversal")
    idx = len(feat) - 6
    _patch_signal_row(feat, idx)
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert arr["valid"][idx]
    assert float(arr["stop"][idx]) < float(feat.loc[idx, "close"])
    assert float(arr["target_preview"][idx]) > float(feat.loc[idx, "close"])


def test_missing_bull_reversal_blocks() -> None:
    st = load_strategy("pa_mtr_reversal")
    feat, cfg = build_pa_features("pa_mtr_reversal")
    idx = len(feat) - 6
    _patch_signal_row(feat, idx)
    feat.loc[idx, "bull_reversal_bar"] = np.int8(0)
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert not arr["valid"][idx]
