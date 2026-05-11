"""Single-strategy backtest adapter.

Canonical fill/exit/PnL lives in ``src.execution``. This module converts signal
rows to ``TradeIntent`` and calls ``execution.path.simulate_trade_path``.

``run_backtest`` delegates to ``legacy.engine_legacy`` for historical sweep
parity until fully ported.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.backtest.legacy.engine_legacy import BacktestConfig, run_backtest as run_backtest_legacy
from src.backtest.metrics import summarize_trades
from src.execution.path import simulate_trade_path
from src.execution.policy import default_intraday_policy
from src.execution.types import ExecutionPolicy, ExitPlan, ExitReason, TradeIntent
from src.strategies.strategy.base import validate_standard_signal_columns


def run_backtest(
    df: pd.DataFrame,
    *,
    config: BacktestConfig | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Legacy engine (pre-reset semantics) for full sweep parity."""
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
    }
    return mapping.get(reason, str(reason.name).lower())


def signals_to_trade_intents(
    row: pd.Series,
    *,
    cfg: BacktestConfig,
    local_entry_idx: int,
    global_signal_idx: int,
    entry_price: float,
    stop_px: float,
    tgt_px: float,
    risk: float,
    tr: float,
    tm: str,
    strategy_name: str,
) -> TradeIntent:
    sd = int(row[cfg.side_col])
    return TradeIntent(
        candidate_id=strategy_name,
        strategy=strategy_name,
        side=sd,
        signal_idx=int(global_signal_idx),
        entry_idx=int(local_entry_idx),
        stop_price=float(stop_px),
        target_price=float(tgt_px),
        target_r=float(tr) if tm == "fixed_r" else 0.0,
        risk_per_share=float(risk),
        max_hold_bars=int(cfg.max_hold_minutes) if cfg.max_hold_minutes is not None else None,
        management_mode="fixed_r",
        qty=float(cfg.quantity),
        target_mode="fixed_r" if tm == "fixed_r" else "fixed_price",
        metadata={},
    )


def trades_to_frame(trades: list[dict[str, Any]]) -> pd.DataFrame:
    if not trades:
        return pd.DataFrame()
    return pd.DataFrame(trades)


def run_strategy_backtest(
    df: pd.DataFrame,
    *,
    config: BacktestConfig | None = None,
    policy: ExecutionPolicy | None = None,
    exit_plan: ExitPlan | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Canonical backtest: per session, first valid signal → ``execution`` path."""
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
            sd = int(row[cfg.side_col]) if not pd.isna(row[cfg.side_col]) else 0
            if not valid or sd == 0:
                continue
            if i + 1 >= n:
                continue
            if sess.iloc[i + 1][cfg.session_col] != row[cfg.session_col]:
                continue
            stop_raw = row[cfg.stop_col]
            if pd.isna(stop_raw):
                continue
            stop_px = float(stop_raw)
            ent_i = i + 1
            ent_open = float(sess.iloc[ent_i][cfg.open_col])
            slip = float(pol.slippage_per_share)
            entry_price = ent_open + slip if sd == 1 else ent_open - slip
            if sd == 1:
                risk = entry_price - stop_px
            else:
                risk = stop_px - entry_price
            if risk <= 0:
                continue
            tm = str(row[cfg.target_mode_col] or "").strip().lower()
            tr_raw = row[cfg.target_r_col]
            tr = float(tr_raw) if not pd.isna(tr_raw) else float("nan")
            tgt_raw = row[cfg.target_col]
            if pd.isna(tgt_raw):
                continue
            if tm == "fixed_r":
                if not (tr == tr and tr > 0):
                    continue
                tgt_px = entry_price + tr * risk if sd == 1 else entry_price - tr * risk
            elif tm == "fixed_price":
                tgt_px = float(tgt_raw)
            else:
                continue
            strat = str(row.get(cfg.strategy_col, "strategy") or "strategy")
            local_entry = ent_i
            bars_slice = work.iloc[gix].reset_index(drop=True)
            intent = signals_to_trade_intents(
                row,
                cfg=cfg,
                local_entry_idx=local_entry,
                global_signal_idx=int(gix[i]),
                entry_price=entry_price,
                stop_px=stop_px,
                tgt_px=tgt_px,
                risk=risk,
                tr=tr,
                tm=tm,
                strategy_name=strat,
            )
            res = simulate_trade_path(bars_slice, intent, pol, exit_plan)
            if not res.ok:
                continue
            trades.append(
                {
                    "session_date": row[cfg.session_col],
                    "r_multiple": res.r_multiple,
                    "net_pnl": res.net_pnl_per_share * cfg.quantity,
                    "exit_reason": _exit_reason_str(res.exit_reason),
                    "bars_held": res.bars_held,
                    "risk_per_share": risk,
                }
            )
            break  # MVP: one trade per session

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
