"""Synthetic long signal / block cases for pa_trading_range_bls_hs."""

from __future__ import annotations

import numpy as np

from src.strategies.loader import load_strategy
from tests.pa_batch_a_fixtures import build_pa_features


def _patch_signal_row(feat, idx: int) -> None:
    rw = 60
    regw = 30
    feat.loc[idx, "minute_from_open"] = 120
    feat.loc[idx, f"pa_trading_range_score_{rw}"] = 0.55
    feat.loc[idx, f"pa_trading_range_score_30"] = 0.55
    feat.loc[idx, f"pa_range_high_{rw}"] = 104.0
    feat.loc[idx, f"pa_range_low_{rw}"] = 96.0
    feat.loc[idx, f"pa_range_mid_{rw}"] = 100.0
    feat.loc[idx, f"pa_range_upper_third_{rw}"] = 102.67
    feat.loc[idx, f"pa_range_lower_third_{rw}"] = 98.67
    feat.loc[idx, f"pa_range_width_atr_{rw}"] = 1.2
    feat.loc[idx, f"pa_failed_breakout_down_{rw}"] = np.int8(0)
    feat.loc[idx, "close"] = 98.0
    feat.loc[idx, "low"] = 97.5
    feat.loc[idx, "high"] = 98.6
    feat.loc[idx, "bull_reversal_bar"] = np.int8(1)
    feat.loc[idx, "lower_wick_pct"] = 0.2
    feat.loc[idx, "upper_wick_pct"] = 0.1
    feat.loc[idx, f"range_efficiency_{regw}"] = 0.4


def test_long_signal_fires_with_geometry() -> None:
    st = load_strategy("pa_trading_range_bls_hs")
    feat, cfg = build_pa_features("pa_trading_range_bls_hs")
    idx = len(feat) - 10
    _patch_signal_row(feat, idx)
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert arr["valid"][idx]
    assert arr["side"][idx] == 1
    assert float(arr["stop"][idx]) < float(feat.loc[idx, "close"])
    assert float(arr["target_preview"][idx]) > float(feat.loc[idx, "close"])


def test_low_trading_range_score_blocks() -> None:
    st = load_strategy("pa_trading_range_bls_hs")
    feat, cfg = build_pa_features("pa_trading_range_bls_hs")
    idx = len(feat) - 10
    _patch_signal_row(feat, idx)
    feat.loc[idx, f"pa_trading_range_score_60"] = 0.05
    feat.loc[idx, f"pa_trading_range_score_30"] = 0.05
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert not arr["valid"][idx]


def test_pre_entry_window_blocks() -> None:
    st = load_strategy("pa_trading_range_bls_hs")
    feat, cfg = build_pa_features("pa_trading_range_bls_hs")
    idx = len(feat) - 10
    _patch_signal_row(feat, idx)
    feat.loc[idx, "minute_from_open"] = 30
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert not arr["valid"][idx]
