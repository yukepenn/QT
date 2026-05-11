"""
Pure helpers for fixed-profile out-of-window (OOW) validation (research-only).

No combiner/strategy changes. Designed to postprocess `local_runs/<profile>/<window>/run_*/trades.csv`.
"""
from __future__ import annotations

import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from src.data.read_bars import read_bars
from src.research.analyze_exit_slip_attribution import aggregate as exit_slip_aggregate
from src.research.analyze_exit_slip_attribution import marginal_r_from_slip_delta
from src.research.score_trade_quality_offline import _load_regime_tables, load_setup_affinity, score_row
from src.research.trade_quality_helpers import add_prior_trade_columns, exit_reason_flags, profit_factor_r
from src.research.trade_quality_unknown import prepare_unknown_frame, summarize_unknown_by


@dataclass(frozen=True)
class OowWindow:
    window_id: str
    start: str
    end: str
    label: str


def default_windows(first_date: str | None, last_date: str | None) -> list[OowWindow]:
    """Clip windows to available [first_date, last_date] when both set; else use nominal bounds."""
    def clip(s: str, e: str) -> tuple[str, str] | None:
        if not first_date or not last_date:
            return s, e
        fs, fe = pd.Timestamp(first_date), pd.Timestamp(last_date)
        ws, we = pd.Timestamp(s), pd.Timestamp(e)
        cs = max(ws, fs)
        ce = min(we, fe)
        if ce < cs:
            return None
        return str(cs.date()), str(ce.date())

    out: list[OowWindow] = []
    for wid, s, e, lab in [
        ("early_oow", "2020-01-01", "2022-12-31", "pre-selection"),
        ("insample_ref", "2023-01-01", "2024-12-31", "selection reference"),
        ("late_oow", "2025-01-01", "2026-12-31", "post-selection"),
        ("full_available", "2020-01-01", "2026-12-31", "full span (clipped to data)"),
    ]:
        if wid == "full_available" and first_date and last_date:
            r = clip(first_date, last_date)
        elif wid == "late_oow" and first_date and last_date:
            r = clip("2025-01-01", "2026-12-31")
            if r is None:
                r = clip("2025-01-01", last_date)
        else:
            r = clip(s, e) if first_date and last_date else (s, e)
        if r is None:
            continue
        out.append(OowWindow(wid, r[0], r[1], lab))
    return out


def scan_qqq_parquet_months(
    *,
    symbol: str = "QQQ",
    data_dir: Path | str = "data/raw/ibkr",
) -> tuple[str | None, str | None, pd.DataFrame]:
    """
    Return (first_month, last_month, detail_df) where months are YYYY-MM of existing parquet partitions.
    detail_df rows: year, months_present, parquet_months_count
    """
    base = Path(data_dir) / "equity" / "bars_1min" / f"symbol={symbol.upper()}"
    if not base.is_dir():
        return None, None, pd.DataFrame()

    ym: list[tuple[int, int]] = []
    for p in base.glob("year=*/month=*/data.parquet"):
        m = re.search(r"year=(\d+)/month=(\d+)", str(p).replace("\\", "/"))
        if m:
            ym.append((int(m.group(1)), int(m.group(2))))
    if not ym:
        return None, None, pd.DataFrame()

    ym.sort()
    y0, mo0 = ym[0]
    y1, mo1 = ym[-1]
    first = f"{y0:04d}-{mo0:02d}-01"
    last_day = pd.Timestamp(year=y1, month=mo1, day=1) + pd.offsets.MonthEnd(0)
    last = str(last_day.date())

    by_year: dict[int, set[int]] = {}
    for y, m in ym:
        by_year.setdefault(y, set()).add(m)
    rows = []
    for y in sorted(by_year):
        months = sorted(by_year[y])
        rows.append({"year": y, "months_present": len(months), "parquet_months_count": len(months)})
    return first, last, pd.DataFrame(rows)


def rth_sessions_in_range(
    *,
    symbol: str,
    start: str,
    end: str,
    data_dir: Path | str = "data/raw/ibkr",
) -> int:
    df = read_bars(asset="equity", symbol=symbol, start=start, end=end, data_dir=data_dir)
    if df.empty or "ts_ny" not in df.columns:
        return 0
    d = df["ts_ny"].dt.normalize().dt.date
    return int(d.nunique())


def max_drawdown_r(rs: np.ndarray) -> float:
    if len(rs) == 0:
        return 0.0
    c = np.cumsum(rs.astype(float))
    peak = np.maximum.accumulate(c)
    dd = c - peak
    return float(dd.min())


def metrics_from_trades(trades: pd.DataFrame, *, metrics_json: dict[str, Any] | None = None) -> dict[str, Any]:
    """Core metrics for OOW tables (raw trades; adds trade# if missing)."""
    if trades is None or trades.empty:
        return {
            "trades": 0,
            "sessions": 0,
            "total_r": 0.0,
            "avg_r": 0.0,
            "median_r": 0.0,
            "pf_r": 0.0,
            "win_rate": 0.0,
            "max_dd_r": 0.0,
            "target_count": 0,
            "stop_count": 0,
            "eod_count": 0,
            "max_hold_count": 0,
            "trades_per_day": 0.0,
            "trade_1_total_r": 0.0,
            "trade_2_total_r": 0.0,
            "trade_3_total_r": 0.0,
        }
    t = trades.copy()
    rs = t["r_multiple"].astype(float)
    n_t = n_s = n_e = n_m = 0
    if "exit_reason" in t.columns:
        for ex in t["exit_reason"].astype(str):
            a, b, c = exit_reason_flags(ex)
            if a:
                n_t += 1
            if b:
                n_s += 1
            if c:
                n_e += 1
            if "max_hold" in ex.lower() or "max hold" in ex.lower():
                n_m += 1
    sess = 0
    if "session_date" in t.columns:
        sess = int(t["session_date"].astype(str).nunique())
    tnum_col = "entry_trade_number_of_day" if "entry_trade_number_of_day" in t.columns else None
    if tnum_col is None and "session_date" in t.columns and "entry_ts_utc" in t.columns:
        t = add_prior_trade_columns(t)
        tnum_col = "entry_trade_number_of_day"
    t1 = t2 = t3 = 0.0
    if tnum_col and tnum_col in t.columns:
        g = t.groupby(pd.to_numeric(t[tnum_col], errors="coerce").fillna(0).astype(int))["r_multiple"].sum()
        t1 = float(g.get(1, 0.0))
        t2 = float(g.get(2, 0.0))
        t3 = float(g.get(3, 0.0))
    pf = profit_factor_r(rs)
    mdd = metrics_json.get("max_drawdown_r") if metrics_json else None
    if mdd is None or (isinstance(mdd, float) and math.isnan(float(mdd))):
        mdd = max_drawdown_r(rs.values)
    tpd = float(len(t) / sess) if sess else 0.0
    return {
        "trades": int(len(t)),
        "sessions": sess,
        "total_r": float(rs.sum()),
        "avg_r": float(rs.mean()),
        "median_r": float(rs.median()),
        "pf_r": float(pf) if math.isfinite(pf) else None,
        "win_rate": float((rs > 0).mean()),
        "max_dd_r": float(mdd),
        "target_count": n_t,
        "stop_count": n_s,
        "eod_count": n_e,
        "max_hold_count": n_m,
        "trades_per_day": tpd,
        "trade_1_total_r": t1,
        "trade_2_total_r": t2,
        "trade_3_total_r": t3,
    }


def discover_runs(runs_root: Path) -> list[tuple[str, str, Path]]:
    """
    Expect layout: runs_root/<profile_id>/<window_id>/run_*/metrics.json
    Returns list of (profile_id, window_id, run_dir) using latest run per (profile, window) by mtime.
    """
    runs_root = runs_root.resolve()
    if not runs_root.is_dir():
        return []
    best: dict[tuple[str, str], Path] = {}
    for metrics_path in runs_root.glob("*/*/run_*/metrics.json"):
        run_dir = metrics_path.parent
        parts = run_dir.relative_to(runs_root).parts
        if len(parts) < 3:
            continue
        profile, window = parts[0], parts[1]
        key = (profile, window)
        prev = best.get(key)
        if prev is None or run_dir.stat().st_mtime > prev.stat().st_mtime:
            best[key] = run_dir
    out = [(p, w, d) for (p, w), d in sorted(best.items())]
    return out


def exit_slip_with_extreme(df: pd.DataFrame) -> pd.DataFrame:
    """Symmetric extra slip vs baseline using 0.03/share (warning tier), with target exit leg relief."""
    base, ext = 0.01, 0.03
    d = exit_slip_aggregate(df.copy())
    extra: list[float] = []
    for _, row in d.iterrows():
        rk = float(row["risk_per_share"]) if pd.notna(row["risk_per_share"]) else float("nan")
        t, _, _ = exit_reason_flags(str(row["exit_reason"]))
        sym_ext = marginal_r_from_slip_delta(rk, 2.0 * (ext - base))
        tgt_rec = marginal_r_from_slip_delta(rk, -(ext - base)) if t else 0.0
        extra.append(sym_ext + tgt_rec)
    d["symmetric_extreme_r"] = d["r_multiple"].astype(float) + pd.Series(extra, index=d.index)
    return d


def exit_slip_scenarios_table(trades: pd.DataFrame, label: str) -> pd.DataFrame:
    if trades.empty or "risk_per_share" not in trades.columns:
        return pd.DataFrame()
    d = exit_slip_aggregate(trades.copy())
    d_ext = exit_slip_with_extreme(trades)
    rows = []
    for scenario, series in [
        ("published", d["r_multiple"]),
        ("symmetric_stress", d["symmetric_stress_r"]),
        ("target_limit_stress", d["target_limit_adjusted_stress_r"]),
        ("symmetric_extreme", d_ext["symmetric_extreme_r"]),
    ]:
        v = series.astype(float)
        pf = profit_factor_r(v)
        rows.append(
            {
                "label": label,
                "scenario": scenario,
                "trades": len(v),
                "total_r": float(v.sum()),
                "avg_r": float(v.mean()),
                "pf_r": float(pf) if math.isfinite(pf) else None,
            }
        )
    return pd.DataFrame(rows)


def score_transfer_rows(
    trades: pd.DataFrame,
    *,
    taxonomy: Path,
    analysis_dir: Path | None,
    train_start: str,
    train_end: str,
    test_label: str,
) -> list[dict[str, Any]]:
    """Train top80/top60 thresholds on [train_start, train_end] session dates; apply to all trades in DF."""
    if trades.empty or "session_date" not in trades.columns:
        return []
    if "entry_regime_label" not in trades.columns:
        return []
    tax = load_setup_affinity(taxonomy)
    rb, rp = _load_regime_tables(analysis_dir)
    df = trades.copy()
    scores = [score_row(df.iloc[i], rb, rp, tax) for i in range(len(df))]
    df["trade_quality_score"] = scores
    sd = pd.to_datetime(df["session_date"].astype(str), errors="coerce")
    t0, t1 = pd.Timestamp(train_start), pd.Timestamp(train_end)
    train_mask = (sd >= t0) & (sd <= t1)
    train = df.loc[train_mask]
    test = df.loc[~train_mask]
    rows: list[dict[str, Any]] = []

    def pack(sub: pd.DataFrame, name: str, thr: float | None, top_frac: float | None) -> dict[str, Any]:
        if sub.empty:
            return {
                "test_label": test_label,
                "subset": name,
                "trades": 0,
                "total_r": 0.0,
                "avg_r": 0.0,
                "pf_r": 0.0,
                "win_rate": 0.0,
                "max_dd_r_proxy": 0.0,
                "n_target": 0,
                "n_stop": 0,
                "train_score_threshold": thr,
                "top_frac": top_frac,
                "low_sample_warning": True,
            }
        rs = sub["r_multiple"].astype(float)
        nt = ns = 0
        if "exit_reason" in sub.columns:
            for ex in sub["exit_reason"].astype(str):
                a, b, _ = exit_reason_flags(ex)
                if a:
                    nt += 1
                if b:
                    ns += 1
        pf = profit_factor_r(rs)
        dd = max_drawdown_r(rs.values)
        return {
            "test_label": test_label,
            "subset": name,
            "trades": len(sub),
            "total_r": float(rs.sum()),
            "avg_r": float(rs.mean()),
            "pf_r": float(pf) if math.isfinite(pf) else None,
            "win_rate": float((rs > 0).mean()),
            "max_dd_r_proxy": float(dd),
            "n_target": nt,
            "n_stop": ns,
            "train_score_threshold": thr,
            "top_frac": top_frac,
            "low_sample_warning": len(sub) < 20,
        }

    rows.append({**pack(train, "train_all", None, None), "cohort": "train"})
    rows.append({**pack(test, "test_all", None, None), "cohort": "test"})
    ts = train["trade_quality_score"].astype(float).values
    for frac, lab in [(0.8, "top80_train_thr"), (0.6, "top60_train_thr")]:
        q = 1.0 - frac
        thr = float(np.quantile(ts, q)) if len(ts) else 0.0
        sub = test.loc[test["trade_quality_score"] >= thr]
        rows.append({**pack(sub, lab, thr, frac), "cohort": "test"})
    sub60 = test.loc[test["trade_quality_score"] >= 60.0]
    rows.append({**pack(sub60, "score_ge_60", 60.0, None), "cohort": "test"})
    return rows


def regime_summary_from_trades(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty or "entry_regime_label" not in trades.columns:
        return pd.DataFrame()
    g = (
        trades.groupby("entry_regime_label", dropna=False)["r_multiple"]
        .agg(count="count", total_r="sum", avg_r="mean")
        .reset_index()
        .rename(columns={"entry_regime_label": "bucket"})
    )
    return g


def unknown_summary_from_trades(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    if "entry_regime_label" not in trades.columns:
        return pd.DataFrame()
    unk = prepare_unknown_frame(trades)
    if unk.empty:
        return pd.DataFrame({"note": ["no regime_unknown rows"]})
    return summarize_unknown_by(unk, "unk_minute_bucket", min_n=3)


def insample_expected_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "profile_id": "vwap_mtp2",
                "trades_ref": 337,
                "total_r_ref": 42.2,
                "notes": "Global L2 VWAP core leader (v1 trade-quality baseline)",
            },
            {
                "profile_id": "vwap_mtp1",
                "trades_ref": 294,
                "total_r_ref": 36.7,
                "notes": "Lower-turnover diagnostic (daily_max_loss_r=-1.5, mtp=1)",
            },
            {
                "profile_id": "indicator_mtp1",
                "trades_ref": 502,
                "total_r_ref": 18.76,
                "notes": "Fixed-profile replay (current combiner); legacy v1.5 doc ~43.55R not reproduced — see insample_sanity_failure.md",
            },
            {
                "profile_id": "indicator_mtp2",
                "trades_ref": 1002,
                "total_r_ref": 46.51,
                "notes": "Fixed-profile replay anchor; legacy v1.5 ~72R not reproduced",
            },
            {
                "profile_id": "indicator_mtp3",
                "trades_ref": 1327,
                "total_r_ref": 58.01,
                "notes": "Fixed-profile replay anchor; legacy v1.5 ~79R not reproduced; high turnover",
            },
        ]
    )


def sanity_pass(actual: dict[str, Any], ref: dict[str, Any], *, trades_rtol: float = 0.08, r_atol: float = 3.0) -> bool:
    if actual.get("trades", 0) == 0:
        return False
    tr, ar = ref.get("trades_ref"), ref.get("total_r_ref")
    if not tr or ar is None:
        return True
    ok_n = abs(actual["trades"] - int(tr)) <= max(5, int(tr) * trades_rtol)
    ok_r = abs(actual["total_r"] - float(ar)) <= r_atol
    return bool(ok_n and ok_r)


CANDIDATE_ROOT_REL = "src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates"


@dataclass(frozen=True)
class FixedProfileSpec:
    profile_id: str
    config_filename: str
    candidate_set: str


def fixed_profile_specs() -> list[FixedProfileSpec]:
    return [
        FixedProfileSpec("vwap_mtp2", "layer2_fixed_vwap_mtp2.yaml", "vwap_core"),
        FixedProfileSpec("vwap_mtp1", "layer2_fixed_vwap_mtp1.yaml", "vwap_core"),
        FixedProfileSpec("indicator_mtp1", "layer2_fixed_indicator_mtp1.yaml", "indicator_completion_core"),
        FixedProfileSpec("indicator_mtp2", "layer2_fixed_indicator_mtp2.yaml", "indicator_completion_core"),
        FixedProfileSpec("indicator_mtp3", "layer2_fixed_indicator_mtp3.yaml", "indicator_completion_core"),
    ]


def spec_by_profile_id(pid: str) -> FixedProfileSpec | None:
    for s in fixed_profile_specs():
        if s.profile_id == pid:
            return s
    return None


def load_window_bounds(output_root: Path, *, data_dir: Path | str = "data/raw/ibkr") -> dict[str, tuple[str, str]]:
    """
    window_id -> (start, end). Prefer data_availability.csv from inspect-data;
    else scan parquet + default_windows.
    """
    csv_path = output_root / "data_availability.csv"
    if csv_path.is_file():
        df = pd.read_csv(csv_path)
        if "window_id" in df.columns and "window_start" in df.columns and "window_end" in df.columns:
            return {
                str(r["window_id"]): (str(r["window_start"]), str(r["window_end"]))
                for _, r in df.iterrows()
            }
    first_m, last_m, _ = scan_qqq_parquet_months(data_dir=data_dir)
    first_d = str(pd.Timestamp(first_m).date()) if first_m else None
    last_d = str(pd.Timestamp(last_m).date()) if last_m else None
    return {w.window_id: (w.start, w.end) for w in default_windows(first_d, last_d)}


def parse_csv_ids(arg: str | None, default: list[str]) -> list[str]:
    if not arg or not str(arg).strip():
        return list(default)
    return [x.strip() for x in str(arg).split(",") if x.strip()]


def combiner_argv(
    *,
    repo_root: Path,
    output_root: Path,
    spec: FixedProfileSpec,
    window_id: str,
    start: str,
    end: str,
    data_dir: str = "data/raw/ibkr",
    top_per_strategy: int = 3,
    tag: str = "fixed_profile",
    detailed: bool = False,
    python_executable: str | None = None,
) -> list[str]:
    """Argv for `python -m src.combiner.run` (no `--use-signal-cache`)."""
    cr = repo_root / CANDIDATE_ROOT_REL
    cfg = output_root / "configs" / spec.config_filename
    out_combiner = output_root / "local_runs" / spec.profile_id / window_id
    py = python_executable or sys.executable
    argv = [
        py,
        "-m",
        "src.combiner.run",
        "--candidate-root",
        str(cr),
        "--config",
        str(cfg),
        "--asset",
        "equity",
        "--symbol",
        "QQQ",
        "--start",
        start,
        "--end",
        end,
        "--candidate-set",
        spec.candidate_set,
        "--output-root",
        str(out_combiner),
        "--tag",
        tag,
        "--top-per-strategy",
        str(top_per_strategy),
        "--data-dir",
        data_dir,
    ]
    if not detailed:
        argv.append("--no-detailed")
    return argv


def trades_path_for_postprocess(run_dir: Path) -> Path | None:
    """Prefer enriched trades (local-only) when present."""
    en = run_dir / "trades_enriched.csv"
    raw = run_dir / "trades.csv"
    if en.is_file():
        return en
    if raw.is_file():
        return raw
    return None


def run_dir_is_complete(run_dir: Path) -> bool:
    if not (run_dir / "metrics.json").is_file():
        return False
    tp = trades_path_for_postprocess(run_dir)
    if tp is None:
        return False
    try:
        return int(pd.read_csv(tp).shape[0]) > 0
    except Exception:
        return False


def latest_run_dir(runs_root: Path, profile_id: str, window_id: str) -> Path | None:
    discovered = discover_runs(runs_root)
    for p, w, d in discovered:
        if p == profile_id and w == window_id:
            return d
    return None


def decide_label(metrics_rows: Iterable[dict[str, Any]]) -> str:
    rows = [r for r in metrics_rows if r.get("status") == "OK"]
    if not rows:
        return "NEED_MORE_FIXED_PROFILE_OOW"
    prim_oow = [
        r
        for r in rows
        if r.get("profile_id") in ("vwap_mtp2", "vwap_mtp1", "indicator_mtp1")
        and r.get("window_id") in ("early_oow", "late_oow")
    ]
    if not prim_oow:
        return "NEED_MORE_FIXED_PROFILE_OOW"
    pos = sum(1 for r in prim_oow if float(r.get("total_r") or 0) > 5.0)
    neg = sum(1 for r in prim_oow if float(r.get("total_r") or 0) < -5.0)
    if pos >= 2 and neg == 0:
        return "PROCEED_TO_LAYER3_FIXED_PROFILE_SMOKE_DESIGN"
    if neg >= 2 and pos == 0:
        return "REVISIT_LAYER2_CANDIDATE_SELECTION"
    return "NEED_MORE_FIXED_PROFILE_OOW"
