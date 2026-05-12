"""Combiner simulation (**legacy Numba compatibility only**).

The symbols below are re-exported **explicitly** from
``src.combiner.legacy.simulator_legacy`` for ``run.py`` / ``sweep.py`` parity
during the architecture reset.

**Do not** extend this module with new accounting logic. Canonical Layer 2
simulation will build :class:`src.execution.types.TradeIntent` rows and call
``src.execution.path.simulate_trade_path``; see ``docs/CANONICAL_COMBINER_DESIGN.md``.

There is **no** wildcard re-export; add new names to ``__all__`` only when they
exist on the legacy module and are required for compatibility.
"""

from __future__ import annotations

from src.combiner.legacy.simulator_legacy import (
    EX_EOD,
    EX_END_DATA,
    EX_END_SESSION,
    EX_MAX_HOLD,
    EX_STOP,
    EX_TARGET,
    EXIT_NAMES,
    PRIORITY_METADATA_ONLY,
    PRIORITY_SCORE_ADJUSTED,
    REJ_NAMES,
    REJ_NONE,
    REJ_COOLDOWN_AFTER_LOSS,
    REJ_DAILY_LOSS_LIMIT,
    REJ_DISABLED_CANDIDATE,
    REJ_EXISTING_POSITION,
    REJ_INVALID_PRICE_NAN,
    REJ_INVALID_STOP_SIDE,
    REJ_INVALID_TARGET_R,
    REJ_INVALID_TARGET_SIDE,
    REJ_LAST_BAR_NO_ENTRY,
    REJ_LOWER_PRIORITY_CONFLICT,
    REJ_MAX_TRADES_REACHED,
    REJ_NO_NEW_AFTER,
    REJ_OPPOSITE_DIRECTION_CONFLICT,
    REJ_RISK_TOO_SMALL,
    REJ_SESSION_BOUNDARY_NO_ENTRY,
    REJ_WRONG_TIME_WINDOW,
    CombinerConfig,
    simulate_combiner_legacy_logs,
    simulate_combiner_numba,
)

__all__ = [
    "CombinerConfig",
    "EXIT_NAMES",
    "EX_STOP",
    "EX_TARGET",
    "EX_MAX_HOLD",
    "EX_EOD",
    "EX_END_SESSION",
    "EX_END_DATA",
    "PRIORITY_METADATA_ONLY",
    "PRIORITY_SCORE_ADJUSTED",
    "REJ_NAMES",
    "REJ_NONE",
    "REJ_COOLDOWN_AFTER_LOSS",
    "REJ_DAILY_LOSS_LIMIT",
    "REJ_DISABLED_CANDIDATE",
    "REJ_EXISTING_POSITION",
    "REJ_INVALID_PRICE_NAN",
    "REJ_INVALID_STOP_SIDE",
    "REJ_INVALID_TARGET_R",
    "REJ_INVALID_TARGET_SIDE",
    "REJ_LAST_BAR_NO_ENTRY",
    "REJ_LOWER_PRIORITY_CONFLICT",
    "REJ_MAX_TRADES_REACHED",
    "REJ_NO_NEW_AFTER",
    "REJ_OPPOSITE_DIRECTION_CONFLICT",
    "REJ_RISK_TOO_SMALL",
    "REJ_SESSION_BOUNDARY_NO_ENTRY",
    "REJ_WRONG_TIME_WINDOW",
    "simulate_combiner_legacy_logs",
    "simulate_combiner_numba",
]
