"""
Calendar holdouts and VWAP trade-number stability (research-only).

Uses same offline score components as v1 (`score_trade_quality_offline.score_row`).
Train-derived score thresholds for top-N% subsets are computed on train only, then applied to test.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.research.score_trade_quality_offline import (
    _load_regime_tables,
    load_setup_affinity,
    score_row,
)
from src.research.score_trade_quality_offline import _max_dd_r, _ordered_subset
from src.research.trade_quality_helpers import profit_factor_r, exit_reason_flags


def _session_year(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s.astype(str), errors="coerce").dt.year


def _session_month(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s.astype(str), errors="coerce").dt.month


def _session_quarter(m: pd.Series) -> pd.Series:
    return ((m - 1) // 3 + 1).astype("Int64")


def add_scores(
    df: pd.DataFrame,
    taxonomy_path: Path,
    analysis_dir: Path | None,
) -> pd.DataFrame:
    tax = load_setup_affinity(taxonomy_path)
    rb, rp = _load_regime_tables(analysis_dir)
    scores = [score_row(df.iloc[i], rb, rp, tax) for i in range(len(df))]
    out = df.copy()
    out["trade_quality_score"] = scores
    return out


def subset_metrics(df: pd.DataFrame, name: str) -> dict:
    if df.empty:
        return {
            "subset": name,
            "trades": 0,
            "total_r": 0.0,
            "avg_r": 0.0,
            "win_rate": 0.0,
            "pf_r": 0.0,
            "max_dd_r_proxy": 0.0,
            "n_target": 0,
            "n_stop": 0,
            "low_sample_warning": True,
        }
    rs = df["r_multiple"].astype(float)
    n_t = n_s = 0
    if "exit_reason" in df.columns:
        for ex in df["exit_reason"].astype(str):
            t, s, f = exit_reason_flags(ex)
            if t:
                n_t += 1
            if s:
                n_s += 1
    pf = profit_factor_r(rs)
    return {
        "subset": name,
        "trades": len(df),
        "total_r": float(rs.sum()),
        "avg_r": float(rs.mean()),
        "win_rate": float((rs > 0).mean()),
        "pf_r": float(pf) if math.isfinite(pf) else None,
        "max_dd_r_proxy": _max_dd_r(_ordered_subset(df)["r_multiple"].astype(float).values),
        "n_target": n_t,
        "n_stop": n_s,
        "low_sample_warning": len(df) < 20,
    }


def top_fraction_threshold(train_scores: np.ndarray, top_frac: float) -> float:
    """Minimum score to be in top `top_frac` fraction of train (e.g. 0.8 => top 80%)."""
    if len(train_scores) == 0:
        return 0.0
    q = 1.0 - top_frac
    return float(np.quantile(train_scores, q))


def eval_split(
    df: pd.DataFrame,
    train_mask: pd.Series,
    test_mask: pd.Series,
    split_name: str,
) -> list[dict]:
    rows = []
    train = df.loc[train_mask]
    test = df.loc[test_mask]
    rows.append({**subset_metrics(train, f"{split_name}__train_all"), "split": split_name, "cohort": "train"})
    rows.append({**subset_metrics(test, f"{split_name}__test_all"), "split": split_name, "cohort": "test"})
    ts = train["trade_quality_score"].astype(float).values
    for frac, label in [(0.8, "top80"), (0.6, "top60")]:
        thr = top_fraction_threshold(ts, frac)
        sub = test.loc[test["trade_quality_score"] >= thr]
        rows.append(
            {
                **subset_metrics(sub, f"{split_name}__test_{label}_thr_train"),
                "split": split_name,
                "cohort": "test",
                "train_score_threshold": thr,
                "top_frac": frac,
            }
        )
    for lo, lab in [(60, "score_ge_60")]:
        sub = test.loc[test["trade_quality_score"] >= lo]
        m = subset_metrics(sub, f"{split_name}__test_{lab}")
        m["train_score_threshold"] = float(lo)
        m["top_frac"] = None
        m["split"] = split_name
        m["cohort"] = "test"
        rows.append(m)
    # Leakage diagnostic: test percentile threshold (labeled)
    thr_test = top_fraction_threshold(test["trade_quality_score"].astype(float).values, 0.8)
    sub_leak = test.loc[test["trade_quality_score"] >= thr_test]
    r = subset_metrics(sub_leak, f"{split_name}__test_top80_thr_test_dist_DIAG")
    r["split"] = split_name
    r["cohort"] = "test_leakage_diag"
    r["train_score_threshold"] = thr_test
    r["top_frac"] = 0.8
    rows.append(r)
    return rows


def trade_two_stability(df: pd.DataFrame, out_dir: Path) -> None:
    """VWAP baseline: trade #2 by year/month/regime/exit/prior."""
    d = df.copy()
    d["_y"] = _session_year(d["session_date"])
    d["_m"] = _session_month(d["session_date"])
    d["_q"] = _session_quarter(d["_m"])
    num = pd.to_numeric(d.get("entry_trade_number_of_day"), errors="coerce")
    if num.isna().all():
        num = pd.to_numeric(d.get("daily_trade_number"), errors="coerce")
    t2 = d.loc[num.eq(2)]
    rows = []
    for key, g in t2.groupby("_y", dropna=False):
        rs = g["r_multiple"].astype(float)
        rows.append({"bucket": str(key), "trades": len(g), "total_r": float(rs.sum()), "avg_r": float(rs.mean())})
    pd.DataFrame(rows).to_csv(out_dir / "vwap_trade_number_by_year_t2.csv", index=False)
    rows = []
    for key, g in t2.groupby(["_y", "_m"], dropna=False):
        rs = g["r_multiple"].astype(float)
        rows.append({"year": key[0], "month": key[1], "trades": len(g), "total_r": float(rs.sum())})
    pd.DataFrame(rows).sort_values(["year", "month"]).to_csv(out_dir / "vwap_trade_number_by_month.csv", index=False)
    if "entry_regime_label" in t2.columns:
        s = t2.groupby("entry_regime_label")["r_multiple"].agg(["count", "sum", "mean"]).reset_index()
        s.to_csv(out_dir / "vwap_trade_number_by_regime.csv", index=False)
    if "exit_reason" in t2.columns:
        s = t2.groupby("exit_reason")["r_multiple"].agg(["count", "sum", "mean"]).reset_index()
        s.to_csv(out_dir / "vwap_trade_number_by_exit.csv", index=False)
    pl = t2.get("entry_prior_trade_was_loss")
    if pl is not None:
        t2 = t2.copy()
        t2["_po"] = "other"
        t2.loc[pl == True, "_po"] = "after_loss"
        t2.loc[pl == False, "_po"] = "after_win"
        s = t2.groupby("_po")["r_multiple"].agg(["count", "sum", "mean"]).reset_index()
        s.to_csv(out_dir / "vwap_trade_number_by_prior_outcome.csv", index=False)
    # summary md
    y2023 = t2.loc[t2["_y"] == 2023, "r_multiple"].astype(float).sum() if len(t2) else 0
    y2024 = t2.loc[t2["_y"] == 2024, "r_multiple"].astype(float).sum() if len(t2) else 0
    lines = [
        "# VWAP trade #2 stability",
        "",
        f"- trade #2 count: **{len(t2)}**",
        f"- total R trade #2: **{float(t2['r_multiple'].sum()):.3f}**",
        f"- 2023 trade#2 total_r: **{y2023:.3f}**",
        f"- 2024 trade#2 total_r: **{y2024:.3f}**",
        "",
        "See `vwap_trade_number_by_month.csv` for concentration; small monthly counts are noisy.",
        "",
    ]
    (out_dir / "vwap_trade_number_stability.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--enriched", required=True, help="VWAP baseline enriched CSV")
    p.add_argument("--taxonomy", required=True)
    p.add_argument("--analysis-dir", default=None, help="v1 analysis dir for vwap_baseline_global_l2")
    p.add_argument("--output-root", required=True)
    args = p.parse_args(argv)
    ep = Path(args.enriched)
    if not ep.is_absolute():
        ep = Path.cwd() / ep
    tax = Path(args.taxonomy)
    if not tax.is_absolute():
        tax = Path.cwd() / tax
    out = Path(args.output_root)
    if not out.is_absolute():
        out = Path.cwd() / out
    out.mkdir(parents=True, exist_ok=True)
    adir = Path(args.analysis_dir) if args.analysis_dir else None
    if adir and not adir.is_absolute():
        adir = Path.cwd() / adir
    df = pd.read_csv(ep)
    df = add_scores(df, tax, adir)
    y = _session_year(df["session_date"])
    m = _session_month(df["session_date"])
    all_rows: list[dict] = []
    # 1) train 2023 test 2024
    all_rows.extend(eval_split(df, y == 2023, y == 2024, "y2023_train_y2024_test"))
    # 2) H1 vs H2 (months 1-6 train, 7-12 test) both years combined in each half... spec: train H1 2023+H1 2024 test H2 2023+H2 2024
    train_h1 = m.isin([1, 2, 3, 4, 5, 6])
    test_h2 = m.isin([7, 8, 9, 10, 11, 12])
    all_rows.extend(eval_split(df, train_h1, test_h2, "h1_train_h2_test"))
    # 3) odd vs even month — train odd test even (calendar months)
    train_odd = (m % 2 == 1)
    test_even = (m % 2 == 0)
    all_rows.extend(eval_split(df, train_odd, test_even, "odd_month_train_even_test"))
    # 4) quarters Q1+Q3 train Q2+Q4 test (arbitrary but fixed)
    q = _session_quarter(m)
    all_rows.extend(eval_split(df, q.isin([1, 3]), q.isin([2, 4]), "q13_train_q24_test"))

    res = pd.DataFrame(all_rows)
    res.to_csv(out / "vwap_quality_holdout_results.csv", index=False)
    xfer = res.loc[res["cohort"] == "test", ["split", "subset", "train_score_threshold", "top_frac", "trades", "total_r", "pf_r", "max_dd_r_proxy", "low_sample_warning"]]
    xfer.to_csv(out / "vwap_quality_threshold_transfer.csv", index=False)
    # summary md
    t2024 = res[(res["split"] == "y2023_train_y2024_test") & (res["subset"].str.contains("test_top80_thr_train", na=False))]
    line_top80 = t2024.iloc[0].to_dict() if len(t2024) else {}
    lines = [
        "# VWAP quality score — calendar holdout (v1.5)",
        "",
        "Train thresholds for `top80` / `top60` are **20th / 40th percentile** of **train** scores, applied to **test**.",
        "Row `test_top80_thr_test_dist_DIAG` uses **test** distribution (leakage diagnostic; do not use for decisions).",
        "",
        f"Example 2023→2024 test top80 (train threshold): **{line_top80.get('trades', 'n/a')}** trades, total_r **{line_top80.get('total_r', 'n/a')}**",
        "",
        "## Robustness",
        "",
        "- If test `total_r` under train-threshold top80 beats test `all` inconsistently across splits, treat as **not robust**.",
        "",
    ]
    (out / "vwap_quality_holdout_summary.md").write_text("\n".join(lines), encoding="utf-8")
    trade_two_stability(df, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
