"""Generic behavior hashing and behavior-level dedupe for Layer 2 (no strategy-specific logic)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pandas as pd


def _safe_str(x: Any) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    return str(x)


def _safe_float(x: Any) -> float:
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return float("nan")
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def _safe_int(x: Any) -> int:
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return -999999999
        return int(x)
    except (TypeError, ValueError):
        return -999999999


def canonical_trade_columns(trades_df: pd.DataFrame) -> tuple[list[str], str]:
    """Columns used for behavior hash (priority: id, entry, exit, side, exit_reason)."""
    cols: list[str] = []
    if "candidate_id" in trades_df.columns:
        cols.append("candidate_id")
        id_quality = "id"
    elif "candidate_idx" in trades_df.columns:
        cols.append("candidate_idx")
        id_quality = "id"
    elif "strategy" in trades_df.columns:
        cols.append("strategy")
        id_quality = "strategy_only"
    else:
        cols.append("_fallback_idx")
        id_quality = "none"

    if "entry_idx" in trades_df.columns:
        cols.append("entry_idx")
    elif "entry_ts_utc" in trades_df.columns:
        cols.append("entry_ts_utc")
    else:
        cols.append("_missing_entry")

    if "exit_idx" in trades_df.columns:
        cols.append("exit_idx")
    elif "exit_ts_utc" in trades_df.columns:
        cols.append("exit_ts_utc")
    else:
        cols.append("_missing_exit")

    cols.append("side" if "side" in trades_df.columns else "_missing_side")
    cols.append("exit_reason" if "exit_reason" in trades_df.columns else "_missing_reason")

    has_entry = "_missing_entry" not in cols
    has_exit = "_missing_exit" not in cols
    if id_quality == "id" and has_entry and has_exit:
        quality = "strong"
    elif id_quality == "strategy_only":
        quality = "weak"
    elif id_quality == "none" or not has_entry or not has_exit:
        quality = "weak"
    else:
        quality = "medium"

    return cols, quality


def behavior_hash_from_trades(trades_df: pd.DataFrame) -> str:
    if trades_df is None or len(trades_df) == 0:
        payload = json.dumps([], sort_keys=False, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    cols, _ = canonical_trade_columns(trades_df)
    rows: list[tuple[Any, ...]] = []
    for i in range(len(trades_df)):
        row = trades_df.iloc[i]
        tup: list[Any] = []
        for c in cols:
            if c == "_fallback_idx":
                tup.append(i)
            elif c in ("entry_idx", "exit_idx", "candidate_idx", "side"):
                tup.append(_safe_int(row.get(c)))
            else:
                tup.append(_safe_str(row.get(c)))
        rows.append(tuple(tup))
    rows.sort()
    payload = json.dumps(rows, sort_keys=False, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def behavior_summary_from_trades(trades_df: pd.DataFrame) -> dict[str, Any]:
    h = behavior_hash_from_trades(trades_df)
    if trades_df is None or len(trades_df) == 0:
        return {
            "behavior_hash": h,
            "behavior_hash_quality": "empty",
            "behavior_trade_count": 0,
            "first_entry_ts": None,
            "last_exit_ts": None,
            "unique_candidates": 0,
            "candidate_ids_json": None,
            "strategies_json": None,
            "exit_reasons_json": None,
            "sides_json": None,
            "entry_day_count": 0,
            "avg_trades_per_active_day": 0.0,
        }

    _, quality = canonical_trade_columns(trades_df)
    n = len(trades_df)
    fe = le = None
    if "entry_ts_utc" in trades_df.columns:
        tss = pd.to_datetime(trades_df["entry_ts_utc"], utc=True, errors="coerce").dropna()
        if len(tss):
            fe = str(tss.min())
    if "exit_ts_utc" in trades_df.columns:
        tss = pd.to_datetime(trades_df["exit_ts_utc"], utc=True, errors="coerce").dropna()
        if len(tss):
            le = str(tss.max())

    cand_json = None
    if "candidate_id" in trades_df.columns:
        uq = trades_df["candidate_id"].dropna().unique().tolist()
        cand_json = json.dumps(sorted(str(x) for x in uq), sort_keys=True)

    strat_json = None
    if "strategy" in trades_df.columns:
        uq = trades_df["strategy"].dropna().unique().tolist()
        strat_json = json.dumps(sorted(str(x) for x in uq), sort_keys=True)

    er_json = None
    if "exit_reason" in trades_df.columns:
        vc = trades_df["exit_reason"].astype(str).value_counts()
        er_json = json.dumps({str(k): int(v) for k, v in vc.items()}, sort_keys=True)

    sides_json = None
    if "side" in trades_df.columns:
        vc = trades_df["side"].value_counts()
        sides_json = json.dumps({str(int(k)): int(v) for k, v in vc.items() if pd.notna(k)}, sort_keys=True)

    day_col = None
    work = trades_df
    if "session_date" in work.columns:
        day_col = work["session_date"]
    elif "entry_ts_utc" in work.columns:
        day_col = pd.to_datetime(work["entry_ts_utc"], utc=True, errors="coerce").dt.normalize()
    elif "exit_ts_utc" in work.columns:
        day_col = pd.to_datetime(work["exit_ts_utc"], utc=True, errors="coerce").dt.normalize()

    active_days = int(day_col.nunique()) if day_col is not None else 0
    avg_td = float(n / active_days) if active_days else float(n)

    uc = int(trades_df["candidate_id"].nunique()) if "candidate_id" in trades_df.columns else 0

    return {
        "behavior_hash": h,
        "behavior_hash_quality": quality,
        "behavior_trade_count": n,
        "first_entry_ts": fe,
        "last_exit_ts": le,
        "unique_candidates": uc,
        "candidate_ids_json": cand_json,
        "strategies_json": strat_json,
        "exit_reasons_json": er_json,
        "sides_json": sides_json,
        "entry_day_count": active_days,
        "avg_trades_per_active_day": avg_td,
    }


def dedupe_behavior_rows(rows_df: pd.DataFrame) -> pd.DataFrame:
    if rows_df is None or len(rows_df) == 0 or "behavior_hash" not in rows_df.columns:
        return rows_df
    d = rows_df.copy()
    sort_cols: list[str] = []
    for c in ("combiner_score", "total_r", "profit_factor_r"):
        if c in d.columns:
            sort_cols.append(c)
    if sort_cols:
        d = d.sort_values(by=sort_cols, ascending=[False] * len(sort_cols), na_position="last")
    return d.drop_duplicates(subset=["behavior_hash"], keep="first").reset_index(drop=True)
