"""Build consolidated MD/CSV comparing baseline Global L2 vs tuned diagnostic roots."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.combiner.analyze_layer2_cost_turnover import (
    cost_adjusted_objective,
    family_diversity_count,
    stress_labels,
)


def _stress_row_for_combo(cost_df: pd.DataFrame, combo_id: int) -> dict[str, float]:
    if cost_df is None or len(cost_df) == 0:
        return {}
    sub = cost_df[cost_df["source_combo_id"] == combo_id]
    out: dict[str, float] = {}
    for slip in (0.01, 0.02, 0.03):
        s2 = sub[sub["slippage_per_share"] == slip]
        if len(s2):
            r = s2.iloc[0]
            out[f"total_r_{slip:g}"] = float(r["total_r"])
            out[f"profit_factor_{slip:g}"] = float(r["profit_factor"])
            if "max_drawdown_r" in r.index:
                out[f"max_drawdown_r_{slip:g}"] = float(r["max_drawdown_r"])
    return out


def _profile_from_root(label: str, root: Path) -> dict[str, Any]:
    tu = pd.read_csv(root / "top_unique_systems.csv")
    tu = tu.sort_values(["combiner_score", "profit_factor", "total_r"], ascending=[False, False, False])
    best = tu.iloc[0]
    cid = int(best["combo_id"])
    cost_path = root / "cost_stress" / "cost_stress_results.csv"
    cost_long = pd.read_csv(cost_path) if cost_path.exists() else pd.DataFrame()
    st = _stress_row_for_combo(cost_long, cid)
    tr01 = float(st.get("total_r_0.01", best["total_r"]))
    pf01 = float(st.get("profit_factor_0.01", best["profit_factor"]))
    mdd = float(st.get("max_drawdown_r_0.01", best["max_drawdown_r"]))
    tr02 = float(st.get("total_r_0.02", float("nan")))
    tr03 = float(st.get("total_r_0.03", float("nan")))
    pf02 = float(st.get("profit_factor_0.02", float("nan")))
    pf03 = float(st.get("profit_factor_0.03", float("nan")))
    trades = int(best["trades"])
    cidj = str(best.get("candidate_ids_json", "[]"))
    divc = family_diversity_count(cidj)
    lbl = stress_labels(tr01, tr02, tr03, pf01, pf02, pf03)
    cao = cost_adjusted_objective(
        total_r_001=tr01,
        pf_001=pf01,
        total_r_002=tr02,
        pf_002=pf02,
        total_r_003=tr03,
        pf_003=pf03,
        trades=float(trades),
        max_drawdown_r_001=mdd,
        family_diversity_count=divc,
    )
    decision = "COST_FRAGILE"
    if not math.isnan(tr02) and tr02 > 0 and not math.isnan(pf02) and pf02 > 1.05:
        decision = "COST_ROBUST" if (not math.isnan(tr03) and tr03 >= 0) else "THIN_BUT_POSITIVE"
    if divc >= 3 and decision == "COST_ROBUST":
        decision = "MULTI_FAMILY_PROMISING"
    return {
        "label": label,
        "combo_id": cid,
        "candidate_set": best["candidate_set"],
        "candidate_ids_json": cidj,
        "n_strategies_distinct": divc,
        "trades": trades,
        "total_r_0.01": tr01,
        "profit_factor_0.01": pf01,
        "max_drawdown_r_0.01": mdd,
        "total_r_0.02": tr02,
        "profit_factor_0.02": pf02,
        "total_r_0.03": tr03,
        "profit_factor_0.03": pf03,
        "r_ret_01_to_02": lbl.get("r_ret_01_to_02"),
        "r_ret_01_to_03": lbl.get("r_ret_01_to_03"),
        "combiner_score": float(best["combiner_score"]),
        "cost_adjusted_objective": cao,
        "decision_label": decision,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Baseline vs tuned Layer 2 comparison table.")
    p.add_argument("--baseline-root", type=Path, required=True)
    p.add_argument("--out-md", type=Path, required=True)
    p.add_argument("--out-csv", type=Path, required=True)
    p.add_argument(
        "--tuned",
        action="append",
        default=[],
        metavar=("LABEL", "PATH"),
        nargs=2,
        help="Repeat: track label and result root (with top_unique + cost_stress).",
    )
    args = p.parse_args(argv)
    cwd = Path.cwd()
    baseline = args.baseline_root if args.baseline_root.is_absolute() else cwd / args.baseline_root
    rows: list[dict[str, Any]] = [_profile_from_root("original_global_l2_top_unique", baseline)]
    for label, path_s in args.tuned:
        r = Path(path_s)
        r = r if r.is_absolute() else cwd / r
        rows.append(_profile_from_root(label, r))
    df = pd.DataFrame(rows)
    out_md = args.out_md if args.out_md.is_absolute() else cwd / args.out_md
    out_csv = args.out_csv if args.out_csv.is_absolute() else cwd / args.out_csv
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    try:
        tbl = df.to_markdown(index=False)
    except Exception:
        tbl = df.to_string(index=False)
    out_md.write_text(
        "# Layer 2 tuned diagnostic comparison\n\n"
        + "Best **combiner_score** row per result root (post-dedupe `top_unique`).\n\n"
        + tbl
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out_md} and {out_csv}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
