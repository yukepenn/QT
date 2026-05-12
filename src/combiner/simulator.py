"""Combiner simulation: legacy Numba reference (lazy) + execution-backed canonical adapter.

Legacy accounting lives in ``archive/legacy_combiner/reference_simulator.py`` and is loaded
on demand. Mainline Layer 2 trades should use :func:`simulate_combiner_canonical`, which
delegates exits to :func:`src.execution.path.simulate_trade_path`.
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Rejection reason codes (signal evaluation)
REJ_NONE = 0
REJ_WRONG_TIME_WINDOW = 1
REJ_EXISTING_POSITION = 2
REJ_DAILY_LOSS_LIMIT = 3
REJ_MAX_TRADES_REACHED = 4
REJ_COOLDOWN_AFTER_LOSS = 5
REJ_NO_NEW_AFTER = 6
REJ_RISK_TOO_SMALL = 7
REJ_LOWER_PRIORITY_CONFLICT = 8
REJ_DISABLED_CANDIDATE = 9
REJ_LAST_BAR_NO_ENTRY = 10
REJ_SESSION_BOUNDARY_NO_ENTRY = 11
REJ_OPPOSITE_DIRECTION_CONFLICT = 12
REJ_INVALID_STOP_SIDE = 13
REJ_INVALID_TARGET_SIDE = 14
REJ_INVALID_TARGET_R = 15
REJ_INVALID_PRICE_NAN = 16

# Exit reason codes
EX_STOP = 1
EX_TARGET = 2
EX_MAX_HOLD = 3
EX_EOD = 4
EX_END_SESSION = 5
EX_END_DATA = 6

EXIT_NAMES = {
    EX_STOP: "stop",
    EX_TARGET: "target",
    EX_MAX_HOLD: "max_hold",
    EX_EOD: "eod",
    EX_END_SESSION: "end_of_session",
    EX_END_DATA: "end_of_data",
}

REJ_NAMES: dict[int, str] = {
    REJ_WRONG_TIME_WINDOW: "wrong_time_window",
    REJ_EXISTING_POSITION: "existing_position",
    REJ_DAILY_LOSS_LIMIT: "daily_loss_limit",
    REJ_MAX_TRADES_REACHED: "max_trades_reached",
    REJ_COOLDOWN_AFTER_LOSS: "cooldown_after_loss",
    REJ_NO_NEW_AFTER: "no_new_after",
    REJ_RISK_TOO_SMALL: "risk_too_small",
    REJ_LOWER_PRIORITY_CONFLICT: "lower_priority_conflict",
    REJ_DISABLED_CANDIDATE: "disabled_candidate",
    REJ_LAST_BAR_NO_ENTRY: "last_bar_no_entry",
    REJ_SESSION_BOUNDARY_NO_ENTRY: "session_boundary_no_entry",
    REJ_OPPOSITE_DIRECTION_CONFLICT: "opposite_direction_conflict",
    REJ_INVALID_STOP_SIDE: "invalid_stop_side",
    REJ_INVALID_TARGET_SIDE: "invalid_target_side",
    REJ_INVALID_TARGET_R: "invalid_target_r",
    REJ_INVALID_PRICE_NAN: "invalid_price_nan",
}

PRIORITY_METADATA_ONLY = 1
PRIORITY_SCORE_ADJUSTED = 2


@dataclass
class CombinerConfig:
    max_open_positions: int = 1
    max_trades_per_day: int = 2
    daily_max_loss_r: float = -2.0
    no_new_after_minute: int = 360
    eod_exit_minute: int = 389
    commission_per_trade: float = 0.0
    slippage_per_share: float = 0.01
    cooldown_after_loss_minutes: int = 0
    allow_same_bar_multiple_candidates: bool = False
    priority_policy: str = "metadata_priority"
    opposite_direction_skip_all: bool = False
    min_risk_per_share: float = 0.0


_LEGACY_PATH = Path(__file__).resolve().parents[2] / "archive" / "legacy_combiner" / "reference_simulator.py"
_legacy_spec = importlib.util.spec_from_file_location("combiner_reference_simulator", _LEGACY_PATH)
_legacy_mod: Any = None


def _legacy_reference() -> Any:
    global _legacy_mod
    if _legacy_mod is None:
        if not _LEGACY_PATH.is_file():
            raise FileNotFoundError(f"legacy combiner reference missing: {_LEGACY_PATH}")
        assert _legacy_spec and _legacy_spec.loader
        _legacy_mod = importlib.util.module_from_spec(_legacy_spec)
        sys.modules[str(_legacy_spec.name)] = _legacy_mod
        _legacy_spec.loader.exec_module(_legacy_mod)
    return _legacy_mod


def simulate_combiner_legacy_numba(**kwargs: Any) -> Any:
    """Archived Numba path (metrics-oriented)."""
    return _legacy_reference().simulate_combiner_numba(**kwargs)


def simulate_combiner_legacy_logs(**kwargs: Any) -> Any:
    """Archived detailed logs path."""
    return _legacy_reference().simulate_combiner_legacy_logs(**kwargs)


def simulate_combiner_numba(**kwargs: Any) -> Any:
    """Backward-compatible alias for :func:`simulate_combiner_legacy_numba`."""
    return simulate_combiner_legacy_numba(**kwargs)


def simulate_combiner_canonical(**kwargs: Any) -> Any:
    """Execution-backed Layer 2 loop (import lazy to avoid cycles)."""
    from src.combiner.adapter import simulate_combiner_canonical as _fn

    return _fn(**kwargs)


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
    "simulate_combiner_canonical",
    "simulate_combiner_legacy_logs",
    "simulate_combiner_legacy_numba",
    "simulate_combiner_numba",
]
