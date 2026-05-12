"""Targetless runner-style paths (no fixed profit target)."""

import numpy as np
import pandas as pd

from src.execution.path import simulate_trade_path
from src.execution.policy import default_intraday_policy
from src.execution.types import ExitPlan, ExitReason, TradeIntent, TrailingRule, Side


def test_targetless_trailing_exit():
    n = 20
    o = np.linspace(100, 108, n)
    h = o + 1.0
    l = o - 0.5
    c = o + 0.3
    df = pd.DataFrame(
        {"open": o, "high": h, "low": l, "close": c, "minute_from_open": np.arange(n, dtype=np.int32)}
    )
    pol = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, eod_exit_minute=999)
    plan = ExitPlan(trailing=TrailingRule(distance_r=0.5))
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=Side.LONG,
        signal_idx=0,
        entry_idx=2,
        stop_price=95.0,
        max_hold_bars=None,
        management_mode="runner",
        target_mode="none",
        target_price=None,
        target_r=None,
        risk_per_share=1.0,
    )
    res = simulate_trade_path(df, intent, pol, plan)
    assert res.ok
    assert res.exit_reason is not None


def test_targetless_fixed_r_without_management_rejected():
    """``fixed_r`` without ``target_r`` fails validation."""
    df = pd.DataFrame(
        {
            "open": [100.0, 101.0],
            "high": [100.5, 101.5],
            "low": [99.5, 100.5],
            "close": [100.1, 101.1],
            "minute_from_open": np.array([0, 1], dtype=np.int32),
        }
    )
    pol = default_intraday_policy()
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=Side.LONG,
        signal_idx=0,
        entry_idx=0,
        stop_price=99.0,
        max_hold_bars=None,
        management_mode="fixed_r",
        target_mode="fixed_r",
        target_r=None,
        target_price=None,
        risk_per_share=1.0,
    )
    res = simulate_trade_path(df, intent, pol, ExitPlan())
    assert not res.ok


def test_targetless_exits_eod_when_eod_policy_counts_as_exit_path():
    minutes = np.array([380, 381, 382, 383, 388, 390], dtype=np.int32)
    o = [100.0] * 6
    df = pd.DataFrame(
        {
            "open": o,
            "high": [x + 0.1 for x in o],
            "low": [x - 0.1 for x in o],
            "close": [x + 0.05 for x in o],
            "minute_from_open": minutes,
        }
    )
    pol = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, eod_exit_minute=389)
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=Side.LONG,
        signal_idx=0,
        entry_idx=0,
        stop_price=90.0,
        max_hold_bars=None,
        management_mode="runner",
        target_mode="none",
        target_price=None,
        target_r=None,
        risk_per_share=1.0,
    )
    res = simulate_trade_path(df, intent, pol, ExitPlan())
    assert res.ok
    assert res.exit_reason == ExitReason.EOD
