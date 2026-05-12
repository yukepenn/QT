"""Mutable combiner constraints (counts, cooldown, daily loss).

These helpers are **framework** state; they do not simulate prices. A future
execution-backed combiner will call them before building :class:`TradeIntent`.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CombinerState:
    open_positions: int = 0
    trades_today: int = 0
    day_realized_r: float = 0.0
    cooldown_until_bar: int = -1
    current_session_day: object | None = None
    meta: dict = field(default_factory=dict)

    def reset_day(self, session_day: object) -> None:
        """Call when the session calendar day changes."""
        self.current_session_day = session_day
        self.trades_today = 0
        self.day_realized_r = 0.0
        self.cooldown_until_bar = -1
        self.open_positions = 0

    def ensure_day(self, session_day: object) -> None:
        if self.current_session_day != session_day:
            self.reset_day(session_day)

    def can_enter_bar(self, bar_index: int) -> bool:
        return bar_index >= int(self.cooldown_until_bar)

    def register_trade_open(self) -> None:
        self.open_positions += 1
        self.trades_today += 1

    def register_trade_close(self, r_multiple: float) -> None:
        self.open_positions = max(0, self.open_positions - 1)
        self.day_realized_r += float(r_multiple)

    def start_cooldown(self, *, from_bar: int, cooldown_bars: int) -> None:
        self.cooldown_until_bar = int(from_bar) + int(cooldown_bars)

    def max_trades_per_day_exceeded(self, limit: int) -> bool:
        return self.trades_today >= int(limit)

    def daily_loss_exceeded(self, max_loss_r: float) -> bool:
        """``max_loss_r`` is a positive budget; exceeded when realized <= -budget."""
        return self.day_realized_r <= -float(max_loss_r)
