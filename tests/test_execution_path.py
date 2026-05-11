import numpy as np
import pandas as pd

from src.execution.path import simulate_trade_path
from src.execution.policy import default_intraday_policy
from src.execution.types import ExitPlan, TradeIntent


def _bars(n: int = 10) -> pd.DataFrame:
    o = np.linspace(100, 100 + n - 1, n)
    h = o + 0.5
    l = o - 0.5
    c = o + 0.1
    return pd.DataFrame(
        {
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "minute_from_open": np.arange(n, dtype=np.int32),
        }
    )


def test_fixed_target_exit():
    df = _bars(20)
    pol = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0)
    intent = TradeIntent(
        candidate_id="c1",
        strategy="s",
        side=1,
        signal_idx=0,
        entry_idx=1,
        stop_price=99.0,
        target_price=103.0,
        target_r=3.0,
        risk_per_share=1.0,
        max_hold_bars=None,
        management_mode="fixed_r",
        qty=1.0,
    )
    res = simulate_trade_path(df, intent, pol, None)
    assert res.ok
    assert res.exit_reason is not None


def test_max_hold():
    df = _bars(30)
    pol = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, eod_exit_minute=999)
    intent = TradeIntent(
        candidate_id="c1",
        strategy="s",
        side=1,
        signal_idx=0,
        entry_idx=1,
        stop_price=90.0,
        target_price=200.0,
        target_r=10.0,
        risk_per_share=1.0,
        max_hold_bars=3,
        management_mode="fixed_r",
        qty=1.0,
    )
    res = simulate_trade_path(df, intent, pol, None)
    assert res.ok
    assert res.exit_reason.name == "MAX_HOLD"


def test_invalid_side():
    df = _bars(5)
    pol = default_intraday_policy()
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=0,
        signal_idx=0,
        entry_idx=1,
        stop_price=99.0,
        target_price=103.0,
        target_r=1.0,
        risk_per_share=1.0,
        max_hold_bars=None,
        management_mode="fixed_r",
    )
    res = simulate_trade_path(df, intent, pol, None)
    assert not res.ok


def test_mfe_positive_long():
    df = _bars(15)
    pol = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, eod_exit_minute=999)
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
        max_hold_bars=5,
        management_mode="fixed_r",
    )
    res = simulate_trade_path(df, intent, pol, None)
    assert res.ok
    assert res.mfe_R >= 0.0
