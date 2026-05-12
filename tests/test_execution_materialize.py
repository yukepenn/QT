"""Execution materialization (entry, risk, fixed-R target)."""

import numpy as np
import pandas as pd
import pytest

from src.execution.materialize import materialize_trade_levels
from src.execution.policy import default_intraday_policy
from src.execution.types import ExitPlan, ScaleOutRule, TradeIntent, Side, TrailingRule


def _df() -> pd.DataFrame:
    o = np.array([100.0, 101.0, 102.0])
    return pd.DataFrame(
        {
            "open": o,
            "high": o + 0.5,
            "low": o - 0.5,
            "close": o + 0.1,
            "minute_from_open": np.arange(3, dtype=np.int32),
        }
    )


def test_materialize_entry_and_risk():
    df = _df()
    pol = default_intraday_policy(slippage_per_share=0.25, commission_per_trade=0.0)
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=Side.LONG,
        signal_idx=0,
        entry_idx=1,
        stop_price=99.0,
        max_hold_bars=None,
        management_mode="fixed_r",
        target_mode="fixed_r",
        target_r=2.0,
        risk_per_share=None,
        target_price=None,
    )
    m = materialize_trade_levels(df, intent, pol, ExitPlan())
    assert m.ok
    assert m.entry_price == pytest.approx(101.25)
    assert m.risk_per_share == pytest.approx(m.entry_price - 99.0)
    assert m.target_price is not None
    assert m.target_price == pytest.approx(m.entry_price + 2.0 * m.risk_per_share)


def test_materialize_uses_explicit_risk_override():
    df = _df()
    pol = default_intraday_policy(slippage_per_share=0.0, commission_per_trade=0.0)
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=Side.LONG,
        signal_idx=0,
        entry_idx=1,
        stop_price=99.0,
        max_hold_bars=None,
        management_mode="fixed_r",
        target_mode="fixed_r",
        target_r=3.0,
        risk_per_share=5.0,
        target_price=None,
    )
    m = materialize_trade_levels(df, intent, pol, ExitPlan())
    assert m.ok
    assert m.risk_per_share == 5.0
    assert m.target_price == pytest.approx(m.entry_price + 15.0)


def test_targetless_rejects_without_path():
    df = _df()
    pol = default_intraday_policy(eod_exit_minute=999)
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=Side.LONG,
        signal_idx=0,
        entry_idx=1,
        stop_price=99.0,
        max_hold_bars=None,
        management_mode="runner",
        target_mode="none",
        target_price=None,
        target_r=None,
        risk_per_share=None,
    )
    m = materialize_trade_levels(df, intent, pol, ExitPlan())
    assert not m.ok
    assert "targetless" in m.reject_reason


def test_targetless_rejects_scale_out_without_trailing():
    df = _df()
    pol = default_intraday_policy(eod_exit_minute=999)
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=Side.LONG,
        signal_idx=0,
        entry_idx=1,
        stop_price=50.0,
        max_hold_bars=None,
        management_mode="runner",
        target_mode="none",
        target_price=None,
        target_r=None,
        risk_per_share=1.0,
    )
    plan = ExitPlan(scale_outs=(ScaleOutRule(trigger_r=0.5, exit_fraction=0.5),))
    m = materialize_trade_levels(df, intent, pol, plan)
    assert not m.ok


def test_targetless_ok_with_trailing_plan():
    df = _df()
    pol = default_intraday_policy(eod_exit_minute=999)
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=Side.LONG,
        signal_idx=0,
        entry_idx=1,
        stop_price=50.0,
        max_hold_bars=10,
        management_mode="runner",
        target_mode="none",
        target_price=None,
        target_r=None,
        risk_per_share=1.0,
    )
    plan = ExitPlan(trailing=TrailingRule(distance_r=0.5))
    m = materialize_trade_levels(df, intent, pol, plan)
    assert m.ok
    assert m.target_price is None


def test_targetless_ok_with_scale_out_and_trailing():
    df = _df()
    pol = default_intraday_policy(eod_exit_minute=999)
    intent = TradeIntent(
        candidate_id="c",
        strategy="s",
        side=Side.LONG,
        signal_idx=0,
        entry_idx=1,
        stop_price=50.0,
        max_hold_bars=None,
        management_mode="runner",
        target_mode="none",
        target_price=None,
        target_r=None,
        risk_per_share=1.0,
    )
    plan = ExitPlan(
        scale_outs=(ScaleOutRule(trigger_r=0.5, exit_fraction=0.5),),
        trailing=TrailingRule(distance_r=0.5),
    )
    m = materialize_trade_levels(df, intent, pol, plan)
    assert m.ok
    assert m.target_price is None
