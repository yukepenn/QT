"""Equity curve from trade pnls."""

from __future__ import annotations

import pandas as pd


def equity_curve_from_net_pnl(trades: pd.DataFrame) -> pd.Series:
    if trades is None or len(trades) == 0 or "net_pnl" not in trades.columns:
        return pd.Series(dtype=float)
    return trades["net_pnl"].astype(float).cumsum()
