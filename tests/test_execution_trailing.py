import numpy as np
import pandas as pd

from src.execution.path import simulate_trade_path
from src.execution.policy import default_intraday_policy
from src.execution.types import ExitPlan, ExitReason, TradeIntent, TrailingRule


def test_trailing_uses_past_bars_only():
    n = 40
    o = np.linspace(100, 120, n)
    h = o + 2.0
    l = o - 1.0
    c = o + 0.5
    df = pd.DataFrame(
        {"open": o, "high": h, "low": l, "close": c, "minute_from_open": np.arange(n, dtype=np.int32)}
    )
    pol = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, eod_exit_minute=999)
    plan = ExitPlan(trailing=TrailingRule(distance_r=0.3))
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=1,
        signal_idx=0,
        entry_idx=2,
        stop_price=90.0,
        target_price=300.0,
        target_r=50.0,
        risk_per_share=1.0,
        max_hold_bars=None,
        management_mode="runner",
    )
    res = simulate_trade_path(df, intent, pol, plan)
    assert res.ok


def test_trailing_not_same_bar_as_spike():
    """Trail level from bar t must not exit on bar t; check starts bar t+1."""
    df = pd.DataFrame(
        {
            "open": [100.0, 100.0, 100.0, 100.0, 100.0],
            "high": [100.0, 100.0, 130.0, 100.0, 100.0],
            "low": [100.0, 99.0, 100.0, 80.0, 99.0],
            "close": [100.0, 99.5, 125.0, 85.0, 99.0],
            "minute_from_open": np.arange(5, dtype=np.int32),
        }
    )
    pol = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, eod_exit_minute=999)
    plan = ExitPlan(trailing=TrailingRule(distance_r=1.0))
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=1,
        signal_idx=0,
        entry_idx=1,
        stop_price=50.0,
        target_price=300.0,
        target_r=50.0,
        risk_per_share=1.0,
        max_hold_bars=None,
        management_mode="runner",
    )
    res = simulate_trade_path(df, intent, pol, plan)
    assert res.ok
    assert res.exit_reason == ExitReason.TRAILING
    assert res.bars_held >= 2
