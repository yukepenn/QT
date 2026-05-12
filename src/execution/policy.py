"""Default :class:`ExecutionPolicy` factories for intraday research."""

from __future__ import annotations

from src.execution.types import AmbiguityPolicy, ExecutionPolicy


def default_intraday_policy(
    *,
    slippage_per_share: float = 0.01,
    commission_per_trade: float = 0.0,
    eod_exit_minute: int = 389,
    allow_short: bool = False,
) -> ExecutionPolicy:
    return ExecutionPolicy(
        slippage_per_share=slippage_per_share,
        commission_per_trade=commission_per_trade,
        same_bar_policy=AmbiguityPolicy.STOP_FIRST,
        eod_exit_minute=eod_exit_minute,
        allow_short=allow_short,
    )
