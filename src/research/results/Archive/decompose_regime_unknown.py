"""
Decompose `regime_unknown` trades using existing enriched columns only.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.research.trade_quality_unknown import prepare_unknown_frame, summarize_unknown_by


def _system_label(path: Path) -> str:
    return path.stem.replace("_enriched", "")


def run_one(enriched_path: Path, out_root: Path) -> list[dict]:
    df = pd.read_csv(enriched_path)
    label = _system_label(enriched_path)
    sys_dir = out_root / label
    sys_dir.mkdir(parents=True, exist_ok=True)
    unk = prepare_unknown_frame(df)
    if unk.empty:
        pd.DataFrame({"note": [f"no regime_unknown rows for {label}"]}).to_csv(
            sys_dir / f"{label}_unknown_empty.csv", index=False
        )
        return []
    pairs = [
        ("unk_minute_bucket", f"{label}_unknown_by_minute_bucket.csv"),
        ("unk_vwap_x_bucket", f"{label}_unknown_by_vwap_cross_count.csv"),
        ("unk_reff_bucket", f"{label}_unknown_by_range_efficiency.csv"),
        ("unk_dvwap", f"{label}_unknown_by_distance_from_vwap.csv"),
        ("unk_exit", f"{label}_unknown_by_exit_reason.csv"),
        ("unk_trade_num", f"{label}_unknown_by_trade_number.csv"),
    ]
    key_rows: list[dict] = []
    for bcol, fname in pairs:
        s = summarize_unknown_by(unk, bcol)
        s.to_csv(sys_dir / fname, index=False)
        if not s.empty:
            top = s.sort_values("total_r", ascending=False).head(3)
            for _, r in top.iterrows():
                key_rows.append(
                    {
                        "system": label,
                        "bucket_type": bcol,
                        "bucket": r["bucket"],
                        "trades": int(r["trades"]),
                        "total_r": r["total_r"],
                        "share_unknown_pnl": r["share_unknown_pnl"],
                    }
                )
    lines = [
        f"# Unknown regime decomposition — {label}",
        "",
        f"- unknown trades: **{len(unk)}**",
        f"- unknown total R: **{float(unk['r_multiple'].sum()):.3f}**",
        "",
        "## Interpretation (diagnostic)",
        "",
        "- Early-session concentration in `m0_30` / `m31_60` suggests **insufficient PA window** or opening transition.",
        "- If losses cluster on `stop` in unknown, treat as **stop-sensitive** context.",
        "- `nearest_magnet` / VWAP distance buckets show whether unknown winners sit at **location** edges.",
        "",
    ]
    (sys_dir / f"{label}_unknown_summary.md").write_text("\n".join(lines), encoding="utf-8")
    return key_rows


def write_master_summary(out_root: Path, labels: list[str]) -> None:
    lines = [
        "# Unknown regime decomposition summary (v1.5)",
        "",
        "Per-system CSVs under each `<system>/` folder. Aggregate keys: `unknown_regime_key_buckets.csv`.",
        "",
        "## Router policy suggestion (research only)",
        "",
        "- Default **neutral** on `regime_unknown` until sub-buckets are stable across holdouts.",
        "- If early-minute buckets dominate unknown PnL, prefer **decomposed sub-score** over global penalty.",
        "",
        f"Systems analyzed: {', '.join(labels)}",
        "",
    ]
    (out_root / "unknown_regime_decomposition_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--enriched-root", default=None)
    p.add_argument("--manifest", default=None)
    p.add_argument(
        "--enriched-base",
        default="src/research/results/trade_quality_router_v1/enriched_trades",
        help="With --manifest, load <enriched-base>/<system_label>_enriched.csv",
    )
    p.add_argument("--output-root", required=True)
    args = p.parse_args(argv)
    out = Path(args.output_root)
    if not out.is_absolute():
        out = Path.cwd() / out
    paths: list[Path] = []
    if args.manifest:
        man = pd.read_csv(Path(args.manifest))
        if not Path(args.enriched_base).is_absolute():
            eb = Path.cwd() / args.enriched_base
        else:
            eb = Path(args.enriched_base)
        for _, row in man.iterrows():
            lab = str(row.get("system_label", "")).strip()
            if not lab:
                continue
            ep = eb / f"{lab}_enriched.csv"
            if ep.exists():
                paths.append(ep)
            else:
                print(f"SKIP missing enriched {ep}", file=sys.stderr)
    elif args.enriched_root:
        er = Path(args.enriched_root)
        if not er.is_absolute():
            er = Path.cwd() / er
        paths = sorted(er.glob("*_enriched.csv"))
    else:
        print("Need --enriched-root or --manifest", file=sys.stderr)
        return 2
    labels = []
    all_keys: list[dict] = []
    for ep in paths:
        if not ep.is_absolute():
            ep = Path.cwd() / ep
        if not ep.exists():
            print(f"SKIP missing {ep}", file=sys.stderr)
            continue
        all_keys.extend(run_one(ep, out))
        labels.append(_system_label(ep))
    if all_keys:
        pd.DataFrame(all_keys).to_csv(out / "unknown_regime_key_buckets.csv", index=False)
    write_master_summary(out, labels)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
