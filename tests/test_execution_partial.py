import numpy as np
import pandas as pd
import pytest

from src.execution.path import simulate_trade_path
from src.execution.policy import default_intraday_policy
from src.execution.types import ExitPlan, ScaleOutRule, TradeIntent


def test_scale_out_partial():
    n = 25
    o = np.linspace(100, 110, n)
    h = o + 1.0
    l = o - 0.2
    c = o + 0.5
    df = pd.DataFrame(
        {"open": o, "high": h, "low": l, "close": c, "minute_from_open": np.arange(n, dtype=np.int32)}
    )
    pol = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, eod_exit_minute=999)
    plan = ExitPlan(scale_outs=(ScaleOutRule(trigger_r=0.5, exit_fraction=0.5),))
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=1,
        signal_idx=0,
        entry_idx=1,
        stop_price=99.0,
        target_price=200.0,
        target_r=50.0,
        risk_per_share=1.0,
        max_hold_bars=None,
        management_mode="runner",
    )
    res = simulate_trade_path(df, intent, pol, plan)
    assert res.ok
    assert len(res.legs) >= 1
    assert abs(res.total_qty_frac - 1.0) < 1e-9


def test_scale_out_fill_trigger_price_vs_close():
    n = 10
    o = np.array([100.0] * n)
    h = np.array([100.0, 101.0, 101.0, 101.0, 101.0, 101.0, 101.0, 101.0, 101.0, 101.0])
    l = np.array([100.0, 99.5, 99.5, 99.5, 99.5, 99.5, 99.5, 99.5, 99.5, 99.5])
    c = np.array([100.0, 100.2, 100.2, 100.2, 100.2, 100.2, 100.2, 100.2, 100.2, 100.2])
    df = pd.DataFrame(
        {"open": o, "high": h, "low": l, "close": c, "minute_from_open": np.arange(n, dtype=np.int32)}
    )
    plan = ExitPlan(scale_outs=(ScaleOutRule(trigger_r=0.5, exit_fraction=1.0),))
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=1,
        signal_idx=0,
        entry_idx=1,
        stop_price=99.0,
        target_price=200.0,
        target_r=50.0,
        risk_per_share=1.0,
        max_hold_bars=None,
        management_mode="runner",
    )
    pol_close = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, eod_exit_minute=999)
    pol_trig = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, eod_exit_minute=999)
    from dataclasses import replace

    pol_trig = replace(pol_trig, scale_fill_policy="trigger_price")
    r_close = simulate_trade_path(df, intent, pol_close, plan)
    r_trig = simulate_trade_path(df, intent, pol_trig, plan)
    assert r_close.ok and r_trig.ok
    assert r_close.legs[0].exit_price == pytest.approx(100.2)
    assert r_trig.legs[0].exit_price == pytest.approx(100.5)


def test_stop_first_dominates_scale_even_with_trigger_price_policy():
    df = pd.DataFrame(
        {
            "open": [100.0, 100.0],
            "high": [100.0, 101.0],
            "low": [100.0, 94.0],
            "close": [100.0, 95.0],
            "minute_from_open": np.array([0, 1], dtype=np.int32),
        }
    )
    pol = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, eod_exit_minute=999)
    from dataclasses import replace

    pol = replace(pol, scale_fill_policy="trigger_price")
    plan = ExitPlan(scale_outs=(ScaleOutRule(trigger_r=0.5, exit_fraction=1.0),))
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=1,
        signal_idx=0,
        entry_idx=0,
        stop_price=99.0,
        target_price=200.0,
        target_r=50.0,
        risk_per_share=1.0,
        max_hold_bars=None,
        management_mode="runner",
    )
    res = simulate_trade_path(df, intent, pol, plan)
    assert res.ok
    assert res.exit_reason.name == "STOP"
