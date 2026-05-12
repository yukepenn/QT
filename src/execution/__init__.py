"""Canonical execution accounting (fills, exits, PnL)."""

from src.execution.materialize import (
    MaterializedTrade,
    materialize_entry_price,
    materialize_initial_risk,
    materialize_target_price,
    materialize_trade_levels,
)
from src.execution.path import simulate_trade_path
from src.execution.types import (
    AmbiguityPolicy,
    ExecutionPolicy,
    ExitPlan,
    ExitReason,
    FillLeg,
    ScaleFillPolicy,
    ScaleOutRule,
    Side,
    TargetMode,
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
    "MaterializedTrade",
    "ScaleFillPolicy",
    "ScaleOutRule",
    "Side",
    "TargetMode",
    "TimeExitRule",
    "TradeIntent",
    "TradeResult",
    "TrailingRule",
    "materialize_entry_price",
    "materialize_initial_risk",
    "materialize_target_price",
    "materialize_trade_levels",
    "simulate_trade_path",
]
