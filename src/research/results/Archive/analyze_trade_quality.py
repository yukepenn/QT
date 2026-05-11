"""
Research-only: summarize enriched trades by regime/context buckets and cost sensitivity proxies.
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

from src.research.trade_quality_helpers import (
    bucket_quantiles,
    summarize_bucket,
    write_bucket_md,
)


def _emit_pair(df: pd.DataFrame, bucket_col: str, title: str, out_dir: Path, r_col: str = "r_multiple") -> None:
    if bucket_col not in df.columns:
        return
    s = summarize_bucket(df, bucket_col, r_col=r_col, bars_col="bars_held" if "bars_held" in df.columns else None)
    s.to_csv(out_dir / f"{bucket_col}_summary.csv", index=False)
    write_bucket_md(title, s, str(out_dir / f"{bucket_col}_summary.md"))


def _minute_bucket(m: pd.Series) -> pd.Series:
    x = pd.to_numeric(m, errors="coerce")
    out = pd.Series(["missing"] * len(m), index=m.index, dtype="object")
    out[(x >= 0) & (x < 30)] = "m0_30"
    out[(x >= 30) & (x < 60)] = "m30_60"
    out[(x >= 60) & (x < 120)] = "m60_120"
    out[x >= 120] = "m120p"
    out[x.isna()] = "missing"
    return out


def _orb_ctx_row(r: pd.Series) -> str:
    ah = r.get("entry_above_orb_high")
    bl = r.get("entry_below_orb_low")
    try:
        if pd.notna(ah) and float(ah) >= 1:
            return "above_orb_high"
        if pd.notna(bl) and float(bl) >= 1:
            return "below_orb_low"
    except (TypeError, ValueError):
        pass
    return "inside_or_other"


def analyze_frame(df: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    r_col = "r_multiple"
    if r_col not in df.columns:
        raise ValueError("enriched trades must include r_multiple")

    df = df.copy()
    df["minute_bucket"] = _minute_bucket(df.get("entry_minute_from_open", pd.Series(np.nan, index=df.index)))

    if "entry_vwap_cross_count" in df.columns:
        vc = pd.to_numeric(df["entry_vwap_cross_count"], errors="coerce")
        df["vwap_cross_bucket"] = pd.cut(
            vc, bins=[-np.inf, 2, 5, 10, np.inf], labels=["xc_0_2", "xc_3_5", "xc_6_10", "xc_10p"]
        ).astype(str)
    if "entry_distance_from_vwap_atr" in df.columns:
        df["dist_vwap_bucket"] = bucket_quantiles(
            pd.to_numeric(df["entry_distance_from_vwap_atr"], errors="coerce"), prefix="dv"
        )
    if "entry_trend_score" in df.columns:
        df["trend_bucket"] = bucket_quantiles(
            pd.to_numeric(df["entry_trend_score"], errors="coerce"), prefix="tr"
        )
    if "entry_range_efficiency" in df.columns:
        df["reff_bucket"] = bucket_quantiles(
            pd.to_numeric(df["entry_range_efficiency"], errors="coerce"), prefix="re"
        )

    df["orb_context"] = df.apply(_orb_ctx_row, axis=1)

    if "entry_regime_label" in df.columns:
        _emit_pair(df, "entry_regime_label", "PnL by regime", out_dir)
    if "entry_trade_mode" in df.columns:
        _emit_pair(df, "entry_trade_mode", "PnL by trade mode", out_dir)
    if "entry_always_in_side" in df.columns:
        _emit_pair(df, "entry_always_in_side", "PnL by always-in", out_dir)
    if "entry_regime_label" in df.columns and "strategy" in df.columns:
        df["strat_regime"] = df["strategy"].astype(str) + " | " + df["entry_regime_label"].astype(str)
        _emit_pair(df, "strat_regime", "PnL by strategy and regime", out_dir)
    if "entry_regime_label" in df.columns and "strategy_family" in df.columns:
        df["fam_regime"] = df["strategy_family"].astype(str) + " | " + df["entry_regime_label"].astype(str)
        _emit_pair(df, "fam_regime", "PnL by family and regime", out_dir)
    if "entry_trade_number_of_day" in df.columns:
        _emit_pair(df, "entry_trade_number_of_day", "PnL by trade number of day", out_dir)
    if "entry_prior_trade_was_loss" in df.columns:
        df["prior_loss_bucket"] = df["entry_prior_trade_was_loss"].map(
            {True: "after_loss", False: "after_win", 1.0: "after_loss", 0.0: "after_win"}
        ).fillna("first_or_unknown")
        _emit_pair(df, "prior_loss_bucket", "PnL by prior trade outcome", out_dir)
    if "entry_prior_trade_same_family" in df.columns:
        df["same_family_repeat"] = df["entry_prior_trade_same_family"].map(
            {True: "repeat_same_family", False: "different_or_first"}
        ).fillna("first_or_unknown")
        _emit_pair(df, "same_family_repeat", "PnL by same-family repeat", out_dir)
    _emit_pair(df, "minute_bucket", "PnL by minute bucket", out_dir)
    if "vwap_cross_bucket" in df.columns:
        _emit_pair(df, "vwap_cross_bucket", "PnL by VWAP cross count bucket", out_dir)
    if "dist_vwap_bucket" in df.columns:
        _emit_pair(df, "dist_vwap_bucket", "PnL by distance from VWAP (quantile)", out_dir)
    if "trend_bucket" in df.columns:
        _emit_pair(df, "trend_bucket", "PnL by trend score bucket", out_dir)
    if "reff_bucket" in df.columns:
        _emit_pair(df, "reff_bucket", "PnL by range efficiency bucket", out_dir)
    _emit_pair(df, "orb_context", "PnL by ORB context", out_dir)
    if "exit_reason" in df.columns:
        _emit_pair(df, "exit_reason", "PnL by exit reason", out_dir)

    # Cost sensitivity proxy: symmetric extra slip vs baseline (+0.01/share per leg -> -0.02/risk_per_share R)
    if "risk_per_share" in df.columns:
        risk = pd.to_numeric(df["risk_per_share"], errors="coerce").replace(0, np.nan)
        df["approx_marginal_r_per_0p01_slip_leg"] = -0.01 / risk
        df["approx_total_r_stress_vs_baseline"] = df[r_col] - 0.02 / risk
        df["cost_stress_bucket"] = bucket_quantiles(df["approx_marginal_r_per_0p01_slip_leg"], prefix="cs")
        _emit_pair(df, "cost_stress_bucket", "PnL by marginal slip sensitivity bucket", out_dir)


def _consolidated_key_findings(enriched_paths: list[Path], analysis_roots: list[Path], out_csv: Path) -> None:
    rows = []
    for ep, ar in zip(enriched_paths, analysis_roots):
        label = ep.stem.replace("_enriched", "")
        df = pd.read_csv(ep)
        total_r = float(df["r_multiple"].sum())
        n = len(df)
        if "entry_regime_label" in df.columns:
            best = df.groupby("entry_regime_label")["r_multiple"].sum().sort_values(ascending=False).head(3)
            worst = df.groupby("entry_regime_label")["r_multiple"].sum().sort_values().head(3)
            rows.append(
                {
                    "system_label": label,
                    "trades": n,
                    "total_r": total_r,
                    "top_regimes_by_r_json": json.dumps({str(k): float(v) for k, v in best.items()}),
                    "worst_regimes_by_r_json": json.dumps({str(k): float(v) for k, v in worst.items()}),
                }
            )
        else:
            rows.append({"system_label": label, "trades": n, "total_r": total_r})
    pd.DataFrame(rows).to_csv(out_csv, index=False)


def emit_trade_quality_analysis_summary(out_root: Path, enriched_paths: list[Path]) -> None:
    """Write a short consolidated markdown summary next to per-system folders."""
    lines = [
        "# Trade quality analysis (consolidated)",
        "",
        "Quantile buckets: see per-system `*_summary.md` files. Low-sample rows flagged in CSV.",
        "",
        "## Per-system totals",
        "",
    ]
    for ep in enriched_paths:
        df = pd.read_csv(ep)
        lab = ep.stem.replace("_enriched", "")
        lines.append(
            f"- **{lab}**: n={len(df)}, total_r={float(df['r_multiple'].sum()):.3f}, "
            f"win_rate={(df['r_multiple'] > 0).mean():.3f}"
        )
    lines.extend(
        [
            "",
            "## Cost sensitivity note",
            "",
            "Symmetric proxy: extra `+0.01` slip/share per leg vs baseline adds roughly `-0.02 / risk_per_share` R per round trip "
            "when applied to both entry and exit. Target fills are modeled with slip in the combiner; see design doc for limitations.",
            "",
        ]
    )
    (out_root / "trade_quality_analysis_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--enriched", default=None)
    p.add_argument("--enriched-root", default=None)
    p.add_argument("--output-root", required=True)
    args = p.parse_args(argv)
    out_root = Path(args.output_root)
    if not out_root.is_absolute():
        out_root = Path.cwd() / out_root

    paths: list[Path] = []
    if args.enriched:
        paths = [Path(args.enriched)]
    elif args.enriched_root:
        root = Path(args.enriched_root)
        if not root.is_absolute():
            root = Path.cwd() / root
        paths = sorted(root.glob("*_enriched.csv"))
    else:
        print("Need --enriched or --enriched-root", file=sys.stderr)
        return 2

    all_analysis: list[Path] = []
    for ep in paths:
        if not ep.is_absolute():
            ep = Path.cwd() / ep
        label = ep.stem.replace("_enriched", "")
        sub = out_root / label
        df = pd.read_csv(ep)
        analyze_frame(df, sub)
        all_analysis.append(sub)
        print(f"Analysis -> {sub}", flush=True)

    if len(paths) > 1:
        _consolidated_key_findings(paths, all_analysis, out_root / "trade_quality_key_findings.csv")
    if paths:
        emit_trade_quality_analysis_summary(out_root, paths)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
