"""Single-strategy backtest column names and execution-related defaults."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BacktestConfig:
    session_col: str = "session_date"
    time_col: str = "ts_utc"
    ny_time_col: str = "ts_ny"
    minute_col: str = "minute_from_open"
    open_col: str = "open"
    high_col: str = "high"
    low_col: str = "low"
    close_col: str = "close"

    side_col: str = "sig_side"
    stop_col: str = "sig_stop"
    target_col: str = "sig_target"
    target_mode_col: str = "sig_target_mode"
    target_r_col: str = "sig_target_r"
    risk_col: str = "sig_risk_per_share"
    reason_col: str = "sig_reason"
    valid_col: str = "sig_valid"
    strategy_col: str = "sig_strategy"

    eod_exit_minute: int = 389
    quantity: float = 1.0
    commission_per_trade: float = 0.0
    slippage_per_share: float = 0.0
    recompute_target_from_entry: bool = True
    max_hold_minutes: int | None = None
    max_trades_per_session: int = 1
    cooldown_bars: int = 0


def _bt_cfg_from_dict(d: dict[str, Any] | None) -> BacktestConfig:
    if not d:
        return BacktestConfig()
    b = d.get("backtest") or {}
    mh = b.get("max_hold_minutes", None)
    max_hold: int | None
    if mh is None:
        max_hold = None
    else:
        max_hold = int(mh)
        if max_hold <= 0:
            raise ValueError("backtest.max_hold_minutes must be > 0 when set")
    max_tr = int(b.get("max_trades_per_session", 1))
    if max_tr <= 0:
        raise ValueError("backtest.max_trades_per_session must be > 0 when set")
    cd = int(b.get("cooldown_bars", 0))
    if cd < 0:
        raise ValueError("backtest.cooldown_bars must be >= 0")
    return BacktestConfig(
        eod_exit_minute=int(b.get("eod_exit_minute", 389)),
        quantity=float(b.get("quantity", 1.0)),
        commission_per_trade=float(b.get("commission_per_trade", 0.0)),
        slippage_per_share=float(b.get("slippage_per_share", 0.0)),
        recompute_target_from_entry=bool(b.get("recompute_target_from_entry", True)),
        max_hold_minutes=max_hold,
        max_trades_per_session=max_tr,
        cooldown_bars=cd,
    )
