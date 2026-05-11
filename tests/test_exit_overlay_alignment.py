"""Unit tests for combiner-clone replay alignment (no heavy panel)."""

from __future__ import annotations

import pandas as pd
import pytest

from src.research.exit_overlay_alignment import (
    CloneReplayConfig,
    aggregate_alignment_per_config_slice,
    combiner_clone_long_walk,
    normalize_exit_reason,
)


def _one_session_bars() -> pd.DataFrame:
    ts = pd.date_range("2024-01-02 14:31", periods=5, freq="1min", tz="UTC")
    return pd.DataFrame(
        {
            "ts_utc": ts,
            "open": [100.0, 100.0, 100.0, 100.0, 100.0],
            "high": [101.2, 101.0, 101.0, 101.0, 101.0],
            "low": [99.5, 99.8, 99.8, 99.8, 99.8],
            "close": [100.2, 100.9, 100.9, 100.9, 100.9],
            "volume": [1000.0] * 5,
        }
    )


def test_normalize_exit_reason_strips_ex_prefix() -> None:
    assert normalize_exit_reason("EX_STOP") == "stop"
    assert normalize_exit_reason("target") == "target"


def test_combiner_clone_applies_exit_slip_on_target() -> None:
    bars = _one_session_bars()
    row = pd.Series(
        {
            "entry_ts_utc": bars["ts_utc"].iloc[0],
            "entry_price": 100.02,
            "stop_price": 99.0,
            "target_price": 101.0,
            "risk_per_share": 1.02,
            "target_r": 1.75,
            "target_mode_code": 1,
            "session_date": "2024-01-02",
            "exit_reason": "target",
            "exit_price": 100.99,
        }
    )
    cfg = CloneReplayConfig(
        config_id="t",
        start_bar_policy="entry_bar",
        entry_price_source="panel_entry_price",
        exit_price_source="simulated_bar_price",
        slippage_policy="apply_like_combiner",
        risk_policy="panel_risk_per_share",
        same_bar_policy="stop_first",
        forced_exit_policy="max_hold",
        target_policy="panel_target_price",
    )
    res = combiner_clone_long_walk(session_bars=bars, row=row, cfg=cfg)
    assert res.exit_reason == "target"
    assert res.exit_price == pytest.approx(100.99)
    assert res.r_multiple == pytest.approx((100.99 - 100.02) / 1.02)


def test_aggregate_alignment_labels_pass() -> None:
    df = pd.DataFrame(
        {
            "config_id": ["a", "a"],
            "start_bar_policy": ["entry_bar", "entry_bar"],
            "entry_price_source": ["panel_entry_price", "panel_entry_price"],
            "exit_price_source": ["simulated_bar_price", "simulated_bar_price"],
            "slippage_policy": ["apply_like_combiner", "apply_like_combiner"],
            "risk_policy": ["panel_risk_per_share", "panel_risk_per_share"],
            "same_bar_policy": ["stop_first", "stop_first"],
            "forced_exit_policy": ["max_hold", "max_hold"],
            "target_policy": ["panel_target_price", "panel_target_price"],
            "r_original": [1.0, 1.0],
            "r_replay": [1.01, 0.99],
            "exit_reason_match": [1.0, 1.0],
            "ambiguous_bar": [False, False],
        }
    )
    out = aggregate_alignment_per_config_slice(
        df,
        [
            "config_id",
            "start_bar_policy",
            "entry_price_source",
            "exit_price_source",
            "slippage_policy",
            "risk_policy",
            "same_bar_policy",
            "forced_exit_policy",
            "target_policy",
        ],
    )
    assert out.iloc[0]["label"] == "ALIGNMENT_PASS"
