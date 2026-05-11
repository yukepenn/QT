"""Build global_branch_leaderboard_v2.csv/md from Layer 1 manifest + selection + diversity."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _count_by_strategy(csv_path: Path | None) -> dict[str, int]:
    if csv_path is None or not csv_path.is_file():
        return {}
    df = pd.read_csv(csv_path)
    if df.empty or "strategy" not in df.columns:
        return {}
    return df.groupby(df["strategy"].astype(str)).size().to_dict()


def _dup_ratio(div_csv: Path | None, strat: str) -> float:
    if div_csv is None or not div_csv.is_file():
        return float("nan")
    d = pd.read_csv(div_csv)
    if "strategy" not in d.columns or "pure_signal_hash" not in d.columns:
        return float("nan")
    sub = d[d["strategy"].astype(str) == strat]
    if sub.empty:
        return float("nan")
    n = len(sub)
    u = sub["pure_signal_hash"].nunique()
    return float(n - u) / float(n) if n else 0.0


def _status(
    *,
    n_full: int,
    n_core: int,
    manifest_status: str,
    dup_ratio: float,
    best_trades: float,
    side_policy: str,
) -> str:
    if str(manifest_status) not in ("ok", "ok_zero_trade"):
        return "DEFER_NO_CANDIDATE" if n_full == 0 else "DEFER_IMPLEMENTATION"
    if n_full == 0:
        return "DEFER_NO_CANDIDATE"
    if n_core == 0:
        return "DEFER_NO_CANDIDATE"
    if dup_ratio == dup_ratio and dup_ratio > 0.75:
        return "DEFER_DUPLICATE_ONLY"
    if best_trades == best_trades and best_trades > 400:
        return "DEFER_COST_FRAGILE"
    if best_trades == best_trades and best_trades < 15:
        return "DEFER_TOO_SPARSE"
    if "short" in str(side_policy).lower() or "both" in str(side_policy).lower():
        return "PASS_TO_GLOBAL_L2_DIAGNOSTIC"
    return "PASS_TO_GLOBAL_L2_CORE"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--layer1-root", type=Path, required=True)
    ap.add_argument("--diversity-csv", type=Path, default=None)
    ap.add_argument("--l2-core-csv", type=Path, default=None)
    ap.add_argument("--output-csv", type=Path, required=True)
    ap.add_argument("--output-md", type=Path, required=True)
    args = ap.parse_args(argv)

    root = args.layer1_root
    if not root.is_absolute():
        root = Path.cwd() / root
    man = root / "sweep_manifest.csv"
    full_csv = root / "selected_candidates.csv"
    if not man.is_file():
        print(f"ERROR missing {man}", file=sys.stderr)
        return 2

    mf = pd.read_csv(man)
    full_c = _count_by_strategy(full_csv if full_csv.is_file() else None)
    core_c = _count_by_strategy(args.l2_core_csv)

    rows: list[dict[str, object]] = []
    for _, r in mf.iterrows():
        strat = str(r.get("strategy", ""))
        dr = _dup_ratio(args.diversity_csv, strat)
        n_f = int(full_c.get(strat, 0))
        n_c = int(core_c.get(strat, 0))
        bt = float(r.get("best_trades") or 0) if str(r.get("best_trades", "")).strip() else float("nan")
        st = _status(
            n_full=n_f,
            n_core=n_c,
            manifest_status=str(r.get("status", "")),
            dup_ratio=dr,
            best_trades=bt,
            side_policy=str(r.get("side_policy", "")),
        )
        rows.append(
            {
                "strategy": strat,
                "family": r.get("family", ""),
                "side_policy": r.get("side_policy", ""),
                "strict_candidate_count_full": n_f,
                "strict_candidate_count_l2_core": n_c,
                "manifest_status": r.get("status", ""),
                "best_total_r": r.get("best_total_r", ""),
                "best_profit_factor": r.get("best_profit_factor", ""),
                "best_max_drawdown_r": r.get("best_max_drawdown_r", ""),
                "best_trades": r.get("best_trades", ""),
                "best_avg_bars_held": r.get("best_avg_bars_held", ""),
                "duplicate_ratio_pure_hash": round(dr, 4) if dr == dr else "",
                "branch_status": st,
            }
        )

    out_csv = args.output_csv
    out_md = args.output_md
    if not out_csv.is_absolute():
        out_csv = Path.cwd() / out_csv
    if not out_md.is_absolute():
        out_md = Path.cwd() / out_md
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)

    hdr = list(df.columns)
    lines = ["# Global branch leaderboard v2", "", "| " + " | ".join(hdr) + " |", "| " + " | ".join(["---"] * len(hdr)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[h]).replace("|", "\\|") for h in hdr) + " |")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_csv}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
