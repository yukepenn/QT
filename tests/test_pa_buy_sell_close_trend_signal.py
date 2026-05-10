"""Synthetic cases for pa_buy_sell_close_trend."""

from __future__ import annotations

import numpy as np

from src.strategies.loader import load_strategy
from tests.pa_batch_a_fixtures import build_pa_features


def _idx(feat) -> int:
    return len(feat) - 12


def _patch(feat, idx: int) -> None:
    rw = 60
    regw = 30
    feat.loc[idx, "minute_from_open"] = 150
    feat.loc[idx, "close_near_high"] = np.int8(1)
    feat.loc[idx, "body_pct"] = 0.62
    feat.loc[idx, "consecutive_bull_closes_3"] = np.int8(1)
    feat.loc[idx, f"trend_score_{regw}"] = 0.55
    feat.loc[idx, f"pa_climax_score_{rw}"] = 0.25
    feat.loc[idx, f"pa_range_high_{rw}"] = 105.0
    feat.loc[idx, f"pa_range_low_{rw}"] = 97.0
    feat.loc[idx, f"pa_range_mid_{rw}"] = 101.0
    feat.loc[idx, f"pa_range_upper_third_{rw}"] = 103.67
    feat.loc[idx, "close"] = 102.0
    feat.loc[idx, "low"] = 101.2
    feat.loc[idx, "high"] = 102.4
    feat.loc[idx, "vwap"] = 100.5


def test_long_signal_fires() -> None:
    st = load_strategy("pa_buy_sell_close_trend")
    feat, cfg = build_pa_features("pa_buy_sell_close_trend")
    idx = _idx(feat)
    _patch(feat, idx)
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert arr["valid"][idx]


def test_low_trend_blocks() -> None:
    st = load_strategy("pa_buy_sell_close_trend")
    feat, cfg = build_pa_features("pa_buy_sell_close_trend")
    idx = _idx(feat)
    _patch(feat, idx)
    feat.loc[idx, "trend_score_30"] = 0.05
    arr = st.generate_signal_arrays_from_context(st.prepare_signal_context(feat, cfg), cfg)
    assert not arr["valid"][idx]
