import numpy as np
import pandas as pd

from src.execution.path import simulate_trade_path
from src.execution.policy import default_intraday_policy
from src.execution.types import ExitPlan, ExitReason, Side, TradeIntent


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


def test_stop_full_exit():
    df = pd.DataFrame(
        {
            "open": [100.0, 100.0, 100.0],
            "high": [100.0, 100.0, 100.0],
            "low": [100.0, 94.0, 94.0],
            "close": [100.0, 94.5, 94.0],
            "minute_from_open": np.arange(3, dtype=np.int32),
        }
    )
    pol = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, eod_exit_minute=999)
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=1,
        signal_idx=0,
        entry_idx=0,
        stop_price=95.0,
        target_price=200.0,
        target_r=10.0,
        risk_per_share=5.0,
        max_hold_bars=None,
        management_mode="fixed_r",
    )
    res = simulate_trade_path(df, intent, pol, None)
    assert res.ok
    assert res.exit_reason == ExitReason.STOP


def test_short_rejected_by_default():
    df = _bars(5)
    pol = default_intraday_policy(allow_short=False)
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=Side.SHORT,
        signal_idx=0,
        entry_idx=1,
        stop_price=110.0,
        target_price=90.0,
        target_r=2.0,
        risk_per_share=1.0,
        max_hold_bars=None,
        management_mode="fixed_r",
    )
    res = simulate_trade_path(df, intent, pol, None)
    assert not res.ok


def test_short_allowed_path():
    df = pd.DataFrame(
        {
            "open": [100.0, 100.0, 100.0, 100.0],
            "high": [100.0, 100.0, 92.0, 92.0],
            "low": [100.0, 99.0, 93.0, 91.0],
            "close": [100.0, 99.5, 93.5, 91.5],
            "minute_from_open": np.arange(4, dtype=np.int32),
        }
    )
    pol = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, allow_short=True, eod_exit_minute=999)
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=Side.SHORT,
        signal_idx=0,
        entry_idx=1,
        stop_price=102.0,
        target_price=90.0,
        target_r=2.0,
        risk_per_share=1.0,
        max_hold_bars=None,
        management_mode="fixed_r",
    )
    res = simulate_trade_path(df, intent, pol, None)
    assert res.ok


def test_invalid_risk_rejected():
    df = _bars(5)
    pol = default_intraday_policy()
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=1,
        signal_idx=0,
        entry_idx=1,
        stop_price=99.0,
        target_price=103.0,
        target_r=1.0,
        risk_per_share=0.0,
        max_hold_bars=None,
        management_mode="fixed_r",
    )
    res = simulate_trade_path(df, intent, pol, None)
    assert not res.ok


def test_eod_exit():
    df = pd.DataFrame(
        {
            "open": [100.0] * 5,
            "high": [100.5] * 5,
            "low": [99.5] * 5,
            "close": [100.1] * 5,
            "minute_from_open": np.array([380, 381, 382, 388, 390], dtype=np.int32),
        }
    )
    pol = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, eod_exit_minute=389)
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=1,
        signal_idx=0,
        entry_idx=0,
        stop_price=90.0,
        target_price=200.0,
        target_r=10.0,
        risk_per_share=1.0,
        max_hold_bars=None,
        management_mode="fixed_r",
    )
    res = simulate_trade_path(df, intent, pol, None)
    assert res.ok
    assert res.exit_reason == ExitReason.EOD


def test_no_followthrough_exit():
    df = pd.DataFrame(
        {
            "open": [100.0, 100.0, 100.0, 100.0],
            "high": [100.2, 100.1, 100.1, 100.1],
            "low": [99.9, 99.7, 99.6, 99.5],
            "close": [100.0, 99.8, 99.7, 99.6],
            "minute_from_open": np.arange(4, dtype=np.int32),
        }
    )
    pol = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, eod_exit_minute=999)
    plan = ExitPlan(no_followthrough_bars=2, no_followthrough_min_r=0.0)
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=1,
        signal_idx=0,
        entry_idx=0,
        stop_price=50.0,
        target_price=200.0,
        target_r=10.0,
        risk_per_share=1.0,
        max_hold_bars=10,
        management_mode="scalp",
    )
    res = simulate_trade_path(df, intent, pol, plan)
    assert res.ok
    assert res.exit_reason == ExitReason.NO_FOLLOWTHROUGH


def test_exit_plan_max_hold_cap():
    df = _bars(30)
    pol = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0, eod_exit_minute=999)
    plan = ExitPlan(max_hold_bars_cap=2)
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
        max_hold_bars=10,
        management_mode="fixed_r",
        qty=1.0,
    )
    res = simulate_trade_path(df, intent, pol, plan)
    assert res.ok
    assert res.exit_reason == ExitReason.MAX_HOLD
    assert res.bars_held == 2
