"""Coarse Layer 1 candidate scoring (not statistically optimal)."""

from __future__ import annotations

import argparse
from typing import Any

import pandas as pd


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return default
        return float(x)
    except (TypeError, ValueError):
        return default


def candidate_score(row: pd.Series) -> float:
    """Simple coarse score for ranking; do not treat as optimal."""
    pf = safe_float(row.get("profit_factor"), 0.0)
    tr = safe_float(row.get("total_r"), 0.0)
    mdd = safe_float(row.get("max_drawdown_r"), 0.0)
    abh = safe_float(row.get("avg_bars_held"), 0.0)
    eod = safe_float(row.get("eod_count"), 0.0)
    eod_data = safe_float(row.get("end_of_data_count"), 0.0)
    return (
        1.00 * pf
        + 0.015 * tr
        - 0.030 * abs(mdd)
        - 0.001 * abh
        - 0.050 * eod
        - 0.050 * eod_data
    )


def passes_filters(row: pd.Series, args: argparse.Namespace) -> bool:
    if int(row.get("trades", 0)) < int(getattr(args, "min_trades", 0) or 0):
        return False
    if getattr(args, "min_profit_factor", None) is not None:
        if safe_float(row.get("profit_factor")) < float(args.min_profit_factor):
            return False
    if getattr(args, "min_total_r", None) is not None:
        if safe_float(row.get("total_r")) < float(args.min_total_r):
            return False
    if getattr(args, "max_drawdown_r", None) is not None:
        if safe_float(row.get("max_drawdown_r")) < float(args.max_drawdown_r):
            return False
    if getattr(args, "max_avg_bars_held", None) is not None:
        if safe_float(row.get("avg_bars_held")) > float(args.max_avg_bars_held):
            return False
    if getattr(args, "max_eod_count", None) is not None:
        if int(safe_float(row.get("eod_count"), 0.0)) > int(args.max_eod_count):
            return False
    if getattr(args, "max_end_of_data_count", None) is not None:
        if int(safe_float(row.get("end_of_data_count"), 0.0)) > int(args.max_end_of_data_count):
            return False
    if getattr(args, "max_max_hold_count", None) is not None:
        if int(safe_float(row.get("max_hold_count"), 0.0)) > int(args.max_max_hold_count):
            return False
    return True
