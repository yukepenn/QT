"""Single-strategy backtest adapter.

Fill / exit / risk / target materialization / PnL live in ``src.execution``.
This module **only**:

- validates standard signal columns,
- maps each signal row to a raw :class:`TradeIntent` (no entry fill, no risk,
  no fixed-R target math),
- calls :func:`src.execution.path.simulate_trade_path`,
- flattens :class:`TradeResult` for metrics.

Standard signal columns (default :class:`BacktestConfig` maps these):

- ``sig_valid``, ``sig_side``, ``sig_stop``, ``sig_target`` (optional for
  ``fixed_r``), ``sig_target_mode``, ``sig_target_r``, ``sig_risk_per_share``
  (optional — execution derives risk if absent),
  ``sig_max_hold_bars`` (optional),
  ``sig_candidate_id``, ``sig_strategy``, ``sig_management_mode`` (optional).

Strategies may emit legacy names internally; map them before calling
``run_strategy_backtest`` if needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.metrics import summarize_trades
from src.execution.path import simulate_trade_path
from src.execution.policy import default_intraday_policy
from src.execution.types import ExecutionPolicy, ExitPlan, ExitReason, TradeIntent, TradeResult
from src.strategies.strategy.base import validate_standard_signal_columns


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
    min_risk_per_share: float = 0.0


def _max_trades_per_session_from_dict(backtest: dict[str, Any], risk: dict[str, Any]) -> int:
    """Resolve session trade cap with explicit ``backtest`` keys winning over risk aliases."""
    b = backtest
    r = risk
    if b.get("max_trades_per_session") is not None:
        v = int(b["max_trades_per_session"])
    elif b.get("max_trades_per_day") is not None:
        v = int(b["max_trades_per_day"])
    elif r.get("max_trades_per_session") is not None:
        v = int(r["max_trades_per_session"])
    elif r.get("max_trades_per_day") is not None:
        v = int(r["max_trades_per_day"])
    else:
        v = 1
    if v <= 0:
        raise ValueError("resolved max_trades_per_session must be > 0")
    return v


def _bt_cfg_from_dict(d: dict[str, Any] | None) -> BacktestConfig:
    if not d:
        return BacktestConfig()
    b = d.get("backtest") or {}
    r = d.get("risk") or {}
    mh = b.get("max_hold_minutes", None)
    max_hold: int | None
    if mh is None:
        max_hold = None
    else:
        max_hold = int(mh)
        if max_hold <= 0:
            raise ValueError("backtest.max_hold_minutes must be > 0 when set")
    max_tr = _max_trades_per_session_from_dict(b, r)
    cd = int(b.get("cooldown_bars", 0))
    if cd < 0:
        raise ValueError("backtest.cooldown_bars must be >= 0")
    if r.get("min_risk_per_share") is not None:
        mrs = float(r["min_risk_per_share"])
    elif b.get("min_risk_per_share") is not None:
        mrs = float(b["min_risk_per_share"])
    else:
        mrs = 0.0
    if mrs < 0 or mrs != mrs:
        raise ValueError("min_risk_per_share must be a finite number >= 0")
    return BacktestConfig(
        eod_exit_minute=int(b.get("eod_exit_minute", 389)),
        quantity=float(b.get("quantity", 1.0)),
        commission_per_trade=float(b.get("commission_per_trade", 0.0)),
        slippage_per_share=float(b.get("slippage_per_share", 0.0)),
        recompute_target_from_entry=bool(b.get("recompute_target_from_entry", True)),
        max_hold_minutes=max_hold,
        max_trades_per_session=max_tr,
        cooldown_bars=cd,
        min_risk_per_share=mrs,
    )


def _exit_reason_str(reason: ExitReason | None) -> str:
    if reason is None:
        return ""
    mapping = {
        ExitReason.STOP: "stop",
        ExitReason.TARGET: "target",
        ExitReason.SCALE_OUT: "scale_out",
        ExitReason.TRAILING: "trailing",
        ExitReason.MAX_HOLD: "max_hold",
        ExitReason.EOD: "eod",
        ExitReason.END_SESSION: "end_session",
        ExitReason.END_DATA: "end_of_data",
        ExitReason.NO_FOLLOWTHROUGH: "no_followthrough",
        ExitReason.REJECTED: "rejected",
    }
    return mapping.get(reason, str(reason.name).lower())


def signals_to_trade_intents(
    row: pd.Series,
    *,
    cfg: BacktestConfig,
    local_entry_idx: int,
    global_signal_idx: int,
    strategy_name: str,
) -> TradeIntent | None:
    """Map one valid signal row to a **raw** :class:`TradeIntent` (no fill/risk/target math)."""
    sd = int(row[cfg.side_col]) if not pd.isna(row[cfg.side_col]) else 0
    if sd == 0:
        return None
    stop_raw = row[cfg.stop_col]
    if pd.isna(stop_raw):
        return None
    stop_px = float(stop_raw)
    tm = str(row[cfg.target_mode_col] or "").strip().lower()
    if tm not in ("fixed_r", "fixed_price", "none"):
        return None

    tr_raw = row[cfg.target_r_col]
    tgt_raw = row[cfg.target_col]
    rs_raw = row.get(cfg.risk_col, float("nan"))

    target_r: float | None
    target_px: float | None
    risk_override: float | None

    if tm == "fixed_r":
        if pd.isna(tr_raw) or not (float(tr_raw) == float(tr_raw) and float(tr_raw) > 0):
            return None
        target_r = float(tr_raw)
        target_px = None
    elif tm == "fixed_price":
        if pd.isna(tgt_raw):
            return None
        target_r = None
        target_px = float(tgt_raw)
    else:
        target_r = None
        target_px = None

    if pd.isna(rs_raw):
        risk_override = None
    else:
        risk_override = float(rs_raw)

    cand = row.get("sig_candidate_id", strategy_name)
    if pd.isna(cand):
        cand = strategy_name
    mgm = row.get("sig_management_mode", "fixed_r")
    if pd.isna(mgm) or str(mgm).strip() == "":
        mgm = "fixed_r"

    max_hold = int(cfg.max_hold_minutes) if cfg.max_hold_minutes is not None else None

    return TradeIntent(
        candidate_id=str(cand),
        strategy=strategy_name,
        side=sd,
        signal_idx=int(global_signal_idx),
        entry_idx=int(local_entry_idx),
        stop_price=stop_px,
        max_hold_bars=max_hold,
        management_mode=str(mgm),
        target_mode=tm,  # type: ignore[arg-type]
        target_price=target_px,
        target_r=target_r,
        risk_per_share=risk_override,
        qty=float(cfg.quantity),
        metadata={},
    )


def trades_to_frame(trades: list[dict[str, Any]]) -> pd.DataFrame:
    if not trades:
        return pd.DataFrame()
    return pd.DataFrame(trades)


def trade_results_to_frame(results: list[TradeResult]) -> pd.DataFrame:
    """Flatten :class:`TradeResult` rows for inspection."""
    rows: list[dict[str, Any]] = []
    for r in results:
        rows.append(
            {
                "ok": r.ok,
                "reject_reason": r.reject_reason,
                "gross_r_multiple": r.gross_r_multiple,
                "net_r_multiple": r.net_r_multiple,
                "r_multiple": r.r_multiple,
                "risk_per_share": r.risk_per_share,
                "gross_pnl_per_share": r.gross_pnl_per_share,
                "net_pnl_per_share": r.net_pnl_per_share,
                "bars_held": r.bars_held,
                "exit_reason": _exit_reason_str(r.exit_reason),
                "legs": len(r.legs),
                "total_qty_frac": r.total_qty_frac,
                "has_partial": r.has_partial,
            }
        )
    return pd.DataFrame(rows)


def run_strategy_backtest(
    df: pd.DataFrame,
    *,
    config: BacktestConfig | None = None,
    policy: ExecutionPolicy | None = None,
    exit_plan: ExitPlan | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Reference backtest: scan valid signals in time order; optional multi-trade per session.

    Default matches prior behavior: ``max_trades_per_session=1``,
    ``cooldown_bars=0`` (first qualifying signal per session only).
    """
    cfg = config or BacktestConfig()
    pol = policy or default_intraday_policy(
        slippage_per_share=cfg.slippage_per_share,
        commission_per_trade=cfg.commission_per_trade,
        eod_exit_minute=cfg.eod_exit_minute,
        min_risk_per_share=cfg.min_risk_per_share,
    )
    validate_standard_signal_columns(df)
    work = df.sort_values(cfg.time_col).reset_index(drop=True)
    trades: list[dict[str, Any]] = []
    max_tr = max(1, int(cfg.max_trades_per_session))
    cd = max(0, int(cfg.cooldown_bars))

    for _, sub in work.groupby(cfg.session_col, sort=False):
        gix = sub.index.to_numpy()
        sess = sub.reset_index(drop=True)
        n = len(sess)
        trades_count = 0
        i = 0
        while i < max(0, n - 1) and trades_count < max_tr:
            row = sess.iloc[i]
            v = row[cfg.valid_col]
            valid = not pd.isna(v) and bool(v)
            if not valid:
                i += 1
                continue
            if i + 1 >= n:
                i += 1
                continue
            if sess.iloc[i + 1][cfg.session_col] != row[cfg.session_col]:
                i += 1
                continue
            ent_i = i + 1
            strat = str(row.get(cfg.strategy_col, "strategy") or "strategy")
            intent = signals_to_trade_intents(
                row,
                cfg=cfg,
                local_entry_idx=ent_i,
                global_signal_idx=int(gix[i]),
                strategy_name=strat,
            )
            if intent is None:
                i += 1
                continue
            bars_slice = work.iloc[gix].reset_index(drop=True)
            res = simulate_trade_path(bars_slice, intent, pol, exit_plan)
            if not res.ok:
                i += 1
                continue
            exit_idx_local = ent_i + int(res.bars_held) - 1
            trades.append(
                {
                    "session_date": row[cfg.session_col],
                    "r_multiple": res.r_multiple,
                    "gross_r_multiple": res.gross_r_multiple,
                    "net_r_multiple": res.net_r_multiple,
                    "net_pnl": res.net_pnl_per_share * cfg.quantity,
                    "exit_reason": _exit_reason_str(res.exit_reason),
                    "bars_held": res.bars_held,
                    "risk_per_share": res.risk_per_share,
                }
            )
            trades_count += 1
            i = exit_idx_local + cd + 1

    tdf = trades_to_frame(trades)
    summ = (
        summarize_trades(
            tdf,
            slippage_per_share=pol.slippage_per_share,
            commission_per_trade=pol.commission_per_trade,
            quantity=cfg.quantity,
        )
        if len(tdf)
        else summarize_trades(tdf)
    )
    return tdf, summ
