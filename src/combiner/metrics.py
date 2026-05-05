"""Combiner run metrics, combiner_score, and attribution."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

import numpy as np

from src.backtest.metrics import profit_factor_r, summarize_trades
from src.combiner.simulator import REJ_NAMES


def execution_config_from_parts(
    slippage_per_share: float,
    commission_per_trade: float,
    quantity_per_candidate: np.ndarray | None,
) -> dict[str, Any]:
    arr = np.asarray(quantity_per_candidate, dtype=float) if quantity_per_candidate is not None else np.array([])
    qmean = float(np.mean(arr)) if len(arr) else 1.0
    return {
        "slippage_per_share": float(slippage_per_share),
        "commission_per_trade": float(commission_per_trade),
        "quantity": qmean,
    }


def _json_group_sum(
    trades_df: pd.DataFrame, col: str, value: str
) -> dict[str, float]:
    if trades_df is None or len(trades_df) == 0 or col not in trades_df.columns:
        return {}
    g = trades_df.groupby(col, dropna=False)[value].sum()
    return {str(k): float(v) for k, v in g.items()}


def _json_group_count(trades_df: pd.DataFrame, col: str) -> dict[str, int]:
    if trades_df is None or len(trades_df) == 0 or col not in trades_df.columns:
        return {}
    g = trades_df.groupby(col, dropna=False).size()
    return {str(k): int(v) for k, v in g.items()}


def _daily_trade_number_profiles(trades_df: pd.DataFrame) -> dict[str, str]:
    empty_json = "{}"
    keys = [
        "trades_by_daily_trade_number_json",
        "r_by_daily_trade_number_json",
        "pnl_by_daily_trade_number_json",
        "profit_factor_r_by_daily_trade_number_json",
        "avg_r_by_daily_trade_number_json",
        "win_rate_by_daily_trade_number_json",
    ]
    if trades_df is None or len(trades_df) == 0 or "daily_trade_number" not in trades_df.columns:
        return dict.fromkeys(keys, empty_json)
    g = trades_df.groupby("daily_trade_number", dropna=False)
    trades_c: dict[str, int] = {}
    r_sum: dict[str, float] = {}
    pnl_sum: dict[str, float] = {}
    pfr: dict[str, float] = {}
    avgr: dict[str, float] = {}
    wr: dict[str, float] = {}
    for k, sub in g:
        kk = str(int(k))
        trades_c[kk] = int(len(sub))
        if "r_multiple" in sub.columns:
            rs = sub["r_multiple"].astype(float)
            r_sum[kk] = float(rs.sum())
            pfr[kk] = profit_factor_r(rs)
            avgr[kk] = float(rs.mean())
        if "net_pnl" in sub.columns:
            net = sub["net_pnl"].astype(float)
            pnl_sum[kk] = float(net.sum())
            w = int((net > 0).sum())
            n = len(sub)
            wr[kk] = float(w / n) if n else 0.0
    return {
        "trades_by_daily_trade_number_json": json.dumps(trades_c, sort_keys=True),
        "r_by_daily_trade_number_json": json.dumps(r_sum, sort_keys=True),
        "pnl_by_daily_trade_number_json": json.dumps(pnl_sum, sort_keys=True),
        "profit_factor_r_by_daily_trade_number_json": json.dumps(
            {k: (v if v != float("inf") else 9999.0) for k, v in pfr.items()}, sort_keys=True
        ),
        "avg_r_by_daily_trade_number_json": json.dumps(avgr, sort_keys=True),
        "win_rate_by_daily_trade_number_json": json.dumps(wr, sort_keys=True),
    }


def combiner_score(metrics: dict[str, Any]) -> tuple[float, bool]:
    """Generic sweep ranking; penalizes shallow samples."""
    trades_n = int(metrics.get("trades", 0))
    low_trade_count = trades_n < 50
    pf = metrics.get("profit_factor")
    if pf is None or (isinstance(pf, float) and np.isnan(pf)):
        pf = 0.0
    elif pf == float("inf"):
        pf = 25.0

    total_r = float(metrics.get("total_r", 0.0) or 0.0)
    mdd_r = float(metrics.get("max_drawdown_r", 0.0) or 0.0)
    avg_bh = float(metrics.get("avg_bars_held", 0.0) or 0.0)
    mh = int(metrics.get("max_hold_count", 0) or 0)
    eod = int(metrics.get("eod_count", 0) or 0)
    eod_sess = int(metrics.get("end_of_session_count", 0) or 0)
    ed = int(metrics.get("end_of_data_count", 0) or 0)

    score = (
        float(pf)
        + 0.015 * total_r
        - 0.030 * abs(mdd_r)
        - 0.001 * avg_bh
        - 0.020 * mh
        - 0.050 * eod
        - 0.050 * eod_sess
        - 0.050 * ed
    )
    if low_trade_count:
        score -= 2.0
    return score, low_trade_count


def summarize_combiner(
    trades_df: pd.DataFrame,
    rejected_signals_df: pd.DataFrame,
    candidate_signal_log_df: pd.DataFrame,
    *,
    rejection_counts: np.ndarray | None = None,
    execution_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ec = execution_config or {}
    slip = ec.get("slippage_per_share")
    comm = ec.get("commission_per_trade")
    qty = ec.get("quantity")

    if trades_df is None or len(trades_df) == 0:
        base = summarize_trades(
            pd.DataFrame(columns=["net_pnl", "r_multiple", "exit_reason", "bars_held"]),
            slippage_per_share=slip,
            commission_per_trade=comm,
            quantity=qty,
        )
    else:
        base = summarize_trades(
            trades_df,
            slippage_per_share=slip,
            commission_per_trade=comm,
            quantity=qty,
        )

    er = (
        trades_df["exit_reason"].astype(str).str.lower()
        if trades_df is not None and len(trades_df) and "exit_reason" in trades_df.columns
        else pd.Series(dtype=str)
    )
    if len(er):
        base["end_of_session_count"] = int((er == "end_of_session").sum())
    else:
        base["end_of_session_count"] = 0

    log = candidate_signal_log_df if candidate_signal_log_df is not None else pd.DataFrame()
    rej = rejected_signals_df if rejected_signals_df is not None else pd.DataFrame()

    trades_by_strategy = _json_group_count(trades_df, "strategy")
    pnl_by_strategy = _json_group_sum(trades_df, "strategy", "net_pnl")
    r_by_strategy = _json_group_sum(trades_df, "strategy", "r_multiple")

    fam_col = "strategy_family" if trades_df is not None and "strategy_family" in getattr(trades_df, "columns", []) else None
    trades_by_family = _json_group_count(trades_df, fam_col) if fam_col else {}
    pnl_by_family = _json_group_sum(trades_df, fam_col, "net_pnl") if fam_col else {}
    r_by_family = _json_group_sum(trades_df, fam_col, "r_multiple") if fam_col else {}

    trades_by_candidate = _json_group_count(trades_df, "candidate_id")
    pnl_by_candidate = _json_group_sum(trades_df, "candidate_id", "net_pnl")
    r_by_candidate = _json_group_sum(trades_df, "candidate_id", "r_multiple")

    rejected_by_reason: dict[str, int] = {}
    if rejection_counts is not None and len(rejection_counts):
        for i, v in enumerate(rejection_counts):
            if i <= 0 or not v:
                continue
            name = REJ_NAMES.get(i, f"code_{i}")
            rejected_by_reason[name] = int(v)
    elif len(rej) and "rejection_reason" in rej.columns:
        vc = rej["rejection_reason"].astype(str).value_counts()
        rejected_by_reason = {str(k): int(v) for k, v in vc.items()}

    cand_sig = int(len(log))
    rej_n = int(len(rej))
    sel_n = int((log["selected"] == True).sum()) if len(log) and "selected" in log.columns else 0
    if rejection_counts is not None and int(rejection_counts.sum()) > 0:
        rej_n = int(rejection_counts.sum())

    if cand_sig > 0:
        selection_rate = float(sel_n / cand_sig) if cand_sig else 0.0
    elif rejection_counts is not None:
        st = int(base.get("trades", 0))
        tot_ev = st + int(rejection_counts.sum())
        selection_rate = float(st / tot_ev) if tot_ev > 0 else 0.0
    else:
        selection_rate = 0.0

    def _rej_code(name: str) -> int:
        return int(rejected_by_reason.get(name, 0))

    cs, low_tc = combiner_score(base)
    dtn_prof = _daily_trade_number_profiles(trades_df)

    out: dict[str, Any] = dict(base)
    out.update(
        {
            "trades_by_strategy_json": json.dumps(trades_by_strategy, sort_keys=True),
            "pnl_by_strategy_json": json.dumps(pnl_by_strategy, sort_keys=True),
            "r_by_strategy_json": json.dumps(r_by_strategy, sort_keys=True),
            "trades_by_family_json": json.dumps(trades_by_family, sort_keys=True),
            "pnl_by_family_json": json.dumps(pnl_by_family, sort_keys=True),
            "r_by_family_json": json.dumps(r_by_family, sort_keys=True),
            "trades_by_candidate_json": json.dumps(trades_by_candidate, sort_keys=True),
            "pnl_by_candidate_json": json.dumps(pnl_by_candidate, sort_keys=True),
            "r_by_candidate_json": json.dumps(r_by_candidate, sort_keys=True),
            "rejected_by_reason_json": json.dumps(rejected_by_reason, sort_keys=True),
            "candidate_signals": cand_sig,
            "rejected_signals": rej_n,
            "selected_signals": sel_n,
            "selection_rate": selection_rate,
            "combiner_score": cs,
            "low_trade_count": low_tc,
            "wrong_time_window_rejections": _rej_code("wrong_time_window"),
            "existing_position_rejections": _rej_code("existing_position"),
            "daily_loss_limit_rejections": _rej_code("daily_loss_limit"),
            "max_trades_rejections": _rej_code("max_trades_reached"),
            "max_trades_reached_rejections": _rej_code("max_trades_reached"),
            "cooldown_rejections": _rej_code("cooldown_after_loss"),
            "cooldown_after_loss_rejections": _rej_code("cooldown_after_loss"),
            "no_new_after_rejections": _rej_code("no_new_after"),
            "risk_too_small_rejections": _rej_code("risk_too_small"),
            "lower_priority_rejections": _rej_code("lower_priority_conflict"),
            "last_bar_no_entry_rejections": _rej_code("last_bar_no_entry"),
            "session_boundary_no_entry_rejections": _rej_code("session_boundary_no_entry"),
            "disabled_candidate_rejections": _rej_code("disabled_candidate"),
            "opposite_direction_conflict_rejections": _rej_code("opposite_direction_conflict"),
            "invalid_stop_side_rejections": _rej_code("invalid_stop_side"),
            "invalid_target_side_rejections": _rej_code("invalid_target_side"),
            "invalid_target_r_rejections": _rej_code("invalid_target_r"),
            "invalid_price_nan_rejections": _rej_code("invalid_price_nan"),
        }
    )
    out.update(dtn_prof)
    return out
