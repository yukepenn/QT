"""Trade and equity metrics."""

from __future__ import annotations

import pandas as pd


def profit_factor(pnls: pd.Series) -> float:
    s = pnls.astype(float)
    wins = s[s > 0].sum()
    losses = s[s < 0].sum()
    if losses == 0:
        return float("inf") if wins > 0 else 0.0
    return float(wins / abs(losses))


def max_drawdown(series: pd.Series) -> float:
    if len(series) == 0:
        return 0.0
    x = series.astype(float).values
    peak = x[0]
    dd = 0.0
    for v in x:
        peak = max(peak, v)
        dd = min(dd, v - peak)
    return float(dd)


def summarize_trades(trades_df: pd.DataFrame) -> dict:
    empty = {
        "trades": 0,
        "win_rate": 0.0,
        "total_net_pnl": 0.0,
        "avg_net_pnl": 0.0,
        "total_r": 0.0,
        "avg_r": 0.0,
        "profit_factor": 0.0,
        "max_drawdown_pnl": 0.0,
        "max_drawdown_r": 0.0,
        "avg_bars_held": 0.0,
        "stop_count": 0,
        "target_count": 0,
        "eod_count": 0,
        "end_of_data_count": 0,
        "max_hold_count": 0,
    }
    if trades_df is None or len(trades_df) == 0:
        return empty

    net = trades_df["net_pnl"].astype(float)
    r = trades_df["r_multiple"].astype(float)
    wins = int((net > 0).sum())
    n = int(len(trades_df))
    cum_pnl = net.cumsum()
    cum_r = r.cumsum()

    er = trades_df["exit_reason"].astype(str).str.lower()
    return {
        "trades": n,
        "win_rate": wins / n if n else 0.0,
        "total_net_pnl": float(net.sum()),
        "avg_net_pnl": float(net.mean()),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "profit_factor": profit_factor(net),
        "max_drawdown_pnl": max_drawdown(cum_pnl),
        "max_drawdown_r": max_drawdown(cum_r),
        "avg_bars_held": float(trades_df["bars_held"].astype(float).mean()),
        "stop_count": int((er == "stop").sum()),
        "target_count": int((er == "target").sum()),
        "eod_count": int((er == "eod").sum()),
        "end_of_data_count": int((er == "end_of_data").sum()),
        "max_hold_count": int((er == "max_hold").sum()),
    }
