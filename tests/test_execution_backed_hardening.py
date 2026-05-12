"""Regression tests for execution-backed Layer2 + execution policy hardening."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.combiner.adapter import simulate_combiner_canonical
from src.combiner.candidate import Candidate
from src.combiner.simulator import CombinerConfig
from src.combiner.state import CombinerState
from src.combiner.trade_intent_adapter import execution_policy_from_combiner_cfg, simulate_selected_trade
from src.execution.materialize import materialize_trade_levels
from src.execution.path import simulate_trade_path
from src.execution.policy import default_intraday_policy
from src.execution.types import ExitPlan, ScaleOutRule, TM_FIXED_R, TradeIntent


def _cand(*, cid: str = "HARDEN_001", priority: int = 10) -> Candidate:
    return Candidate(
        candidate_id=cid,
        strategy="synthetic",
        asset="equity",
        symbol="QQQ",
        candidate_rank=1,
        source_sweep_path="",
        source_results_csv="",
        params_hash="00",
        config={},
        metrics={},
        metadata={},
        selection={},
        family="test_family",
        conflict_group="g",
        default_priority=priority,
        default_active_start_minute=0,
        default_active_end_minute=389,
        warning="",
    )


def test_session_boundary_skips_next_session_entry():
    """Signal on last bar of session A must not enter on first bar of session B."""
    n = 6
    o = np.linspace(100.0, 100.5, n)
    bt = {
        "open": o,
        "high": o + 0.2,
        "low": o - 0.2,
        "close": o + 0.05,
        "minute": np.array([100, 101, 102, 0, 1, 2], dtype=np.int32),
        "session_id": np.zeros(n, dtype=np.int32),
        "n": n,
    }
    ts = pd.date_range("2024-01-02 15:00", periods=n, freq="min", tz="UTC")
    sd = np.array(["2024-01-02"] * 3 + ["2024-01-03"] * 3, dtype=object)
    meta = {"ts_utc": ts.to_numpy(), "session_date": sd, "minute_from_open": bt["minute"]}
    nc = 1
    side = np.zeros((nc, n), dtype=np.int8)
    valid = np.zeros((nc, n), dtype=np.int8)
    stop = np.full((nc, n), np.nan)
    tp = np.full((nc, n), np.nan)
    tmc = np.full((nc, n), int(TM_FIXED_R), dtype=np.int8)
    tr = np.full((nc, n), 2.0)
    risk = np.full((nc, n), 1.0)
    cross_sig = 2
    side[0, cross_sig] = 1
    valid[0, cross_sig] = 1
    stop[0, cross_sig] = 99.0
    mats = {"side": side, "valid": valid, "stop": stop, "target_preview": tp, "target_mode_code": tmc, "target_r": tr, "risk_preview": risk}
    cfg = CombinerConfig(slippage_per_share=0.0, commission_per_trade=0.0, max_trades_per_day=5)
    out_cross = simulate_combiner_canonical(
        backtest_arrays=bt,
        candidate_arrays=mats,
        candidates=[_cand()],
        meta_arrays=meta,
        combiner_cfg=cfg,
        enabled_mask=np.ones(nc, dtype=np.int8),
        max_hold_per_candidate=np.array([-1], dtype=np.int32),
        recompute_target=np.zeros(nc, dtype=np.int8),
        quantity_per_candidate=np.ones(nc),
        min_risk_per_candidate=np.zeros(nc),
        priority_float=np.array([10.0]),
        score_float=np.zeros(nc),
        rank_int=np.zeros(nc, dtype=np.int32),
        active_start=np.zeros(nc, dtype=np.int32),
        active_end=np.full(nc, 389, dtype=np.int32),
    )
    assert len(out_cross["trades_df"]) == 0

    same_sig = 1
    side[:] = 0
    valid[:] = 0
    side[0, same_sig] = 1
    valid[0, same_sig] = 1
    stop[0, same_sig] = 99.0
    out_same = simulate_combiner_canonical(
        backtest_arrays=bt,
        candidate_arrays=mats,
        candidates=[_cand()],
        meta_arrays=meta,
        combiner_cfg=cfg,
        enabled_mask=np.ones(nc, dtype=np.int8),
        max_hold_per_candidate=np.array([-1], dtype=np.int32),
        recompute_target=np.zeros(nc, dtype=np.int8),
        quantity_per_candidate=np.ones(nc),
        min_risk_per_candidate=np.zeros(nc),
        priority_float=np.array([10.0]),
        score_float=np.zeros(nc),
        rank_int=np.zeros(nc, dtype=np.int32),
        active_start=np.zeros(nc, dtype=np.int32),
        active_end=np.full(nc, 389, dtype=np.int32),
    )
    assert len(out_same["trades_df"]) >= 1


def test_reset_day_clears_cooldown_and_open_positions():
    s = CombinerState()
    s.ensure_day("2024-01-02")
    s.start_cooldown(from_bar=388, cooldown_bars=15)
    assert not s.can_enter_bar(390)
    s.reset_day("2024-01-03")
    assert s.cooldown_until_bar == -1
    assert s.open_positions == 0
    assert s.can_enter_bar(390)
    assert s.trades_today == 0
    assert s.day_realized_r == 0.0


def test_materialize_rejects_risk_below_policy_min():
    df = pd.DataFrame(
        {
            "open": [100.0, 100.1],
            "high": [100.1, 100.2],
            "low": [99.9, 100.0],
            "close": [100.05, 100.15],
            "minute_from_open": np.array([0, 1], dtype=np.int32),
        }
    )
    pol_lo = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, eod_exit_minute=999, min_risk_per_share=0.5)
    pol_hi = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, eod_exit_minute=999, min_risk_per_share=0.01)
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=1,
        signal_idx=0,
        entry_idx=1,
        stop_price=99.9,
        max_hold_bars=None,
        management_mode="none",
        target_mode="fixed_r",
        target_r=2.0,
        risk_per_share=0.1,
        qty=1.0,
    )
    bad = materialize_trade_levels(df, intent, pol_lo, ExitPlan())
    assert not bad.ok
    assert bad.reject_reason == "risk_too_small"
    good = materialize_trade_levels(df, intent, pol_hi, ExitPlan())
    assert good.ok


def test_simulate_trade_path_min_risk_rejection_stable_reason():
    df = pd.DataFrame(
        {
            "open": [100.0, 100.1],
            "high": [100.1, 100.2],
            "low": [99.9, 100.0],
            "close": [100.05, 100.15],
            "minute_from_open": np.array([0, 1], dtype=np.int32),
        }
    )
    pol = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, eod_exit_minute=999, min_risk_per_share=2.0)
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=1,
        signal_idx=0,
        entry_idx=1,
        stop_price=99.5,
        max_hold_bars=None,
        management_mode="none",
        target_mode="fixed_r",
        target_r=2.0,
        risk_per_share=0.4,
        qty=1.0,
    )
    res = simulate_trade_path(df, intent, pol, ExitPlan())
    assert not res.ok
    assert "risk_too_small" in str(res.reject_reason)


def test_simulate_selected_trade_min_risk_floor_and_cfg_max():
    df = pd.DataFrame(
        {
            "open": [100.0, 100.1],
            "high": [100.1, 100.2],
            "low": [99.9, 100.0],
            "close": [100.05, 100.15],
            "minute_from_open": np.array([0, 1], dtype=np.int32),
        }
    )
    cfg = CombinerConfig(slippage_per_share=0.0, commission_per_trade=0.0, min_risk_per_share=0.5)
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=1,
        signal_idx=0,
        entry_idx=1,
        stop_price=99.9,
        max_hold_bars=None,
        management_mode="none",
        target_mode="fixed_r",
        target_r=2.0,
        risk_per_share=0.2,
        qty=1.0,
    )
    rej = simulate_selected_trade(df, intent, combiner_cfg=cfg, min_risk_per_share_floor=0.0)
    assert not rej.ok
    assert "risk_too_small" in str(rej.reject_reason)
    cfg_lo = CombinerConfig(slippage_per_share=0.0, commission_per_trade=0.0, min_risk_per_share=0.0)
    ok2 = simulate_selected_trade(df, intent, combiner_cfg=cfg_lo, min_risk_per_share_floor=0.0)
    assert ok2.ok


def test_execution_policy_floor_maxes_with_cfg():
    cfg = CombinerConfig(slippage_per_share=0.0, commission_per_trade=0.0, min_risk_per_share=0.03)
    p1 = execution_policy_from_combiner_cfg(cfg, min_risk_per_share_floor=0.10)
    assert p1.min_risk_per_share == pytest.approx(0.10)
    p2 = execution_policy_from_combiner_cfg(cfg, min_risk_per_share_floor=0.01)
    assert p2.min_risk_per_share == pytest.approx(0.03)


def test_scale_out_fraction_applies_to_remaining_qty():
    n = 40
    o = np.linspace(100.0, 110.0, n)
    h = o + 2.0
    l = o - 0.5
    c = o + 0.3
    df = pd.DataFrame(
        {"open": o, "high": h, "low": l, "close": c, "minute_from_open": np.arange(n, dtype=np.int32)}
    )
    pol = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, eod_exit_minute=999)
    plan = ExitPlan(
        scale_outs=(
            ScaleOutRule(trigger_r=0.5, exit_fraction=0.5),
            ScaleOutRule(trigger_r=1.0, exit_fraction=0.5),
        )
    )
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=1,
        signal_idx=0,
        entry_idx=1,
        stop_price=95.0,
        max_hold_bars=30,
        management_mode="runner",
        target_mode="fixed_r",
        target_r=50.0,
        risk_per_share=1.0,
        qty=1.0,
    )
    res = simulate_trade_path(df, intent, pol, plan)
    assert res.ok
    scale_legs = [lg for lg in res.legs if lg.reason.name == "SCALE_OUT"]
    assert len(scale_legs) == 2
    assert scale_legs[0].qty_frac == pytest.approx(0.5)
    assert scale_legs[1].qty_frac == pytest.approx(0.25)
    assert res.total_qty_frac == pytest.approx(1.0)
