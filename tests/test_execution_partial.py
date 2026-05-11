import numpy as np
import pandas as pd

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
