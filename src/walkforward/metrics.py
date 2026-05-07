"""Aggregate fold-level smoke metrics."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd


def summarize_fold_results(fold_results: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(fold_results)


def summarize_system_across_folds(fold_summary: pd.DataFrame) -> pd.DataFrame:
    if fold_summary.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for sid, grp in fold_summary.groupby("system_id", dropna=False):
        rows.append(_aggregate_one_system(str(sid), grp))
    return pd.DataFrame(rows)


def _aggregate_one_system(system_id: str, grp: pd.DataFrame) -> dict[str, Any]:
    tr = pd.to_numeric(grp["total_r"], errors="coerce").fillna(0.0)
    stitched_total_r = float(tr.sum())
    trades_sum = int(pd.to_numeric(grp["trades"], errors="coerce").fillna(0).sum())

    pf_vals = pd.to_numeric(grp["profit_factor"], errors="coerce")
    pfr_vals = pd.to_numeric(grp["profit_factor_r"], errors="coerce")

    slip02_tr = grp["slip_0_02_total_r"] if "slip_0_02_total_r" in grp.columns else pd.Series(dtype=float)
    slip03_tr = grp["slip_0_03_total_r"] if "slip_0_03_total_r" in grp.columns else pd.Series(dtype=float)
    slip02_pf = grp["slip_0_02_pf"] if "slip_0_02_pf" in grp.columns else pd.Series(dtype=float)
    slip03_pf = grp["slip_0_03_pf"] if "slip_0_03_pf" in grp.columns else pd.Series(dtype=float)

    pos_mask = tr > 0
    positive_fold_count = int(pos_mask.sum())
    fold_count = len(grp)

    mean_pf = float(np.nanmean(pf_vals)) if len(pf_vals) else float("nan")
    mean_pfr = float(np.nanmean(pfr_vals)) if len(pfr_vals) else float("nan")

    out: dict[str, Any] = {
        "system_id": system_id,
        "fold_count": fold_count,
        "positive_fold_count": positive_fold_count,
        "total_trades": trades_sum,
        "stitched_total_r": stitched_total_r,
        # stitched_pf / stitched_pf_r are mean-of-fold PF metrics (not trade-level stitched PF).
        "stitched_pf": mean_pf,
        "stitched_pf_r": mean_pfr,
        "mean_fold_pf": mean_pf,
        "mean_fold_pf_r": mean_pfr,
        "median_fold_r": float(np.nanmedian(tr)) if len(tr) else float("nan"),
        "worst_fold_r": float(np.nanmin(tr)) if len(tr) else float("nan"),
        "best_fold_r": float(np.nanmax(tr)) if len(tr) else float("nan"),
        "positive_fold_rate": compute_positive_fold_rate(grp),
        "fold_concentration": compute_fold_concentration(grp),
        "slip_0_02_total_r_mean": float(np.nanmean(pd.to_numeric(slip02_tr, errors="coerce"))) if len(slip02_tr) else float("nan"),
        "slip_0_02_pf_mean": float(np.nanmean(pd.to_numeric(slip02_pf, errors="coerce"))) if len(slip02_pf) else float("nan"),
        "slip_0_03_total_r_mean": float(np.nanmean(pd.to_numeric(slip03_tr, errors="coerce"))) if len(slip03_tr) else float("nan"),
        "slip_0_03_pf_mean": float(np.nanmean(pd.to_numeric(slip03_pf, errors="coerce"))) if len(slip03_pf) else float("nan"),
    }

    if "max_drawdown_r" in grp.columns:
        out["stitched_max_drawdown_r"] = float(np.nanmin(pd.to_numeric(grp["max_drawdown_r"], errors="coerce")))
    else:
        out["stitched_max_drawdown_r"] = float("nan")

    flags = interpretation_flags(grp)
    out.update(flags)
    return out


def compute_positive_fold_rate(fold_summary: pd.DataFrame) -> float:
    if fold_summary.empty or "total_r" not in fold_summary.columns:
        return float("nan")
    tr = pd.to_numeric(fold_summary["total_r"], errors="coerce").fillna(0.0)
    return float((tr > 0).mean())


def compute_worst_fold_r(fold_summary: pd.DataFrame) -> float:
    if fold_summary.empty or "total_r" not in fold_summary.columns:
        return float("nan")
    tr = pd.to_numeric(fold_summary["total_r"], errors="coerce")
    return float(np.nanmin(tr))


def compute_fold_concentration(fold_summary: pd.DataFrame) -> float:
    """Share of stitched |total_r| contributed by the single largest-|R| fold."""
    if fold_summary.empty or "total_r" not in fold_summary.columns:
        return float("nan")
    tr = pd.to_numeric(fold_summary["total_r"], errors="coerce").fillna(0.0)
    denom = float(np.sum(np.abs(tr)))
    if denom <= 0:
        return float("nan")
    return float(np.max(np.abs(tr)) / denom)


def interpretation_flags(fold_summary: pd.DataFrame) -> dict[str, Any]:
    """Boolean-ish diagnostics per system (aggregated across folds)."""
    out: dict[str, Any] = {}
    if fold_summary.empty:
        return {
            "positive_total_r": False,
            "pf_above_1": False,
            "pf_r_above_1": False,
            "cost_0_02_survives": False,
            "cost_0_03_survives": False,
            "drawdown_exceeds_insample": float("nan"),
            "drawdown_exceeds_source_baseline": float("nan"),
            "single_fold_dependency": False,
            "trade_2_positive": False,
        }

    tr = pd.to_numeric(fold_summary["total_r"], errors="coerce").fillna(0.0)
    out["positive_total_r"] = bool(tr.sum() > 0)

    if "profit_factor" in fold_summary.columns:
        pf = pd.to_numeric(fold_summary["profit_factor"], errors="coerce")
        out["pf_above_1"] = bool(np.nanmean(pf) >= 1.0) if len(pf) else False
    else:
        out["pf_above_1"] = False

    if "profit_factor_r" in fold_summary.columns:
        pfr = pd.to_numeric(fold_summary["profit_factor_r"], errors="coerce")
        out["pf_r_above_1"] = bool(np.nanmean(pfr) >= 1.0) if len(pfr) else False
    else:
        out["pf_r_above_1"] = False

    if "slip_0_02_total_r" in fold_summary.columns and "slip_0_02_pf" in fold_summary.columns:
        s2tr = pd.to_numeric(fold_summary["slip_0_02_total_r"], errors="coerce")
        s2pf = pd.to_numeric(fold_summary["slip_0_02_pf"], errors="coerce")
        out["cost_0_02_survives"] = bool((s2tr.sum() > 0) and (np.nanmean(s2pf) >= 1.0))
    else:
        out["cost_0_02_survives"] = False

    if "slip_0_03_total_r" in fold_summary.columns and "slip_0_03_pf" in fold_summary.columns:
        s3tr = pd.to_numeric(fold_summary["slip_0_03_total_r"], errors="coerce")
        s3pf = pd.to_numeric(fold_summary["slip_0_03_pf"], errors="coerce")
        out["cost_0_03_survives"] = bool((s3tr.sum() > 0) and (np.nanmean(s3pf) >= 1.0))
    else:
        out["cost_0_03_survives"] = False

    # Legacy column name kept for CSV compatibility; not computed unless an in-sample baseline exists.
    out["drawdown_exceeds_insample"] = float("nan")
    out["drawdown_exceeds_source_baseline"] = float("nan")

    conc = compute_fold_concentration(fold_summary)
    out["single_fold_dependency"] = bool(np.isfinite(conc) and conc >= 0.65)

    if "trade_2_total_r" in fold_summary.columns:
        t2 = pd.to_numeric(fold_summary["trade_2_total_r"], errors="coerce").fillna(0.0)
        out["trade_2_positive"] = bool((t2.sum() > 0) and (float(np.nanmean(t2)) > 0))
    else:
        out["trade_2_positive"] = False

    return out


def trade_number_rs_from_metrics(metrics: dict[str, Any]) -> tuple[float | None, float | None]:
    raw = metrics.get("r_by_daily_trade_number_json") or "{}"
    try:
        d = json.loads(str(raw))
    except json.JSONDecodeError:
        return None, None
    def _get(k: int) -> float | None:
        key = str(k)
        if key not in d:
            return None
        try:
            return float(d[key])
        except (TypeError, ValueError):
            return None
    return _get(1), _get(2)


def metrics_slip_row(metrics_by_slip: dict[float, dict[str, Any]], slip: float) -> dict[str, Any] | None:
    key = None
    for k in metrics_by_slip:
        if abs(float(k) - float(slip)) < 1e-9:
            key = k
            break
    if key is None:
        return None
    m = metrics_by_slip[key]
    return {
        "total_r": m.get("total_r"),
        "profit_factor": m.get("profit_factor"),
        "profit_factor_r": m.get("profit_factor_r"),
        "max_drawdown_r": m.get("max_drawdown_r"),
        "avg_cost_r": m.get("avg_cost_r"),
        "median_cost_r": m.get("median_cost_r"),
        "trades": m.get("trades"),
    }
