"""Build indicator mtp=1/2/3 comparison tables from enriched trade CSVs (research-only)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.research.trade_quality_helpers import summarize_bucket


def _trade_num(df: pd.DataFrame) -> pd.Series:
    n = pd.to_numeric(df.get("entry_trade_number_of_day"), errors="coerce")
    if n.isna().all():
        n = pd.to_numeric(df.get("daily_trade_number"), errors="coerce")
    return n


def summarize_path(path: Path, mtp: int) -> dict:
    df = pd.read_csv(path)
    n = _trade_num(df)
    rs = df["r_multiple"].astype(float)
    out: dict = {"mtp": mtp, "trades": len(df), "total_r": float(rs.sum()), "avg_r": float(rs.mean())}
    for k in (2, 3):
        sub = df.loc[n == k]
        out[f"trades_t{k}"] = len(sub)
        out[f"total_r_trade{k}"] = float(sub["r_multiple"].astype(float).sum()) if len(sub) else 0.0
        out[f"avg_r_trade{k}"] = float(sub["r_multiple"].astype(float).mean()) if len(sub) else float("nan")
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mtp1-enriched", required=True)
    p.add_argument("--mtp2-enriched", required=True)
    p.add_argument("--mtp3-enriched", required=True)
    p.add_argument("--output-root", required=True)
    args = p.parse_args(argv)
    out = Path(args.output_root)
    if not out.is_absolute():
        out = Path.cwd() / out
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for mtp, pth in [(1, args.mtp1_enriched), (2, args.mtp2_enriched), (3, args.mtp3_enriched)]:
        pp = Path(pth)
        if not pp.is_absolute():
            pp = Path.cwd() / pp
        if not pp.exists():
            print(f"MISSING {pp}", file=sys.stderr)
            continue
        rows.append(summarize_path(pp, mtp))
    cmp_df = pd.DataFrame(rows)
    cmp_df.to_csv(out / "indicator_mtp_comparison.csv", index=False)
    # family repeat / prior on mtp2+3
    for mtp, pth, lab in [(2, args.mtp2_enriched, "mtp2"), (3, args.mtp3_enriched, "mtp3")]:
        pp = Path(pth)
        if not pp.is_absolute():
            pp = Path.cwd() / pp
        if not pp.exists():
            continue
        df = pd.read_csv(pp)
        if "entry_prior_trade_same_family" in df.columns:
            sf = df["entry_prior_trade_same_family"]
            df = df.copy()
            df["_sf"] = "first"
            df.loc[sf == True, "_sf"] = "repeat_family"
            df.loc[sf == False, "_sf"] = "diff_family"
            summarize_bucket(df, "_sf").to_csv(out / f"indicator_{lab}_by_family_repeat.csv", index=False)
        if "entry_prior_trade_was_loss" in df.columns:
            pl = df["entry_prior_trade_was_loss"]
            df["_po"] = "first_or_unknown"
            df.loc[pl == True, "_po"] = "after_loss"
            df.loc[pl == False, "_po"] = "after_win"
            summarize_bucket(df, "_po").to_csv(out / f"indicator_{lab}_by_prior_outcome.csv", index=False)
        tn = _trade_num(df)
        summarize_bucket(df.assign(_tn=tn.fillna(0).astype(int)), "_tn").to_csv(
            out / f"indicator_{lab}_trade_number_summary.csv", index=False
        )
    # Narrative summary is curated in-repo: `indicator_mtp_summary.md` (do not auto-overwrite here).
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
