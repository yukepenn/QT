"""Pivot cost_stress_results onto high-trade top_unique rows (generic, data-driven)."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def _pick_slip(df: pd.DataFrame, combo_id: int, slip: float) -> pd.Series | None:
    sub = df[np.isclose(df["source_combo_id"].astype(float), float(combo_id))]
    sub = sub[np.isclose(sub["slippage_per_share"].astype(float), float(slip))]
    if len(sub) == 0:
        return None
    return sub.iloc[0]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="High-trade Layer 2 cost review from postprocess outputs.")
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--min-trades", type=int, default=400)
    p.add_argument(
        "--cost-stress-csv",
        type=Path,
        default=None,
        help="Default: <output-root>/cost_stress/cost_stress_results.csv",
    )
    args = p.parse_args(argv)

    root = args.output_root
    if not root.is_absolute():
        root = Path.cwd() / root
    stress_path = args.cost_stress_csv or (root / "cost_stress" / "cost_stress_results.csv")
    top_path = root / "top_unique_systems.csv"
    if not top_path.exists():
        raise SystemExit(f"missing {top_path}")
    if not stress_path.exists():
        raise SystemExit(f"missing {stress_path} (run postprocess with --cost-stress-top > 0)")

    tu = pd.read_csv(top_path)
    cs = pd.read_csv(stress_path)
    if "trades" not in tu.columns:
        raise SystemExit("top_unique_systems.csv missing trades column")

    tu_ht = tu[tu["trades"].fillna(0).astype(float) >= float(args.min_trades)].copy()
    rows: list[dict[str, object]] = []
    for _, r in tu_ht.iterrows():
        cid = int(r["combo_id"])
        tag = f"uq{int(r.get('unique_rank', 0))}_combo{cid}_{r.get('candidate_set', '')}_tp{r.get('top_per_strategy', '')}"
        base = {
            "system_tag": tag,
            "candidate_set": r.get("candidate_set"),
            "top_per_strategy": r.get("top_per_strategy"),
            "trades": r.get("trades"),
        }
        notes: list[str] = []
        for slip, suffix in [(0.01, "0_01"), (0.02, "0_02"), (0.03, "0_03")]:
            row = _pick_slip(cs, cid, slip)
            if row is None:
                notes.append(f"missing slip {slip} for combo_id {cid}")
                base[f"total_r_{suffix}"] = float("nan")
                base[f"pf_{suffix}"] = float("nan")
                base[f"maxdd_{suffix}"] = float("nan")
            else:
                base[f"total_r_{suffix}"] = row.get("total_r")
                base[f"pf_{suffix}"] = row.get("profit_factor")
                base[f"maxdd_{suffix}"] = row.get("max_drawdown_r")
        base["notes"] = "; ".join(notes) if notes else ""
        rows.append(base)

    out = pd.DataFrame(rows)
    root.mkdir(parents=True, exist_ok=True)
    out_csv = root / "high_trade_cost_review.csv"
    out.to_csv(out_csv, index=False)
    md = [
        "# High-trade cost review",
        "",
        f"- Source: `{top_path}` × `{stress_path}`",
        f"- Filter: trades >= **{args.min_trades}** → **{len(out)}** systems",
        "",
    ]
    try:
        md.append(out.head(40).to_markdown(index=False))
    except Exception:
        md.append(out.head(40).to_string(index=False))
    md.append("")
    (root / "high_trade_cost_review.md").write_text("\n".join(md), encoding="utf-8")
    print(f"wrote {out_csv} and high_trade_cost_review.md ({len(out)} rows)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
