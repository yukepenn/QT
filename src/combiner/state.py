"""Combiner selection state (minimal scaffold for execution-backed path)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CombinerState:
    open_positions: int = 0
    trades_today: int = 0
    day_realized_r: float = 0.0
    cooldown_until_bar: int = -1
    meta: dict = field(default_factory=dict)
