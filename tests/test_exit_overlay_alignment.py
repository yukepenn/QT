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
        max_hold_priority="intrabar_first",
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
            "max_hold_priority": ["intrabar_first", "intrabar_first"],
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
            "max_hold_priority",
        ],
    )
    assert out.iloc[0]["label"] == "ALIGNMENT_PASS"


def _bars_max_hold_terminal_touch_target() -> pd.DataFrame:
    ts = pd.date_range("2024-01-02 14:31", periods=3, freq="1min", tz="UTC")
    return pd.DataFrame(
        {
            "ts_utc": ts,
            "open": [100.0, 100.0, 100.0],
            "high": [100.1, 100.1, 101.2],
            "low": [99.9, 99.9, 99.9],
            "close": [100.0, 100.0, 100.5],
            "volume": [1000.0, 1000.0, 1000.0],
        }
    )


def _bars_max_hold_terminal_touch_stop() -> pd.DataFrame:
    ts = pd.date_range("2024-01-02 14:31", periods=3, freq="1min", tz="UTC")
    return pd.DataFrame(
        {
            "ts_utc": ts,
            "open": [100.0, 100.0, 100.0],
            "high": [100.1, 100.1, 100.1],
            "low": [99.9, 99.9, 98.8],
            "close": [100.0, 100.0, 99.5],
            "volume": [1000.0, 1000.0, 1000.0],
        }
    )


def _mh_base_cfg(priority: str) -> CloneReplayConfig:
    return CloneReplayConfig(
        config_id="mh",
        start_bar_policy="entry_bar",
        entry_price_source="panel_entry_price",
        exit_price_source="simulated_bar_price",
        slippage_policy="apply_like_combiner",
        risk_policy="panel_risk_per_share",
        same_bar_policy="stop_first",
        forced_exit_policy="panel_exit_idx",
        target_policy="panel_target_price",
        max_hold_priority=priority,  # type: ignore[arg-type]
    )


def test_max_hold_priority_intrabar_vs_forced_on_terminal_target() -> None:
    bars = _bars_max_hold_terminal_touch_target()
    row = pd.Series(
        {
            "entry_ts_utc": bars["ts_utc"].iloc[0],
            "entry_price": 100.0,
            "stop_price": 99.0,
            "target_price": 101.0,
            "risk_per_share": 1.0,
            "target_r": 1.0,
            "target_mode_code": 1,
            "session_date": "2024-01-02",
            "exit_idx": 2,
            "exit_reason": "max_hold",
            "exit_price": 100.48,
        }
    )
    intr = combiner_clone_long_walk(
        session_bars=bars,
        row=row,
        cfg=_mh_base_cfg("intrabar_first"),
        max_hold_minutes=3,
    )
    forced = combiner_clone_long_walk(
        session_bars=bars,
        row=row,
        cfg=_mh_base_cfg("forced_first_on_terminal_bar"),
        max_hold_minutes=3,
    )
    panel = combiner_clone_long_walk(
        session_bars=bars,
        row=row,
        cfg=_mh_base_cfg("panel_exit_reason_authoritative"),
        max_hold_minutes=3,
    )
    assert intr.exit_reason == "target"
    assert forced.exit_reason == "max_hold"
    assert panel.exit_reason == "max_hold"


def test_max_hold_priority_intrabar_vs_forced_on_terminal_stop() -> None:
    bars = _bars_max_hold_terminal_touch_stop()
    row = pd.Series(
        {
            "entry_ts_utc": bars["ts_utc"].iloc[0],
            "entry_price": 100.0,
            "stop_price": 99.0,
            "target_price": 102.0,
            "risk_per_share": 1.0,
            "target_r": 1.0,
            "target_mode_code": 1,
            "session_date": "2024-01-02",
            "exit_idx": 2,
            "exit_reason": "max_hold",
            "exit_price": 99.52,
        }
    )
    intr = combiner_clone_long_walk(
        session_bars=bars,
        row=row,
        cfg=_mh_base_cfg("intrabar_first"),
        max_hold_minutes=3,
    )
    forced = combiner_clone_long_walk(
        session_bars=bars,
        row=row,
        cfg=_mh_base_cfg("forced_first_on_terminal_bar"),
        max_hold_minutes=3,
    )
    assert intr.exit_reason == "stop"
    assert forced.exit_reason == "max_hold"


def test_max_hold_priority_target_before_terminal_all_modes_target() -> None:
    ts = pd.date_range("2024-01-02 14:31", periods=3, freq="1min", tz="UTC")
    bars = pd.DataFrame(
        {
            "ts_utc": ts,
            "open": [100.0, 100.0, 100.0],
            "high": [100.1, 101.2, 100.1],
            "low": [99.9, 99.9, 99.9],
            "close": [100.0, 100.0, 100.0],
            "volume": [1000.0, 1000.0, 1000.0],
        }
    )
    row = pd.Series(
        {
            "entry_ts_utc": bars["ts_utc"].iloc[0],
            "entry_price": 100.0,
            "stop_price": 99.0,
            "target_price": 101.0,
            "risk_per_share": 1.0,
            "target_r": 1.0,
            "target_mode_code": 1,
            "session_date": "2024-01-02",
            "exit_idx": 2,
            "exit_reason": "max_hold",
            "exit_price": 100.48,
        }
    )
    for pri in ("intrabar_first", "forced_first_on_terminal_bar", "panel_exit_reason_authoritative"):
        out = combiner_clone_long_walk(
            session_bars=bars,
            row=row,
            cfg=_mh_base_cfg(pri),
            max_hold_minutes=3,
        )
        assert out.exit_reason == "target"
        # Exit on bar index 1 => bars_held == 2 from entry at bar 0
        assert out.bars_held == 2


def test_aggregate_skip_terminal_bar_conflicts_excludes_rows() -> None:
    df = pd.DataFrame(
        {
            "config_id": ["c", "c"],
            "profile_id": ["p", "p"],
            "window": ["w", "w"],
            "start_bar_policy": ["entry_bar", "entry_bar"],
            "entry_price_source": ["panel_entry_price", "panel_entry_price"],
            "exit_price_source": ["simulated_bar_price", "simulated_bar_price"],
            "slippage_policy": ["apply_like_combiner", "apply_like_combiner"],
            "risk_policy": ["panel_risk_per_share", "panel_risk_per_share"],
            "same_bar_policy": ["stop_first", "stop_first"],
            "forced_exit_policy": ["panel_exit_idx", "panel_exit_idx"],
            "target_policy": ["panel_target_price", "panel_target_price"],
            "max_hold_priority": ["skip_terminal_bar_conflicts", "skip_terminal_bar_conflicts"],
            "r_original": [1.0, 1.0],
            "r_replay": [1.0, 2.0],
            "r_diff": [0.0, 1.0],
            "panel_exit_reason": ["max_hold", "max_hold"],
            "exit_reason_replay": ["max_hold", "target"],
        }
    )
    out = aggregate_alignment_per_config_slice(
        df,
        group_cols=[
            "config_id",
            "profile_id",
            "window",
            "start_bar_policy",
            "entry_price_source",
            "exit_price_source",
            "slippage_policy",
            "risk_policy",
            "same_bar_policy",
            "forced_exit_policy",
            "target_policy",
            "max_hold_priority",
        ],
    )
    assert len(out) == 1
    assert out.iloc[0]["trades"] == 1
    assert out.iloc[0]["mean_abs_r_diff"] == 0.0


def test_clone_replay_config_serialization_max_hold_priority() -> None:
    cfg = CloneReplayConfig(
        config_id="x",
        start_bar_policy="entry_bar",
        entry_price_source="panel_entry_price",
        exit_price_source="simulated_bar_price",
        slippage_policy="apply_like_combiner",
        risk_policy="panel_risk_per_share",
        same_bar_policy="stop_first",
        forced_exit_policy="panel_exit_idx",
        target_policy="panel_target_price",
        max_hold_priority="forced_first_on_terminal_bar",
    )
    d = cfg.to_dict()
    assert d["max_hold_priority"] == "forced_first_on_terminal_bar"
    cfg2 = CloneReplayConfig.from_mapping(d)
    assert cfg2.max_hold_priority == "forced_first_on_terminal_bar"
