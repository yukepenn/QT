#!/usr/bin/env python3
"""Synthetic-bar smoke for the canonical execution engine (no external data)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from src.execution.path import simulate_trade_path
from src.execution.policy import default_intraday_policy
from src.execution.types import ExitPlan, ScaleOutRule, TradeIntent, TrailingRule


def _minute(n: int) -> np.ndarray:
    return np.arange(n, dtype=np.int32)


def main() -> None:
    pol = default_intraday_policy(slippage_per_share=0.01, commission_per_trade=1.0, eod_exit_minute=999)

    # 1) Fixed target long
    n = 25
    o = np.linspace(100, 104, n)
    df = pd.DataFrame(
        {"open": o, "high": o + 0.6, "low": o - 0.4, "close": o + 0.2, "minute_from_open": _minute(n)}
    )
    r1 = simulate_trade_path(
        df,
        TradeIntent(
            candidate_id="smoke",
            strategy="smoke",
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
        ),
        pol,
        None,
    )
    print("fixed_target", r1.ok, r1.exit_reason, f"R={r1.r_multiple:.3f}", f"net={r1.net_pnl_per_share:.4f}")

    # 2) Max hold
    r2 = simulate_trade_path(
        df,
        TradeIntent(
            candidate_id="smoke",
            strategy="smoke",
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
        ),
        pol,
        None,
    )
    print("max_hold", r2.ok, r2.exit_reason, f"bars={r2.bars_held}")

    # 3) Partial + trail runner-style
    n = 30
    o = np.linspace(100, 112, n)
    h = o + 1.0
    l = o - 0.5
    c = o + 0.4
    df3 = pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "minute_from_open": _minute(n)})
    plan = ExitPlan(
        scale_outs=(ScaleOutRule(trigger_r=1.0, exit_fraction=0.5),),
        trailing=TrailingRule(distance_r=0.5),
    )
    r3 = simulate_trade_path(
        df3,
        TradeIntent(
            candidate_id="smoke",
            strategy="smoke",
            side=1,
            signal_idx=0,
            entry_idx=2,
            stop_price=95.0,
            target_price=300.0,
            target_r=20.0,
            risk_per_share=1.0,
            max_hold_bars=None,
            management_mode="runner",
            qty=1.0,
        ),
        pol,
        plan,
    )
    print("runner", r3.ok, r3.exit_reason, f"legs={len(r3.legs)}", f"R={r3.r_multiple:.3f}")


if __name__ == "__main__":
    main()
