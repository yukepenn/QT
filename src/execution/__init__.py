"""Canonical execution accounting (fills, exits, PnL)."""

from src.execution.path import simulate_trade_path
from src.execution.types import (
    AmbiguityPolicy,
    ExecutionPolicy,
    ExitPlan,
    ExitReason,
    FillLeg,
    ScaleOutRule,
    Side,
    TimeExitRule,
    TradeIntent,
    TradeResult,
    TrailingRule,
)

__all__ = [
    "AmbiguityPolicy",
    "ExecutionPolicy",
    "ExitPlan",
    "ExitReason",
    "FillLeg",
    "ScaleOutRule",
    "Side",
    "TimeExitRule",
    "TradeIntent",
    "TradeResult",
    "TrailingRule",
    "simulate_trade_path",
]
