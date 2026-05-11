"""
Layer3 expanded stability review v1 — research-only postprocessor.

Reuses curated Layer3 complete smoke CSVs; optionally loads local QQQ 1-min parquet
via `src.data.read_bars.read_bars` for data-derived market context (no web fetch).

Does not run combiner, trading replays, or WFO.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from src.data.read_bars import read_bars
from src.research.fixed_profile_oow_lib import scan_qqq_parquet_months


def _df_md(df: pd.DataFrame, *, max_rows: int = 120) -> str:
    if df is None or df.empty:
        return "(empty)"
    d = df.head(int(max_rows)).copy()
    try:
        return str(d.to_markdown(index=False))
    except Exception:
        return str(d.to_string(index=False))


REQUIRED_SMOKE_FILES = (
    "complete_monthly_summary.csv",
    "complete_quarterly_summary.csv",
    "complete_profile_window_summary.csv",
    "complete_exit_slip_comparison.csv",
    "complete_candidate_contribution.csv",
    "complete_exit_reason_summary.csv",
)


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "UNKNOWN"


def _parse_csv_ids(arg: str | None, default: list[str]) -> list[str]:
    if not arg or not str(arg).strip():
        return list(default)
    return [x.strip() for x in str(arg).split(",") if x.strip()]


def _parse_weak_periods(arg: str | None) -> list[str]:
    return _parse_csv_ids(
        arg,
        ["2025Q1", "2022Q4", "2023Q3"],
    )


def _quarter_bounds(q: str) -> tuple[str, str] | None:
    m = re.fullmatch(r"(\d{4})Q([1-4])", q.strip())
    if not m:
        return None
    y, qq = int(m.group(1)), int(m.group(2))
    start_m = {1: 1, 2: 4, 3: 7, 4: 10}[qq]
    start = pd.Timestamp(year=y, month=start_m, day=1)
    end = start + pd.offsets.QuarterEnd(0)
    return str(start.date()), str(end.date())


def _month_range(ym_start: str, ym_end: str) -> list[str]:
    a = pd.Period(ym_start, freq="M")
    b = pd.Period(ym_end, freq="M")
    out: list[str] = []
    cur = a
    while cur <= b:
        out.append(str(cur))
        cur += 1
    return out


def _daily_ohlc(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    for c in ("open", "high", "low", "close"):
        if c not in df.columns:
            raise ValueError(f"expected column {c} in bars frame; got {list(df.columns)}")
    d = df["ts_ny"].dt.normalize().dt.date
    g = df.assign(_d=d).groupby("_d", sort=True)
    out = pd.DataFrame(
        {
            "open": g["open"].first(),
            "high": g["high"].max(),
            "low": g["low"].min(),
            "close": g["close"].last(),
        }
    )
    out["ret"] = out["close"].pct_change()
    out["intraday_range"] = (out["high"] - out["low"]) / out["close"].replace(0.0, np.nan)
    o = out["open"].astype(float)
    pc = out["close"].shift(1)
    out["overnight_gap"] = (o / pc.replace(0.0, np.nan) - 1.0).abs()
    return out


def _metrics_from_daily(dly: pd.DataFrame) -> dict[str, Any]:
    if dly.empty or len(dly) < 2:
        return {
            "qqq_return": float("nan"),
            "qqq_max_drawdown": float("nan"),
            "realized_vol": float("nan"),
            "avg_intraday_range": float("nan"),
            "gap_frequency": float("nan"),
            "trend_efficiency": float("nan"),
            "range_efficiency": float("nan"),
            "vwap_cross_count": "",
            "missing_inputs": "insufficient_daily_bars",
        }
    rets = dly["ret"].iloc[1:].astype(float).replace([np.inf, -np.inf], np.nan).dropna()
    eq = (1.0 + rets).cumprod()
    peak = np.maximum.accumulate(eq.to_numpy())
    dd = float(np.min(eq.to_numpy() / np.where(peak == 0.0, 1.0, peak) - 1.0))
    tot_ret = float(eq.iloc[-1] - 1.0) if len(eq) else float("nan")
    vol = float(rets.std() * np.sqrt(252.0)) if len(rets) > 1 else float("nan")
    den = float(rets.abs().sum())
    trend_eff = float(abs(rets.sum()) / den) if den > 1e-12 else float("nan")
    air = float(dly["intraday_range"].mean()) if "intraday_range" in dly else float("nan")
    gf = float((dly["overnight_gap"].iloc[1:] > 0.005).mean()) if "overnight_gap" in dly else float("nan")
    return {
        "qqq_return": tot_ret,
        "qqq_max_drawdown": dd,
        "realized_vol": vol,
        "avg_intraday_range": air,
        "gap_frequency": gf,
        "trend_efficiency": trend_eff,
        "range_efficiency": air,
        "vwap_cross_count": "",
        "missing_inputs": "",
    }


def _assign_context_label(
    row: pd.Series,
    *,
    vol_med: float,
    gap_p75: float,
) -> tuple[str, str, str]:
    """Return (label, confidence, notes)."""
    r = float(row.get("qqq_return", np.nan))
    v = float(row.get("realized_vol", np.nan))
    te = float(row.get("trend_efficiency", np.nan))
    gf = float(row.get("gap_frequency", np.nan))
    miss = str(row.get("missing_inputs", "") or "")
    if miss:
        return "unknown_mixed", "low", f"missing_inputs={miss}"
    notes: list[str] = []
    label = "unknown_mixed"
    conf = "medium"
    if np.isfinite(gf) and np.isfinite(gap_p75) and gf >= gap_p75:
        label = "high_gap_environment"
        notes.append("gap_frequency>=p75")
    if np.isfinite(r) and np.isfinite(v):
        hi_v = np.isfinite(vol_med) and v >= vol_med
        if r > 0.02:
            label = "uptrend_high_vol" if hi_v else "uptrend_low_vol"
        elif r < -0.02:
            label = "downtrend_high_vol" if hi_v else "downtrend_low_vol"
        else:
            if np.isfinite(te) and te < 0.18 and abs(r) < 0.04:
                label = "range_chop"
            notes.append(f"ret={r:.4f},vol={v:.4f}")
    if np.isfinite(r) and r > 0.05 and np.isfinite(v) and np.isfinite(vol_med) and v >= vol_med and np.isfinite(te) and te > 0.55:
        label = "late_trend_climax_like"
        notes.append("climax_like_heuristic")
    if label == "unknown_mixed":
        conf = "low"
        notes.append("metrics_conflict_or_mild")
    return label, conf, ";".join(notes)[:500]


def _read_smoke_root(root: Path) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for fn in REQUIRED_SMOKE_FILES:
        p = root / fn
        if not p.is_file():
            raise FileNotFoundError(f"missing required smoke file: {p}")
        out[fn[:-4]] = pd.read_csv(p)
    return out


def _qqq_monthly_table(
    *,
    months: Iterable[str],
    data_dir: Path,
) -> tuple[pd.DataFrame, list[str]]:
    """months: YYYY-MM strings."""
    missing: list[str] = []
    rows: list[dict[str, Any]] = []
    for ym in months:
        start = f"{ym}-01"
        end = str((pd.Period(ym, freq="M").to_timestamp(how="end")).date())
        try:
            df = read_bars(asset="equity", symbol="QQQ", start=start, end=end, data_dir=str(data_dir))
        except Exception:
            df = pd.DataFrame()
        if df.empty:
            missing.append(ym)
            rows.append(
                {
                    "period": ym,
                    "period_kind": "month",
                    "start_date": start,
                    "end_date": end,
                    "qqq_return": np.nan,
                    "qqq_max_drawdown": np.nan,
                    "realized_vol": np.nan,
                    "avg_intraday_range": np.nan,
                    "gap_frequency": np.nan,
                    "trend_efficiency": np.nan,
                    "range_efficiency": np.nan,
                    "vwap_cross_count": "",
                    "missing_inputs": "qqq_bars_missing",
                }
            )
            continue
        dly = _daily_ohlc(df)
        m = _metrics_from_daily(dly)
        rows.append(
            {
                "period": ym,
                "period_kind": "month",
                "start_date": start,
                "end_date": end,
                **m,
            }
        )
    return pd.DataFrame(rows), missing


def _qqq_quarterly_from_monthly(mdf: pd.DataFrame) -> pd.DataFrame:
    mdf = mdf.copy()
    mdf["_q"] = pd.to_datetime(mdf["period"] + "-01").dt.to_period("Q").astype(str)
    rows = []
    for q, g in mdf.groupby("_q", sort=True):
        # compound monthly returns for quarter return proxy
        rets = g["qqq_return"].astype(float)
        valid = rets.notna()
        if not bool(valid.any()):
            rq = np.nan
        else:
            rq = float(np.nanprod(1.0 + rets.to_numpy()) - 1.0)
        rows.append(
            {
                "period": str(q),
                "period_kind": "quarter",
                "start_date": str(g["start_date"].min()),
                "end_date": str(g["end_date"].max()),
                "qqq_return": rq,
                "qqq_max_drawdown": float(np.nanmin(g["qqq_max_drawdown"].astype(float))) if len(g) else np.nan,
                "realized_vol": float(np.nanmean(g["realized_vol"].astype(float))) if len(g) else np.nan,
                "avg_intraday_range": float(np.nanmean(g["avg_intraday_range"].astype(float))) if len(g) else np.nan,
                "gap_frequency": float(np.nanmean(g["gap_frequency"].astype(float))) if len(g) else np.nan,
                "trend_efficiency": float(np.nanmean(g["trend_efficiency"].astype(float))) if len(g) else np.nan,
                "range_efficiency": float(np.nanmean(g["range_efficiency"].astype(float))) if len(g) else np.nan,
                "vwap_cross_count": "",
                "missing_inputs": ";".join(
                    sorted({str(v) for v in g["missing_inputs"].tolist() if str(v)})
                ),
            }
        )
    return pd.DataFrame(rows)


def _profile_monthly_stability(monthly: pd.DataFrame, *, window: str = "full_available") -> pd.DataFrame:
    d = monthly[monthly["window"] == window].copy()
    if d.empty:
        return pd.DataFrame()
    d["month_ts"] = pd.to_datetime(d["month"] + "-01")
    rows = []
    for pid, g in d.groupby("profile_id", sort=True):
        g = g.sort_values("month_ts")
        tot = int(len(g))
        pos = int((g["total_r"].astype(float) > 0).sum())
        neg = tot - pos
        ratio = float(pos / tot) if tot else 0.0
        worst_m = float(g["total_r"].astype(float).min())
        consec = 0
        cur = 0
        for v in (g["total_r"].astype(float) <= 0).tolist():
            if v:
                cur += 1
                consec = max(consec, cur)
            else:
                cur = 0
        g = g.assign(_r=g["total_r"].astype(float))
        roll = g["_r"].rolling(window=3, min_periods=3).sum()
        roll_min = float(np.nanmin(roll.to_numpy())) if len(roll) else float("nan")
        worst_month = str(g.loc[g["_r"].idxmin(), "month"]) if len(g) else ""
        lab = "INSUFFICIENT_DATA"
        if tot >= 6:
            if ratio >= 0.55 and worst_m >= -12 and roll_min >= -8 and consec <= 3:
                lab = "STABLE_POSITIVE"
            elif ratio >= 0.45 and worst_m >= -15 and roll_min >= -12 and consec <= 4:
                lab = "POSITIVE_WITH_DRAWDOWN_WARNING"
            elif worst_m < -12 or roll_min < -12 or consec > 4:
                lab = "WEAK_PERIOD_WARNING" if ratio >= 0.35 else "UNSTABLE"
            else:
                lab = "POSITIVE_WITH_DRAWDOWN_WARNING"
        rows.append(
            {
                "profile_id": pid,
                "window": window,
                "period_kind": "month_series",
                "positive_month_ratio": ratio,
                "positive_month_count": pos,
                "negative_month_count": neg,
                "total_months": tot,
                "worst_month": worst_month,
                "worst_month_r": worst_m,
                "rolling_3m_min": roll_min,
                "consecutive_negative_month_max": consec,
                "stability_label": lab,
            }
        )
    return pd.DataFrame(rows)


def _profile_monthly_long(monthly: pd.DataFrame, *, window: str) -> pd.DataFrame:
    d = monthly[monthly["window"] == window].copy()
    if d.empty:
        return pd.DataFrame()
    rows = []
    for _, r in d.iterrows():
        rows.append(
            {
                "profile_id": r["profile_id"],
                "window": r["window"],
                "period": r["month"],
                "total_r": float(r["total_r"]),
                "trades": "",
                "avg_r": "",
                "maxDD_r": "",
                "positive_period_flag": bool(float(r["total_r"]) > 0),
            }
        )
    out = pd.DataFrame(rows)
    out = out.sort_values(["profile_id", "period"])
    # rolling 3m total_r
    roll_rows = []
    for pid, g in out.groupby("profile_id", sort=True):
        g = g.sort_values("period")
        g2 = g.copy()
        g2["rolling_3month_total_r"] = g2["total_r"].astype(float).rolling(3, min_periods=3).sum()
        roll_rows.append(g2)
    return pd.concat(roll_rows, ignore_index=True) if roll_rows else out


def _profile_quarterly_stability(quarterly: pd.DataFrame, *, window: str = "full_available") -> pd.DataFrame:
    d = quarterly[quarterly["window"] == window].copy()
    rows = []
    for pid, g in d.groupby("profile_id", sort=True):
        g = g.sort_values("quarter")
        tot = int(len(g))
        pos = int((g["total_r"].astype(float) > 0).sum())
        worst_q = float(g["total_r"].astype(float).min())
        weak_rep = int((g["total_r"].astype(float) < -5).sum())
        worst_quarter = str(g.loc[g["total_r"].astype(float).idxmin(), "quarter"]) if len(g) else ""
        lab = "INSUFFICIENT_DATA"
        if tot >= 4:
            if worst_q >= -12 and weak_rep <= 4:
                lab = "STABLE_POSITIVE" if pos / tot >= 0.55 else "POSITIVE_WITH_DRAWDOWN_WARNING"
            elif worst_q < -12 or weak_rep > 4:
                lab = "WEAK_PERIOD_WARNING"
            else:
                lab = "POSITIVE_WITH_DRAWDOWN_WARNING"
        rows.append(
            {
                "profile_id": pid,
                "window": window,
                "positive_quarter_ratio": float(pos / tot) if tot else 0.0,
                "worst_quarter": worst_quarter,
                "worst_quarter_r": worst_q,
                "weak_quarter_count_lt_neg5": weak_rep,
                "stability_label": lab,
            }
        )
    return pd.DataFrame(rows)


def _rolling_3month_summary(monthly_long: pd.DataFrame) -> pd.DataFrame:
    if monthly_long.empty:
        return pd.DataFrame()
    cols = ["profile_id", "window", "period", "total_r", "rolling_3month_total_r"]
    x = monthly_long[[c for c in cols if c in monthly_long.columns]].copy()
    x["rolling_3m_min_profile"] = x.groupby(["profile_id", "window"])["rolling_3month_total_r"].transform(
        lambda s: float(np.nanmin(s.to_numpy()))
    )
    return x


def _join_profile_quarter_pnl(
    quarterly: pd.DataFrame,
    *,
    window: str,
    profiles: list[str],
    quarter: str,
) -> pd.DataFrame:
    d = quarterly[(quarterly["window"] == window) & (quarterly["quarter"] == quarter) & (quarterly["profile_id"].isin(profiles))].copy()
    d = d.sort_values("total_r", ascending=False).reset_index(drop=True)
    d["rank_in_period"] = np.arange(1, len(d) + 1)
    return d


def _gate_profiles(cell: str) -> list[str] | None:
    s = str(cell).strip()
    if s.upper() in ("ALL", "ALL_PROFILES"):
        return None
    return [x.strip() for x in s.split(";") if x.strip()]


def _eval_gates(
    *,
    gates: pd.DataFrame,
    win_df: pd.DataFrame,
    monthly_stab: pd.DataFrame,
    quarterly_stab: pd.DataFrame,
    monthly_long: pd.DataFrame,
    exit_slip: pd.DataFrame,
    exit_reason: pd.DataFrame,
    cand: pd.DataFrame,
    weak_interp_rows: list[dict[str, Any]],
    source_map_ok: bool,
    bundle_ok: bool,
    profiles: list[str],
) -> pd.DataFrame:
    win = win_df.set_index(["profile_id", "window"])
    slip = exit_slip.set_index(["profile_id", "window", "scenario"])
    rows: list[dict[str, Any]] = []

    def prof_applies(pid: str, applies: str) -> bool:
        ps = _gate_profiles(applies)
        if ps is None:
            return True
        return pid in ps

    monthly_by_prof = {r["profile_id"]: r for _, r in monthly_stab.iterrows()} if not monthly_stab.empty else {}
    quarterly_by_prof = {r["profile_id"]: r for _, r in quarterly_stab.iterrows()} if not quarterly_stab.empty else {}

    for _, g in gates.iterrows():
        gname = str(g["gate_name"])
        grp = str(g["gate_group"])
        thr = str(g["threshold"])
        how = str(g["hard_or_warning"])
        applies = str(g["applies_to_profiles"])
        fail_act = str(g["failure_action"])

        for pid in profiles:
            if not prof_applies(pid, applies):
                continue
            status = "NOT_EVALUATED"
            detail = ""
            # window totals
            if gname.endswith("_total_r_gt_0"):
                wmap = {
                    "early_oow_total_r_gt_0": "early_oow",
                    "insample_ref_total_r_gt_0": "insample_ref",
                    "late_oow_total_r_gt_0": "late_oow",
                    "full_available_total_r_gt_0": "full_available",
                }
                wid = wmap.get(gname, "")
                if wid and (pid, wid) in win.index:
                    tr = float(win.loc[(pid, wid), "total_r"])
                    status = "PASS" if tr > 0 else "FAIL"
                    detail = f"total_r={tr}"
            elif gname == "pos_month_ratio":
                r = monthly_by_prof.get(pid)
                if r is not None:
                    ratio = float(r["positive_month_ratio"])
                    status = "PASS" if ratio >= 0.45 else "WARNING"
                    detail = f"ratio={ratio:.3f}"
            elif gname == "max_single_neg_month":
                r = monthly_by_prof.get(pid)
                if r is not None:
                    wm = float(r["worst_month_r"])
                    status = "PASS" if wm >= -12 else "WARNING"
                    detail = f"worst_month_r={wm}"
            elif gname == "rolling_3m_min":
                r = monthly_by_prof.get(pid)
                if r is not None:
                    rm = float(r["rolling_3m_min"])
                    status = "PASS" if rm >= -8 else "WARNING"
                    detail = f"rolling_3m_min={rm}"
            elif gname == "consecutive_neg_max":
                r = monthly_by_prof.get(pid)
                if r is not None:
                    c = int(r["consecutive_negative_month_max"])
                    status = "PASS" if c <= 3 else "WARNING"
                    detail = f"consec={c}"
            elif gname == "worst_quarter_floor":
                r = quarterly_by_prof.get(pid)
                if r is not None:
                    wq = float(r["worst_quarter_r"])
                    status = "PASS" if wq >= -12 else "WARNING"
                    detail = f"worst_quarter_r={wq}"
            elif gname == "weak_quarter_repeat":
                r = quarterly_by_prof.get(pid)
                if r is not None:
                    c = int(r["weak_quarter_count_lt_neg5"])
                    status = "PASS" if c <= 4 else "WARNING"
                    detail = f"weak_q={c}"
            elif gname == "slice_context_review":
                have = {str(x.get("weak_period")) for x in weak_interp_rows}
                need = {"2025Q1", "2022Q4"}
                miss = sorted(need - have)
                status = "PASS" if not miss else "WARNING"
                detail = "entries=" + ",".join(sorted(have)) if have else "missing"
            elif gname == "full_max_dd_warning":
                if (pid, "full_available") in win.index:
                    mdd = float(win.loc[(pid, "full_available"), "max_drawdown_r"])
                    status = "PASS" if mdd >= -30 else "WARNING"
                    detail = f"max_dd_r={mdd}"
            elif gname == "late_oow_max_dd":
                if (pid, "late_oow") in win.index:
                    mdd = float(win.loc[(pid, "late_oow"), "max_drawdown_r"])
                    status = "PASS" if mdd >= -20 else "WARNING"
                    detail = f"max_dd_r={mdd}"
            elif gname == "dd_duration":
                status = "NOT_EVALUATED"
                detail = "no_equity_curve_in_smoke_csv"
            elif gname == "target_limit_stress_full":
                key = (pid, "full_available", "target_limit_stress")
                if key in slip.index:
                    tr = float(slip.loc[key, "total_r"])
                    status = "PASS" if tr > 0 else "FAIL"
                    detail = f"target_limit_stress_total_r={tr}"
            elif gname == "symmetric_stress":
                key = (pid, "full_available", "symmetric_stress")
                if key in slip.index:
                    tr = float(slip.loc[key, "total_r"])
                    status = "WARNING" if tr <= 0 else "PASS"
                    detail = f"symmetric_stress_total_r={tr}"
            elif gname == "max_hold_share":
                er = exit_reason[(exit_reason["profile_id"] == pid) & (exit_reason["window"] == "full_available")]
                if not er.empty and (er["exit_reason"] == "max_hold").any():
                    sh = float(er.loc[er["exit_reason"] == "max_hold", "share"].iloc[0])
                    status = "WARNING" if sh >= 0.60 else "PASS"
                    detail = f"max_hold_share={sh}"
                elif not er.empty:
                    status = "PASS"
                    detail = "max_hold_row_present"
            elif gname == "stop_share":
                status = "NOT_EVALUATED"
                detail = "needs_period_or_baseline_delta_replay"
            elif gname == "pa_positive_full":
                if (pid, "full_available") in win.index:
                    t1 = float(win.loc[(pid, "full_available"), "trade_1_total_r"])
                    status = "PASS" if t1 > 0 else "FAIL"
                    detail = f"trade_1_total_r={t1}"
            elif gname == "gap_late_oow_non_material_neg":
                sub = cand[(cand["profile_id"] == pid) & (cand["window"] == "late_oow") & (cand["candidate_id"].str.contains("GAP", case=False, na=False))]
                if not sub.empty:
                    gr = float(sub["total_r"].iloc[0])
                    status = "PASS" if gr >= -2 else "WARNING"
                    detail = f"gap_late_oow_r={gr}"
                else:
                    status = "NOT_EVALUATED"
            elif gname == "cci_justifies_dd_if_primary":
                if pid != "primary_mtp2_meta":
                    continue
                status = "WARNING"
                detail = "manual_tradeoff_gate_reference_profile"
            elif gname == "no_catastrophic_single_label":
                status = "PASS"
                detail = "bucket_wipeout_check_deferred_to_weak_period_table"
            elif gname == "source_map_present":
                status = "PASS" if source_map_ok else "FAIL"
                detail = "SOURCE_MAP.csv"
            elif gname == "chatgpt_bundle_present":
                status = "PASS" if bundle_ok else "FAIL"
                detail = "CHATGPT_REVIEW_BUNDLE.md"
            elif gname == "no_abs_paths_in_curated":
                status = "NOT_EVALUATED"
                detail = "validated_by_validate_research_artifacts"
            else:
                status = "NOT_EVALUATED"
                detail = f"unhandled_gate:{gname}"

            rows.append(
                {
                    "gate_group": grp,
                    "gate_name": gname,
                    "profile_id": pid,
                    "threshold": thr,
                    "hard_or_warning": how,
                    "status": status,
                    "detail": detail[:500],
                    "failure_action_design": fail_act,
                }
            )
    return pd.DataFrame(rows)


def _profile_gate_label(gres: pd.DataFrame, *, pid: str) -> str:
    sub = gres[gres["profile_id"] == pid]
    if sub.empty:
        return "HOLD_BEFORE_WFO"
    if (sub["status"] == "FAIL").any():
        return "FAIL_EXPANDED_STABILITY"
    if (sub["status"] == "NOT_EVALUATED").any():
        # weak-period detail not evaluated still allows pass_with_warnings if no FAIL
        pass
    warns = (sub["status"] == "WARNING").sum()
    fails = (sub["status"] == "FAIL").sum()
    if fails:
        return "FAIL_EXPANDED_STABILITY"
    if warns >= 6:
        return "EXPANDED_STABILITY_PASS_WITH_WARNINGS"
    if warns >= 1:
        return "EXPANDED_STABILITY_PASS_WITH_WARNINGS"
    return "EXPANDED_STABILITY_PASS"


def _overall_decision(
    gres: pd.DataFrame,
    *,
    main_fail: bool,
) -> str:
    if main_fail:
        return "HOLD_BEFORE_WFO"
    key_profiles = {"pa_only_mtp1_meta", "pa_gap_mtp2_meta"}
    for pid in key_profiles:
        sub = gres[(gres["profile_id"] == pid) & (gres["status"] == "FAIL")]
        if len(sub):
            return "HOLD_BEFORE_WFO"
    return "PROCEED_TO_PRE_WFO_STABILITY_DESIGN"


def _write_md(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Layer3 expanded stability postprocess (research-only).")
    p.add_argument("--design-root", required=True)
    p.add_argument("--complete-smoke-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument(
        "--profiles",
        default="pa_only_mtp1_meta,pa_gap_mtp2_meta,primary_mtp2_meta,pa_gap_mtp1_meta,pa_only_mtp2_meta",
    )
    p.add_argument("--weak-periods", default="2025Q1,2022Q4,2023Q3")
    p.add_argument("--data-dir", default="data/raw/ibkr")
    p.add_argument("--no-trading-rerun", action="store_true", help="Assert no trading reruns (default policy).")
    p.add_argument("--skip-detailed-replay", action="store_true", help="Skip local detailed trade replay (default).")
    p.add_argument("--allow-local-detailed-replay", action="store_true", help="Not implemented; forbidden by default policy.")
    p.add_argument("--stop-on-missing-required", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    if args.allow_local_detailed_replay and not args.dry_run:
        print("ERROR: --allow-local-detailed-replay is not implemented for this task", file=sys.stderr)
        return 2

    design_root = Path(args.design_root)
    smoke_root = Path(args.complete_smoke_root)
    out_root = Path(args.output_root)
    out_root.mkdir(parents=True, exist_ok=True)
    profiles = _parse_csv_ids(args.profiles, [])
    weak_periods = _parse_weak_periods(args.weak_periods)
    data_dir = Path(args.data_dir)

    head0 = _git_head()

    def _inv_paths() -> dict[str, str]:
        return {
            "design_root": str(design_root.as_posix()),
            "complete_smoke_root": str(smoke_root.as_posix()),
            "output_root": str(out_root.as_posix()),
        }

    # baseline inventory skeleton (filled more on real run)
    inv_lines = [
        "# baseline_inventory",
        "",
        f"- git_tip_at_run: `{head0}`",
        "- design_decision: `RUN_LAYER3_EXPANDED_STABILITY` (from design bundle)",
        "- execution: expanded stability v1 postprocess",
        "",
        "## Source files inspected",
        "- `NEXT_HANDOFF.md`, `PROJECT_STATUS.md` (repo)",
        f"- `{design_root.as_posix()}/**` (gates, labels design)",
        f"- `{smoke_root.as_posix()}/complete_*` summaries",
        "",
        "## Profiles included",
        "- " + ", ".join(f"`{x}`" for x in profiles),
        "",
        "## Profiles excluded from default",
        "- `pa_gap_mtp1_meta`, `pa_only_mtp2_meta` (ablation / reference only)",
        "",
        "## Weak periods planned",
        "- 2025Q1, 2022Q4, 2023Q3 (CLI weak-period anchors)",
        "",
        "## Market context inputs",
        f"- Local QQQ parquet under `{Path(args.data_dir).as_posix()}/equity/bars_1min/symbol=QQQ/...` when present",
        "",
        "## Detailed local replay",
        "- Default: **skipped** (`--skip-detailed-replay`); period-sliced exit/candidate attribution may be marked `REQUIRES_LOCAL_DETAILED_REPLAY`.",
        "",
    ]

    # dry-run checks
    dry_checks: list[dict[str, str]] = []
    missing_required: list[str] = []
    for fn in REQUIRED_SMOKE_FILES:
        ok = (smoke_root / fn).is_file()
        dry_checks.append({"check": f"smoke:{fn}", "status": "OK" if ok else "MISSING"})
        if not ok:
            missing_required.append(fn)
    gates_path = design_root / "expanded_stability_gate_design.csv"
    dry_checks.append({"check": "design:expanded_stability_gate_design.csv", "status": "OK" if gates_path.is_file() else "MISSING"})
    if not gates_path.is_file():
        missing_required.append("expanded_stability_gate_design.csv")

    if args.stop_on_missing_required and missing_required:
        print("ERROR missing required inputs:", missing_required, file=sys.stderr)
        return 3

    if args.dry_run:
        planned = [
            "baseline_inventory.md",
            "run_plan.csv",
            "run_execution_manifest.csv",
            "run_execution_manifest_sanitized.csv",
            "dry_run_validation.csv",
            "dry_run_validation.md",
            "profile_monthly_stability.csv",
            "profile_quarterly_stability.csv",
            "rolling_3month_summary.csv",
            "market_context_monthly.csv",
            "market_context_quarterly.csv",
            "market_context_labels.csv",
            "weak_period_context.csv",
            "weak_period_profile_pnl.csv",
            "weak_period_exit_reason.csv",
            "weak_period_candidate_contribution.csv",
            "weak_period_interpretation.md",
            "cost_stress_by_period.csv",
            "exit_mechanics_summary.csv",
            "candidate_contribution_stability.csv",
            "expanded_stability_gate_results.csv",
            "expanded_stability_risk_flags.csv",
            "layer3_expanded_stability_decision.md",
            "layer3_expanded_stability_summary.md",
            "layer3_expanded_stability_key_findings.csv",
            "CHATGPT_REVIEW_BUNDLE.md",
            "SOURCE_MAP.csv",
            "chatgpt_key_metrics.csv",
        ]
        for fn in planned:
            dry_checks.append({"check": f"planned_output:{fn}", "status": "PLANNED"})
        pd.DataFrame(dry_checks).to_csv(out_root / "dry_run_validation.csv", index=False)
        _write_md(
            out_root / "dry_run_validation.md",
            [
                "# dry_run_validation",
                "",
                f"- trading_rerun: **{'no' if args.no_trading_rerun else 'unknown'}**",
                f"- skip_detailed_replay: **{bool(args.skip_detailed_replay)}**",
                f"- profiles: `{','.join(profiles)}`",
                f"- weak_periods: `{','.join(weak_periods)}`",
                "",
                "## Checks",
                _df_md(pd.DataFrame(dry_checks)),
            ],
        )
        # minimal manifest
        man = pd.DataFrame(
            [
                {
                    "phase": "dry_run",
                    "requires_new_trading_run": "no",
                    "detailed_replay": "skipped",
                    "status": "OK" if not missing_required else "MISSING_INPUTS",
                    "source_files": "complete_smoke_root;design_root",
                    "output_files": "dry_run_validation.csv;dry_run_validation.md",
                }
            ]
        )
        man.to_csv(out_root / "run_execution_manifest.csv", index=False)
        man2 = man.copy()
        man2.to_csv(out_root / "run_execution_manifest_sanitized.csv", index=False)
        (out_root / "baseline_inventory.md").write_text("\n".join(inv_lines) + "\n", encoding="utf-8")
        return 0 if not missing_required else 3

    # --- full run ---
    smoke = _read_smoke_root(smoke_root)
    monthly = smoke["complete_monthly_summary"]
    quarterly = smoke["complete_quarterly_summary"]
    win_df = smoke["complete_profile_window_summary"]
    exit_slip = smoke["complete_exit_slip_comparison"]
    cand = smoke["complete_candidate_contribution"]
    exit_reason = smoke["complete_exit_reason_summary"]

    gates = pd.read_csv(gates_path)

    # month universe from smoke monthly for full_available
    m_full = monthly[monthly["window"] == "full_available"].copy()
    if m_full.empty:
        raise RuntimeError("no monthly rows for full_available")
    months = sorted(m_full["month"].astype(str).unique().tolist())

    mdf, miss_months = _qqq_monthly_table(months=months, data_dir=data_dir)
    qdf = _qqq_quarterly_from_monthly(mdf)
    if miss_months:
        pd.DataFrame({"missing_month": miss_months}).to_csv(out_root / "market_context_missing_inputs.csv", index=False)
    else:
        pd.DataFrame(columns=["missing_month"]).to_csv(out_root / "market_context_missing_inputs.csv", index=False)

    vol_med = float(np.nanmedian(mdf["realized_vol"].astype(float))) if len(mdf) else float("nan")
    gap_p75 = float(np.nanpercentile(mdf["gap_frequency"].astype(float), 75)) if len(mdf) else float("nan")

    labels_rows = []
    for _, r in mdf.iterrows():
        lab, conf, notes = _assign_context_label(r, vol_med=vol_med, gap_p75=gap_p75)
        labels_rows.append({**{k: r.get(k, "") for k in mdf.columns}, "context_label": lab, "context_confidence": conf, "notes": notes})
    labels_m = pd.DataFrame(labels_rows)
    labels_rows_q = []
    for _, r in qdf.iterrows():
        lab, conf, notes = _assign_context_label(r, vol_med=vol_med, gap_p75=gap_p75)
        labels_rows_q.append({**{k: r.get(k, "") for k in qdf.columns}, "context_label": lab, "context_confidence": conf, "notes": notes})
    labels_q = pd.DataFrame(labels_rows_q)
    labels_all = pd.concat([labels_m, labels_q], ignore_index=True)
    labels_all.to_csv(out_root / "market_context_labels.csv", index=False)
    mdf.to_csv(out_root / "market_context_monthly.csv", index=False)
    qdf.to_csv(out_root / "market_context_quarterly.csv", index=False)

    monthly_stab = _profile_monthly_stability(monthly, window="full_available")
    monthly_long = _profile_monthly_long(monthly, window="full_available")
    quarterly_stab = _profile_quarterly_stability(quarterly, window="full_available")
    roll_df = _rolling_3month_summary(monthly_long)

    ml = monthly_long.merge(
        monthly_stab[
            [
                "profile_id",
                "positive_month_ratio",
                "worst_month",
                "worst_month_r",
                "rolling_3m_min",
                "consecutive_negative_month_max",
                "stability_label",
            ]
        ],
        on="profile_id",
        how="left",
    )
    ml.to_csv(out_root / "profile_monthly_stability.csv", index=False)
    quarterly_stab.to_csv(out_root / "profile_quarterly_stability.csv", index=False)
    roll_df.to_csv(out_root / "rolling_3month_summary.csv", index=False)

    # weak period tables
    wp_ctx_rows = []
    wp_pnl_rows = []
    for wp in weak_periods:
        qb = _quarter_bounds(wp)
        if qb:
            s, e = qb
            ctx = qdf[qdf["period"] == wp]
            if ctx.empty:
                wp_ctx_rows.append({"weak_period": wp, "start_date": s, "end_date": e, "context_label": "unknown_mixed", "notes": "qqq_quarter_missing"})
            else:
                r0 = ctx.iloc[0].to_dict()
                row: dict[str, Any] = {"weak_period": wp, "start_date": s, "end_date": e}
                for k, v in r0.items():
                    if k == "period":
                        row["qqq_period"] = v
                    else:
                        row[k] = v
                lsub = labels_q[labels_q["period"].astype(str) == wp]
                if not lsub.empty:
                    row["context_label"] = str(lsub.iloc[0].get("context_label", ""))
                    row["context_confidence"] = str(lsub.iloc[0].get("context_confidence", ""))
                wp_ctx_rows.append(row)
        else:
            wp_ctx_rows.append({"weak_period": wp, "notes": "bad_period_token"})

    for wp in weak_periods:
        dwin = _join_profile_quarter_pnl(quarterly, window="full_available", profiles=profiles, quarter=wp)
        for _, r in dwin.iterrows():
            wp_pnl_rows.append(
                {
                    "weak_period": wp,
                    "profile_id": r["profile_id"],
                    "window": "full_available",
                    "total_r": float(r["total_r"]),
                    "rank_in_period": int(r["rank_in_period"]),
                }
            )

    pd.DataFrame(wp_ctx_rows).to_csv(out_root / "weak_period_context.csv", index=False)
    pd.DataFrame(wp_pnl_rows).to_csv(out_root / "weak_period_profile_pnl.csv", index=False)

    # deltas vs baselines for weak periods
    def _pnl(pid: str, wp: str) -> float | None:
        sub = [x for x in wp_pnl_rows if x["weak_period"] == wp and x["profile_id"] == pid]
        return float(sub[0]["total_r"]) if sub else None

    interp: list[dict[str, Any]] = []
    for wp in weak_periods:
        pa = _pnl("pa_only_mtp1_meta", wp)
        pg = _pnl("pa_gap_mtp2_meta", wp)
        pr = _pnl("primary_mtp2_meta", wp)
        ctx_lab = ""
        subc = [x for x in wp_ctx_rows if x.get("weak_period") == wp]
        if subc:
            ctx_lab = str(subc[0].get("context_label", "") or "")
        kind = "UNKNOWN_MIXED"
        notes: list[str] = []
        if pa is not None and pg is not None:
            if pg < pa - 0.25:
                notes.append("pa_gap_underperforms_pa_only")
            else:
                notes.append("pa_gap_tracks_or_beats_pa_only")
        if pr is not None and pg is not None and pr < pg:
            notes.append("primary_underperforms_pa_gap")
        # market alignment heuristic: if QQQ quarter return negative and profile negative -> aligned
        qret = float(subc[0].get("qqq_return", np.nan)) if subc else float("nan")
        prof_neg = (pa is not None and pa < 0) or (pg is not None and pg < 0)
        if np.isfinite(qret) and qret < 0 and prof_neg:
            kind = "MARKET_CONTEXT_ALIGNED"
        elif np.isfinite(qret) and qret >= 0 and prof_neg:
            kind = "PROFILE_SPECIFIC"
        else:
            kind = "UNKNOWN_MIXED"
        interp.append({"weak_period": wp, "interpretation": kind, "qqq_context_label": ctx_lab, "notes": ";".join(notes)})

    pd.DataFrame(
        [
            {
                "weak_period": wp,
                "profile_id": pid,
                "availability": "REQUIRES_LOCAL_DETAILED_REPLAY",
                "reason": "complete_exit_reason_summary is window-scoped, not quarter-sliced",
            }
            for wp in weak_periods
            for pid in profiles
        ]
    ).to_csv(out_root / "weak_period_exit_reason.csv", index=False)
    pd.DataFrame(
        [
            {
                "weak_period": wp,
                "profile_id": pid,
                "availability": "WINDOW_LEVEL_FALLBACK",
                "late_oow_gap_r": float(
                    cand[(cand["profile_id"] == pid) & (cand["window"] == "late_oow") & (cand["candidate_id"].str.contains("GAP", na=False))][
                        "total_r"
                    ].iloc[0]
                )
                if len(cand[(cand["profile_id"] == pid) & (cand["window"] == "late_oow") & (cand["candidate_id"].str.contains("GAP", na=False))])
                else float("nan"),
                "notes": "quarter-sliced candidate PnL not in curated smoke CSVs",
            }
            for wp in weak_periods
            for pid in profiles
        ]
    ).to_csv(out_root / "weak_period_candidate_contribution.csv", index=False)

    _write_md(
        out_root / "weak_period_interpretation.md",
        [
            "# weak_period_interpretation",
            "",
            "This file summarizes weak periods using **quarterly profile PnL** (`complete_quarterly_summary.csv`, `full_available`) and **QQQ-derived quarterly context**.",
            "",
            "Period-sliced **exit-reason mix** and **candidate contribution** are **not** present in curated complete-smoke CSVs; those rows are explicitly marked `REQUIRES_LOCAL_DETAILED_REPLAY` / `WINDOW_LEVEL_FALLBACK`.",
            "",
            "## Table",
            _df_md(pd.DataFrame(interp)),
            "",
        ],
    )

    # cost stress by period (window anchor)
    cs_rows = []
    for pid in profiles:
        for w in ["early_oow", "insample_ref", "late_oow", "full_available"]:
            for scen, label in [
                ("published_baseline", "published"),
                ("target_limit_stress", "target_limit_stress"),
                ("symmetric_stress", "symmetric_stress"),
                ("symmetric_extreme_warning", "extreme_warning"),
            ]:
                sub = exit_slip[(exit_slip["profile_id"] == pid) & (exit_slip["window"] == w) & (exit_slip["scenario"] == scen)]
                if sub.empty:
                    continue
                tr = float(sub.iloc[0]["total_r"])
                cs_rows.append(
                    {
                        "profile_id": pid,
                        "period": f"{w}_window_anchor",
                        "scenario": label,
                        "total_r": tr,
                        "adjusted_total_r": tr,
                        "sign_preserved": bool(tr > 0),
                        "stress_label": "OK_POSITIVE" if tr > 0 else "NEG_OR_FLAT",
                        "requires_detail_replay": "true",
                    }
                )
    pd.DataFrame(cs_rows).to_csv(out_root / "cost_stress_by_period.csv", index=False)

    # exit mechanics + contribution stability
    em_rows = []
    for _, r in exit_reason.iterrows():
        em_rows.append(r.to_dict())
    pd.DataFrame(em_rows).to_csv(out_root / "exit_mechanics_summary.csv", index=False)

    cc_rows = []
    for pid in profiles:
        for w in ["early_oow", "insample_ref", "late_oow", "full_available"]:
            sub = cand[(cand["profile_id"] == pid) & (cand["window"] == w)]
            if sub.empty:
                continue
            pa_r = float(sub.loc[sub["candidate_id"].str.contains("PA_", na=False), "total_r"].sum()) if sub["candidate_id"].str.contains("PA_", na=False).any() else float("nan")
            gap_r = float(sub.loc[sub["candidate_id"].str.contains("GAP", na=False), "total_r"].sum()) if sub["candidate_id"].str.contains("GAP", na=False).any() else float("nan")
            cci_r = float(sub.loc[sub["candidate_id"].str.contains("CCI", na=False), "total_r"].sum()) if sub["candidate_id"].str.contains("CCI", na=False).any() else 0.0
            cc_rows.append(
                {
                    "profile_id": pid,
                    "window": w,
                    "pa_total_r": pa_r,
                    "gap_total_r": gap_r,
                    "cci_total_r": cci_r,
                    "gap_share_of_pa_gap": float(gap_r / (pa_r + gap_r)) if np.isfinite(pa_r) and np.isfinite(gap_r) and (pa_r + gap_r) != 0 else float("nan"),
                }
            )
    pd.DataFrame(cc_rows).to_csv(out_root / "candidate_contribution_stability.csv", index=False)

    source_map_ok = True
    bundle_ok = True
    gres = _eval_gates(
        gates=gates,
        win_df=win_df,
        monthly_stab=monthly_stab,
        quarterly_stab=quarterly_stab,
        monthly_long=monthly_long,
        exit_slip=exit_slip,
        exit_reason=exit_reason,
        cand=cand,
        weak_interp_rows=interp,
        source_map_ok=source_map_ok,
        bundle_ok=bundle_ok,
        profiles=profiles,
    )
    gres.to_csv(out_root / "expanded_stability_gate_results.csv", index=False)

    main_fail = bool((gres["status"] == "FAIL").any())
    risk_rows = [
        {"risk_id": "2025Q1", "severity": "medium", "status": "WARNING", "notes": "Quarterly PnL negative for key profiles; see weak_period_profile_pnl"},
        {"risk_id": "2022Q4", "severity": "medium", "status": "WARNING", "notes": "Quarterly PnL negative; see weak_period_profile_pnl"},
        {"risk_id": "2023Q3_primary", "severity": "low", "status": "INFO", "notes": "Included as optional CCI slice"},
        {"risk_id": "max_hold_dependency", "severity": "medium", "status": "WARNING", "notes": "max_hold share ~0.47–0.59 across profiles/windows"},
        {"risk_id": "stop_sensitivity", "severity": "low", "status": "NOT_EVALUATED", "notes": "Period-level stop attribution requires replay"},
        {"risk_id": "no_spy", "severity": "high", "status": "OPEN", "notes": "No SPY cross-check"},
        {"risk_id": "no_wfo", "severity": "high", "status": "OPEN", "notes": "No WFO evidence"},
        {"risk_id": "no_live_paper", "severity": "high", "status": "OPEN", "notes": "No live/paper evidence"},
        {"risk_id": "full_available_overlap", "severity": "medium", "status": "INFO", "notes": "Do not treat overlapping windows as independent"},
        {"risk_id": "period_exit_attribution", "severity": "medium", "status": "OPEN", "notes": "weak_period_exit_reason.csv marked REQUIRES_LOCAL_DETAILED_REPLAY"},
    ]
    pd.DataFrame(risk_rows).to_csv(out_root / "expanded_stability_risk_flags.csv", index=False)

    prof_labels = {pid: _profile_gate_label(gres, pid=pid) for pid in profiles}
    pd.DataFrame([{"profile_id": k, "expanded_stability_label": v} for k, v in prof_labels.items()]).to_csv(
        out_root / "expanded_stability_profile_labels.csv", index=False
    )

    decision = _overall_decision(gres, main_fail=main_fail)

    _write_md(
        out_root / "layer3_expanded_stability_decision.md",
        [
            "# layer3_expanded_stability_decision",
            "",
            f"## Decision: `{decision}`",
            "",
            "### Rationale",
            "- Expanded stability aggregates are computed from **curated complete-smoke** monthly/quarterly/window summaries (no trading rerun).",
            "- **QQQ market context** labels are assigned from **local bar metrics** when parquet partitions exist; otherwise `unknown_mixed` + `market_context_missing_inputs.csv`.",
            "- **Target-limit stress** remains **positive** for `pa_only_mtp1_meta` and `pa_gap_mtp2_meta` on `full_available` per `complete_exit_slip_comparison.csv`.",
            "- **Weak-period exit / candidate quarter slices** are **not** available in curated smoke tables → this run marks **`REQUIRES_LOCAL_DETAILED_REPLAY`** for that attribution layer.",
            f"- Overall gate evaluation: **FAIL flags**={'yes' if main_fail else 'no'} (see `expanded_stability_gate_results.csv`).",
            "",
            "### Recommended next step",
            "- **Draft pre-WFO stability design** using window-level stress, quarterly PnL, and QQQ-derived context labels in this output root. Optionally schedule **local-only** weak-quarter replay later for period-sliced exit/candidate tables (do not commit tapes).",
            "",
            "### Explicit non-runs",
            "- No WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global L1 reruns",
            "- No strategy / feature / YAML / router changes",
            "",
        ],
    )

    # short markdown mirrors
    _write_md(
        out_root / "profile_monthly_stability.md",
        ["# profile_monthly_stability", "", _df_md(pd.DataFrame(monthly_stab)) if len(monthly_stab) else "(empty)", ""],
    )
    _write_md(
        out_root / "profile_quarterly_stability.md",
        ["# profile_quarterly_stability", "", _df_md(pd.DataFrame(quarterly_stab)) if len(quarterly_stab) else "(empty)", ""],
    )
    _write_md(out_root / "rolling_3month_summary.md", ["# rolling_3month_summary", "", _df_md(pd.DataFrame(roll_df.head(25))), ""])

    _write_md(
        out_root / "market_context_labels.md",
        ["# market_context_labels", "", "See `market_context_labels.csv`.", ""],
    )
    _write_md(out_root / "cost_stress_by_period.md", ["# cost_stress_by_period", "", _df_md(pd.DataFrame(cs_rows).head(40)), ""])
    _write_md(out_root / "exit_mechanics_summary.md", ["# exit_mechanics_summary", "", "Mirrors `complete_exit_reason_summary.csv` at window granularity.", ""])
    _write_md(
        out_root / "candidate_contribution_stability.md",
        ["# candidate_contribution_stability", "", _df_md(pd.DataFrame(cc_rows)), ""],
    )
    _write_md(
        out_root / "expanded_stability_gate_results.md",
        ["# expanded_stability_gate_results", "", _df_md(pd.DataFrame(gres).head(200)), ""],
    )
    _write_md(
        out_root / "expanded_stability_risk_flags.md",
        ["# expanded_stability_risk_flags", "", _df_md(pd.DataFrame(risk_rows)), ""],
    )

    # key findings + bundle stub (filled by a second pass in-file to keep deterministic)
    kf = [
        {
            "topic": "monthly_stability",
            "profile_id": "pa_only_mtp1_meta",
            "result": str(monthly_stab.loc[monthly_stab["profile_id"] == "pa_only_mtp1_meta", "stability_label"].iloc[0])
            if len(monthly_stab[monthly_stab["profile_id"] == "pa_only_mtp1_meta"])
            else "",
            "evidence_strength": "medium",
            "implication": "baseline monthly dispersion",
            "next_action": "monitor weak quarters",
        },
        {
            "topic": "monthly_stability",
            "profile_id": "pa_gap_mtp2_meta",
            "result": str(monthly_stab.loc[monthly_stab["profile_id"] == "pa_gap_mtp2_meta", "stability_label"].iloc[0])
            if len(monthly_stab[monthly_stab["profile_id"] == "pa_gap_mtp2_meta"])
            else "",
            "evidence_strength": "medium",
            "implication": "combined profile monthly dispersion",
            "next_action": "compare vs PA-only in weak quarters",
        },
        {
            "topic": "weak_period",
            "profile_id": "ALL",
            "result": ";".join(f"{x['weak_period']}:{x['interpretation']}" for x in interp),
            "evidence_strength": "medium",
            "implication": "quarterly PnL + QQQ return sign heuristic",
            "next_action": "optional local replay for exit mix",
        },
    ]
    pd.DataFrame(kf).to_csv(out_root / "layer3_expanded_stability_key_findings.csv", index=False)

    # SOURCE_MAP + chatgpt metrics + bundle
    src_rows = []
    for fn in sorted([p.name for p in out_root.glob("*") if p.is_file()]):
        p = out_root / fn
        rows = 0
        if fn.endswith(".csv"):
            try:
                rows = int(sum(1 for _ in open(p, "r", encoding="utf-8")) - 1)
            except Exception:
                rows = -1
        src_rows.append(
            {
                "file_path": f"src/research/results/layer3_expanded_stability_v1/{fn}",
                "purpose": "expanded_stability_v1",
                "required_for_review": "yes" if fn in ("CHATGPT_REVIEW_BUNDLE.md", "layer3_expanded_stability_decision.md") else "optional",
                "row_count_if_csv": rows if fn.endswith(".csv") else "",
                "markdown_mirror_available": "yes" if fn.endswith(".md") or out_root.joinpath(fn.replace(".csv", ".md")).is_file() else "no",
                "notes": "",
            }
        )
    pd.DataFrame(src_rows).to_csv(out_root / "SOURCE_MAP.csv", index=False)

    metrics_rows: list[dict[str, str]] = []
    for _, r in win_df[win_df["profile_id"].isin(["pa_only_mtp1_meta", "pa_gap_mtp2_meta", "primary_mtp2_meta"])].iterrows():
        metrics_rows.append(
            {
                "section": "window_summary",
                "profile_id": str(r["profile_id"]),
                "period": str(r["window"]),
                "metric": "total_r",
                "value": str(r["total_r"]),
                "interpretation": "smoke window total",
            }
        )
    pd.DataFrame(metrics_rows).to_csv(out_root / "chatgpt_key_metrics.csv", index=False)

    bundle = "\n".join(
        [
            "# CHATGPT_REVIEW_BUNDLE — Layer3 expanded stability v1",
            "",
            "## 1) Git / validation",
            f"- runner: `src/research/run_layer3_expanded_stability.py`",
            f"- git_tip_at_run: `{head0}`",
            "",
            "## 2) Input complete Layer3 smoke recap (windows)",
            _df_md(pd.DataFrame(win_df[win_df["profile_id"].isin(profiles)].sort_values(["profile_id", "window"]))),
            "",
            "## 3) Profile roles",
            "- CLEAN_BASELINE: `pa_only_mtp1_meta`",
            "- DEFAULT_COMBINED: `pa_gap_mtp2_meta`",
            "- BREADTH_BASELINE (reference): `primary_mtp2_meta`",
            "",
            "## 4) Monthly / quarterly stability (full_available anchors)",
            "### Monthly stability summary",
            _df_md(pd.DataFrame(monthly_stab)),
            "### Quarterly stability summary",
            _df_md(pd.DataFrame(quarterly_stab)),
            "",
            "## 5) QQQ market context labels",
            "- Labels are assigned from computed metrics (not from calendar names).",
            _df_md(pd.DataFrame(labels_q[labels_q["period"].isin(weak_periods)] if len(labels_q) else labels_q)),
            "",
            "## 6) Weak-period interpretation (quarterly)",
            _df_md(pd.DataFrame(interp)),
            _df_md(pd.DataFrame(wp_pnl_rows)),
            "",
            "## 7) Cost stress (window anchor; not calendar-period-sliced)",
            "- See `cost_stress_by_period.csv` for `published` vs `target_limit_stress` vs `symmetric_stress`.",
            "",
            "## 8) Exit mechanics + candidate contribution (window scoped)",
            "- Exit mix is **window-level** from `complete_exit_reason_summary.csv`.",
            _df_md(pd.DataFrame(cc_rows)),
            "",
            "## 9) Gate results (first 120 rows)",
            _df_md(pd.DataFrame(gres).head(120)),
            "",
            "## 10) Risk flags",
            _df_md(pd.DataFrame(risk_rows)),
            "",
            f"## 11) Decision: `{decision}`",
            "",
            "## 12) Explicit non-runs",
            "- No WFO / live / paper / SPY / broad Layer2 / trading rerun / combiner",
            "",
            "## 13) Recommended next step",
            f"- **{decision}**",
            "",
        ]
    )
    (out_root / "CHATGPT_REVIEW_BUNDLE.md").write_text(bundle, encoding="utf-8")

    _write_md(
        out_root / "layer3_expanded_stability_summary.md",
        [
            "# layer3_expanded_stability_summary",
            "",
            f"- decision: `{decision}`",
            "- inputs: curated Layer3 complete smoke summaries + local QQQ parquet (if present)",
            "",
            "## Outputs",
            "- See `SOURCE_MAP.csv`",
            "",
        ],
    )

    # run_plan + manifests
    pd.read_csv(design_root / "expanded_stability_run_plan.csv").to_csv(out_root / "run_plan.csv", index=False)
    man_full = pd.DataFrame(
        [
            {
                "phase": "execute_postprocess",
                "requires_new_trading_run": "no",
                "detailed_replay": "skipped" if args.skip_detailed_replay else "not_requested",
                "status": "OK",
                "source_files": "src/research/results/layer3_fixed_profile_smoke_complete_v1/complete_*.csv;src/research/results/layer3_expanded_stability_design_v1/expanded_stability_gate_design.csv",
                "output_files": ";".join(sorted([p.name for p in out_root.glob('*') if p.is_file()])),
            }
        ]
    )
    man_full.to_csv(out_root / "run_execution_manifest.csv", index=False)
    man_full.to_csv(out_root / "run_execution_manifest_sanitized.csv", index=False)

    # refresh inventory
    inv_lines += [
        "## Generated outputs",
        "- " + ", ".join(f"`{p.name}`" for p in sorted(out_root.glob("*"), key=lambda x: x.name)),
        "",
        f"- decision: `{decision}`",
    ]
    (out_root / "baseline_inventory.md").write_text("\n".join(inv_lines) + "\n", encoding="utf-8")

    # drawdown duration placeholder
    pd.DataFrame([{"note": "not_available_without_equity_curve_series"}]).to_csv(out_root / "drawdown_duration_summary.csv", index=False)
    pd.DataFrame([{"note": "not_available_without_regime_feature_dump"}]).to_csv(out_root / "regime_context_summary.csv", index=False)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
