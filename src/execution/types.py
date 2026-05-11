from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Literal


class Side(IntEnum):
    LONG = 1
    SHORT = -1


class ExitReason(IntEnum):
    STOP = 1
    TARGET = 2
    SCALE_OUT = 3
    TRAILING = 4
    MAX_HOLD = 5
    EOD = 6
    END_SESSION = 7
    END_DATA = 8
    NO_FOLLOWTHROUGH = 9


class AmbiguityPolicy(IntEnum):
    STOP_FIRST = 0
    TARGET_FIRST = 1


TargetMode = Literal["fixed_r", "fixed_price"]
EntryTiming = Literal["next_open"]


@dataclass(frozen=True)
class ExecutionPolicy:
    semantics_version: str = "1.0"
    slippage_per_share: float = 0.0
    commission_per_trade: float = 0.0
    same_bar_policy: AmbiguityPolicy = AmbiguityPolicy.STOP_FIRST
    entry_timing: EntryTiming = "next_open"
    max_hold_policy: Literal["after_stop_target"] = "after_stop_target"
    eod_exit_minute: int = 389
    allow_partial_exits: bool = True
    allow_trailing: bool = True
    allow_short: bool = False


@dataclass
class ScaleOutRule:
    """Scale out when unrealized R reaches trigger_r; exit fraction of remaining qty."""

    trigger_r: float
    exit_fraction: float  # of *remaining* position


@dataclass
class TrailingRule:
    """Trail stop distance measured in R from best price since entry."""

    distance_r: float


@dataclass
class TimeExitRule:
    """Exit at session close / minute threshold."""

    eod_exit_minute: int | None = None


@dataclass
class ExitPlan:
    """Management-produced plan consumed by execution.path."""

    scale_outs: tuple[ScaleOutRule, ...] = ()
    trailing: TrailingRule | None = None
    no_followthrough_bars: int | None = None
    no_followthrough_min_r: float | None = None  # exit if unrealized R below this after N bars
    time_rule: TimeExitRule | None = None


@dataclass
class TradeIntent:
    candidate_id: str
    strategy: str
    side: int
    signal_idx: int
    entry_idx: int
    stop_price: float
    target_price: float
    target_r: float
    risk_per_share: float
    max_hold_bars: int | None
    management_mode: str
    qty: float = 1.0
    target_mode: TargetMode = "fixed_r"
    metadata: dict[str, Any] = field(default_factory=dict)
    family: str = "unknown"
    setup_type: str = "unknown"


@dataclass
class FillLeg:
    qty_frac: float
    entry_price: float
    exit_price: float
    r_multiple: float
    reason: ExitReason


@dataclass
class TradeResult:
    ok: bool
    reject_reason: str
    legs: tuple[FillLeg, ...] = ()
    gross_pnl_per_share: float = 0.0
    net_pnl_per_share: float = 0.0
    r_multiple: float = 0.0
    mfe_R: float = 0.0
    mae_R: float = 0.0
    bars_held: int = 0
    exit_reason: ExitReason | None = None
    entry_price: float = float("nan")
    exit_price: float = float("nan")
