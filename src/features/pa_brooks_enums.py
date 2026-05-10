"""Coarse Brooks-style PA regime / Always-In enums (integer labels for DataFrames)."""

from __future__ import annotations

# Always-In side (coarse intraday bias proxy; not a trade signal).
PA_ALWAYS_IN_SHORT = -1
PA_ALWAYS_IN_NEUTRAL = 0
PA_ALWAYS_IN_LONG = 1

# Regime label (mutually exclusive-ish router state).
PA_REGIME_UNKNOWN = 0
PA_REGIME_STRONG_BULL_BREAKOUT = 1
PA_REGIME_STRONG_BEAR_BREAKOUT = -1
PA_REGIME_TIGHT_BULL_CHANNEL = 2
PA_REGIME_TIGHT_BEAR_CHANNEL = -2
PA_REGIME_BROAD_BULL_CHANNEL = 3
PA_REGIME_BROAD_BEAR_CHANNEL = -3
PA_REGIME_TRADING_RANGE = 4
PA_REGIME_LATE_TREND_CLIMAX = 5

# Trade-mode router (orthogonal to regime label; diagnostics only).
PA_TRADE_MODE_NEUTRAL = 0
PA_TRADE_MODE_TREND_LONG = 1
PA_TRADE_MODE_TREND_SHORT = -1
PA_TRADE_MODE_RANGE = 2
PA_TRADE_MODE_CLIMAX = 3
