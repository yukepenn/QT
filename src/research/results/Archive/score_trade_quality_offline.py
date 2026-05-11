"""
Offline trade quality score (diagnostic only). Does not affect combiner.
Derives regime bonus/penalty tables from per-system `entry_regime_label_summary.csv` when present.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.research.trade_quality_helpers import profit_factor_r


def _load_regime_tables(analysis_dir: Path | None) -> tuple[dict[str, float], dict[str, float]]:
    bonus: dict[str, float] = {}
    pen: dict[str, float] = {}
    if analysis_dir is None:
        return bonus, pen
    p = analysis_dir / "entry_regime_label_summary.csv"
    if not p.exists():
        return bonus, pen
    t = pd.read_csv(p)
    for _, r in t.iterrows():
        bucket = str(r["bucket"])
        tr = int(r["trades"])
        tot = float(r["total_r"])
        if tr >= 15 and tot >= 3.0:
            bonus[bucket] = 8.0
        elif tr >= 15 and tot <= -3.0:
            pen[bucket] = 10.0
    return bonus, pen


def score_row(
    r: pd.Series,
    regime_bonus: dict[str, float],
    regime_pen: dict[str, float],
    setup_affinity: dict[str, list[str]],
) -> float:
    s = 50.0
    reg = str(r.get("entry_regime_label", "missing"))
    fam = str(r.get("entry_family", r.get("strategy_family", "")))
    stype = setup_affinity.get(fam, [fam])

    # Evidence-based regime adjustment
    if reg in regime_bonus:
        s += regime_bonus[reg]
    if reg in regime_pen:
        s -= regime_pen[reg]

    # Hypothesis: setup affinity (documented as non-evidence)
    if reg == "trading_range" and "vwap" in fam.lower():
        s += 3.0  # hypothesis: small bonus

    vc = r.get("entry_vwap_cross_count")
    try:
        if vc is not None and float(vc) > 8:
            s -= 5.0
    except (TypeError, ValueError):
        pass

    tn = r.get("entry_trade_number_of_day")
    if pd.notna(tn) and float(tn) > 1:
        sf = r.get("entry_prior_trade_same_family")
        if sf is True or sf == 1.0:
            s -= 4.0
    pl = r.get("entry_prior_trade_was_loss")
    try:
        if pl is True or float(pl) == 1.0:
            s -= 3.0
    except (TypeError, ValueError):
        pass

    # Trend alignment (long-only research): continuation setups vs always-in
    ais = str(r.get("entry_always_in_side", ""))
    side = str(r.get("entry_side", r.get("side", "")))
    if "pullback" in str(r.get("entry_strategy", "")).lower() and ais == "always_in_long" and side == "1":
        s += 2.0

    return float(np.clip(s, 0.0, 100.0))


def _max_dd_r(rs: np.ndarray) -> float:
    cum = np.cumsum(rs)
    peak = np.maximum.accumulate(cum)
    dd = cum - peak
    return float(dd.min()) if len(dd) else 0.0


def _ordered_subset(sub: pd.DataFrame) -> pd.DataFrame:
    if sub.empty:
        return sub
    if "entry_ts_utc" in sub.columns:
        return sub.sort_values("entry_ts_utc")
    return sub.sort_index()


def threshold_summary(df: pd.DataFrame, label: str) -> pd.DataFrame:
    sc = df["trade_quality_score"].astype(float).values
    order = np.argsort(sc)
    n = len(df)
    rows = []
    cuts = [
        ("all", None, None),
        ("score_ge_40", 40, None),
        ("score_ge_50", 50, None),
        ("score_ge_60", 60, None),
        ("score_ge_70", 70, None),
    ]
    for name, lo, _ in cuts:
        if name == "all":
            sub = df
        else:
            assert lo is not None
            sub = df[df["trade_quality_score"] >= lo]
        if sub.empty:
            rows.append({"subset": name, "trades": 0, "total_r": 0.0, "avg_r": 0.0, "win_rate": 0.0, "pf_r": 0.0, "max_dd_r_proxy": 0.0})
            continue
        srs = sub["r_multiple"].astype(float)
        rows.append(
            {
                "subset": name,
                "trades": len(sub),
                "total_r": float(srs.sum()),
                "avg_r": float(srs.mean()),
                "win_rate": float((srs > 0).mean()),
                "pf_r": float(profit_factor_r(srs)),
                "max_dd_r_proxy": _max_dd_r(_ordered_subset(sub)["r_multiple"].astype(float).values),
            }
        )
    # Top percentiles by score (in-sample rank)
    for pct, pname in [(80, "top80pct_score"), (60, "top60pct_score"), (40, "top40pct_score")]:
        k = max(1, int(np.ceil(n * pct / 100.0)))
        idx = order[-k:]
        sub = df.iloc[idx]
        srs = sub["r_multiple"].astype(float)
        rows.append(
            {
                "subset": pname,
                "trades": len(sub),
                "total_r": float(srs.sum()),
                "avg_r": float(srs.mean()),
                "win_rate": float((srs > 0).mean()),
                "pf_r": float(profit_factor_r(srs)),
                "max_dd_r_proxy": _max_dd_r(_ordered_subset(sub)["r_multiple"].astype(float).values),
            }
        )
    return pd.DataFrame(rows)


def load_setup_affinity(taxonomy_path: Path) -> dict[str, list[str]]:
    t = pd.read_csv(taxonomy_path)
    out: dict[str, list[str]] = {}
    for _, r in t.iterrows():
        fam = str(r.get("family", "")).strip()
        st = str(r.get("setup_type", "")).strip()
        if fam:
            out[fam] = [st]
    return out


def run_one(
    enriched_path: Path,
    taxonomy_path: Path,
    analysis_dir: Path | None,
    out_dir: Path,
) -> None:
    df = pd.read_csv(enriched_path)
    tax = load_setup_affinity(taxonomy_path)
    rb, rp = _load_regime_tables(analysis_dir)
    scores = [score_row(df.iloc[i], rb, rp, tax) for i in range(len(df))]
    df["trade_quality_score"] = scores
    label = enriched_path.stem.replace("_enriched", "")
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / f"scored_trades_{label}.csv", index=False)
    th = threshold_summary(df, label)
    th.to_csv(out_dir / f"threshold_simulation_{label}.csv", index=False)
    # Decile PnL
    df["quality_decile"] = pd.qcut(df["trade_quality_score"], 10, duplicates="drop")
    dec = df.groupby("quality_decile", observed=True)["r_multiple"].agg(["count", "sum", "mean"])
    dec.to_csv(out_dir / f"pnl_by_quality_decile_{label}.csv")
    meta = {
        "regime_bonus": rb,
        "regime_penalty": rp,
        "note": "Hypothesis components (affinity etc.) documented in regime_router_design_from_evidence_v1.md",
    }
    (out_dir / f"score_rules_resolved_{label}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--enriched-root", default=None)
    p.add_argument("--enriched", default=None)
    p.add_argument("--taxonomy", required=True)
    p.add_argument("--analysis-root", default=None, help="Parent of per-system analysis dirs")
    p.add_argument("--output-root", required=True)
    args = p.parse_args(argv)
    tax_p = Path(args.taxonomy)
    if not tax_p.is_absolute():
        tax_p = Path.cwd() / tax_p
    out_root = Path(args.output_root)
    if not out_root.is_absolute():
        out_root = Path.cwd() / out_root
    aroot = Path(args.analysis_root) if args.analysis_root else None
    if aroot and not aroot.is_absolute():
        aroot = Path.cwd() / aroot

    paths: list[Path] = []
    if args.enriched:
        paths = [Path(args.enriched)]
    elif args.enriched_root:
        er = Path(args.enriched_root)
        if not er.is_absolute():
            er = Path.cwd() / er
        paths = sorted(er.glob("*_enriched.csv"))
    else:
        print("Need --enriched or --enriched-root", file=sys.stderr)
        return 2

    for ep in paths:
        if not ep.is_absolute():
            ep = Path.cwd() / ep
        label = ep.stem.replace("_enriched", "")
        adir = (aroot / label) if aroot else None
        run_one(ep, tax_p, adir, out_root)
        print(f"Scored -> {out_root}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
