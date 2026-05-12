"""Single-strategy backtest adapter.

Canonical fill / exit / risk / target materialization / PnL lives in
``src.execution``. This module **only**:

- validates standard signal columns,
- maps each signal row to a raw :class:`TradeIntent` (no entry fill, no risk,
  no fixed-R target math),
- calls :func:`src.execution.path.simulate_trade_path`,
- flattens :class:`TradeResult` for metrics.

``run_backtest`` delegates to ``legacy.engine_legacy`` — **legacy Numba
accounting**, pre-reset semantics, **not** canonical execution. Do not treat
its outputs as interchangeable with ``run_strategy_backtest``.

Canonical signal columns (default :class:`BacktestConfig` maps these):

- ``sig_valid``, ``sig_side``, ``sig_stop``, ``sig_target`` (optional for
  ``fixed_r``), ``sig_target_mode``, ``sig_target_r``, ``sig_risk_per_share``
  (optional — execution derives risk if absent),
  ``sig_max_hold_bars`` (optional),
  ``sig_candidate_id``, ``sig_strategy``, ``sig_management_mode`` (optional).

Strategies may emit legacy names internally; map them before calling
``run_strategy_backtest`` if needed.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.backtest.legacy.engine_legacy import BacktestConfig, run_backtest as run_backtest_legacy
from src.backtest.metrics import summarize_trades
from src.execution.path import simulate_trade_path
from src.execution.policy import default_intraday_policy
from src.execution.types import ExecutionPolicy, ExitPlan, ExitReason, TradeIntent, TradeResult
from src.strategies.strategy.base import validate_standard_signal_columns


def run_backtest(
    df: pd.DataFrame,
    *,
    config: BacktestConfig | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Legacy engine (Numba fast path, pre-reset semantics) — **not canonical**."""
    return run_backtest_legacy(df, config=config)


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
    """Canonical backtest: per session, first valid signal → execution path.

    MVP: **one trade per session** after first qualifying signal. No fill,
    risk, or target math here — only raw field extraction.
    """
    cfg = config or BacktestConfig()
    pol = policy or default_intraday_policy(
        slippage_per_share=cfg.slippage_per_share,
        commission_per_trade=cfg.commission_per_trade,
        eod_exit_minute=cfg.eod_exit_minute,
    )
    validate_standard_signal_columns(df)
    work = df.sort_values(cfg.time_col).reset_index(drop=True)
    trades: list[dict[str, Any]] = []

    for _, sub in work.groupby(cfg.session_col, sort=False):
        gix = sub.index.to_numpy()
        sess = sub.reset_index(drop=True)
        n = len(sess)
        for i in range(max(0, n - 1)):
            row = sess.iloc[i]
            v = row[cfg.valid_col]
            valid = not pd.isna(v) and bool(v)
            if not valid:
                continue
            if i + 1 >= n:
                continue
            if sess.iloc[i + 1][cfg.session_col] != row[cfg.session_col]:
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
                continue
            bars_slice = work.iloc[gix].reset_index(drop=True)
            res = simulate_trade_path(bars_slice, intent, pol, exit_plan)
            if not res.ok:
                continue
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
            break

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
