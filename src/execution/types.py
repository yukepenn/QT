"""Core dataclasses and enums for canonical execution accounting.

All backtest/combiner adapters should build :class:`TradeIntent` with **raw**
signal fields (stop, optional risk, ``target_mode``, ``target_r`` and/or
``target_price``) and pass them to :func:`src.execution.path.simulate_trade_path`.
Entry fill, initial risk, and fixed-R target **materialization** happen inside
execution (see :mod:`src.execution.materialize`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Literal


class Side(IntEnum):
    """Position side. Long is ``+1``, short is ``-1``."""

    LONG = 1
    SHORT = -1


class ExitReason(IntEnum):
    """Why a leg (or full position) exited."""

    STOP = 1
    TARGET = 2
    SCALE_OUT = 3
    TRAILING = 4
    MAX_HOLD = 5
    EOD = 6
    END_SESSION = 7
    END_DATA = 8
    NO_FOLLOWTHROUGH = 9
    REJECTED = 10


class AmbiguityPolicy(IntEnum):
    """When stop and target both trade in the same bar."""

    STOP_FIRST = 0
    TARGET_FIRST = 1


TargetMode = Literal["fixed_r", "fixed_price", "none"]
EntryTiming = Literal["next_open"]
ScaleFillPolicy = Literal["close", "trigger_price"]


@dataclass(frozen=True)
class ExecutionPolicy:
    """Global knobs for the reference simulator."""

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
    scale_fill_policy: ScaleFillPolicy = "close"


@dataclass
class ScaleOutRule:
    """Scale out when unrealized R (touch-based) reaches ``trigger_r``.

    ``exit_fraction`` applies to *remaining* quantity after prior scale-outs.
    """

    trigger_r: float
    exit_fraction: float


@dataclass
class TrailingRule:
    """Chandelier-style trail: stop sits ``distance_r`` (in initial R units)
    behind the best favorable price since entry.
    """

    distance_r: float


@dataclass
class TimeExitRule:
    """Optional explicit time-exit rule (reserved for session templates)."""

    eod_exit_minute: int | None = None


@dataclass
class ExitPlan:
    """Management layer output consumed by :mod:`src.execution.path`.

    ``max_hold_bars_cap`` tightens ``TradeIntent.max_hold_bars`` when both are
    set (minimum of the two). When only the cap is set, it becomes the
    effective max-hold.
    """

    scale_outs: tuple[ScaleOutRule, ...] = ()
    trailing: TrailingRule | None = None
    no_followthrough_bars: int | None = None
    no_followthrough_min_r: float | None = None
    time_rule: TimeExitRule | None = None
    max_hold_bars_cap: int | None = None


@dataclass
class TradeIntent:
    """Raw signal-aligned trade request (pre-materialization).

    ``risk_per_share``: optional; if ``None``, execution derives it from entry
    fill and ``stop_price``.

    ``target_mode``:

    - ``fixed_r``: ``target_r`` required (``> 0``); ``target_price`` ignored for
      materialization (recomputed at entry).
    - ``fixed_price``: ``target_price`` required.
    - ``none``: no fixed profit target; requires a viable management/time exit
      path (validated in :mod:`src.execution.materialize`).
    """

    candidate_id: str
    strategy: str
    side: int
    signal_idx: int
    entry_idx: int
    stop_price: float
    max_hold_bars: int | None
    management_mode: str
    target_mode: TargetMode = "fixed_r"
    target_price: float | None = None
    target_r: float | None = None
    risk_per_share: float | None = None
    qty: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    family: str = "unknown"
    setup_type: str = "unknown"


@dataclass
class FillLeg:
    """One closed partial or full exit."""

    qty_frac: float
    entry_price: float
    exit_price: float
    r_multiple: float
    reason: ExitReason


@dataclass
class TradeResult:
    """Outcome of :func:`simulate_trade_path`.

    ``gross_r_multiple`` is price-path R (Σ ``qty_frac × leg_r``) before
    commission. ``net_r_multiple`` is ``net_pnl_per_share / risk_per_share``.
    ``r_multiple`` aliases ``net_r_multiple`` for headline reporting.
    ``risk_per_share`` is the **initial** risk denominator used for R.
    """

    ok: bool
    reject_reason: str
    legs: tuple[FillLeg, ...] = ()
    gross_pnl_per_share: float = 0.0
    net_pnl_per_share: float = 0.0
    gross_r_multiple: float = 0.0
    net_r_multiple: float = 0.0
    r_multiple: float = 0.0
    risk_per_share: float = float("nan")
    mfe_R: float = 0.0
    mae_R: float = 0.0
    bars_held: int = 0
    exit_reason: ExitReason | None = None
    entry_price: float = float("nan")
    exit_price: float = float("nan")

    @property
    def is_win(self) -> bool:
        return self.ok and self.net_pnl_per_share > 0.0

    @property
    def total_qty_frac(self) -> float:
        return float(sum(leg.qty_frac for leg in self.legs))

    @property
    def has_partial(self) -> bool:
        return len(self.legs) > 1
