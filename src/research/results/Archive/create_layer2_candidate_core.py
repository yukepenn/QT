"""
Build a Layer-2-ready strict candidate subset from Global Layer 1 output.

Caps total candidates, prefers unique pure_signal_hash per strategy, and
attempts to retain at least one candidate per strategy_family before trimming.
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _layer1_paths(candidate_root: Path) -> tuple[Path, Path]:
    root = candidate_root
    if not root.is_absolute():
        root = Path.cwd() / root
    csv_path = root / "selected_candidates.csv"
    sel_dir = root / "selected_candidates"
    if not csv_path.is_file():
        raise FileNotFoundError(f"missing {csv_path}")
    if not sel_dir.is_dir():
        raise FileNotFoundError(f"missing {sel_dir}")
    return csv_path, sel_dir


def _per_strategy_pick(
    sub: pd.DataFrame,
    *,
    max_per_strategy: int,
    prefer_unique: bool,
    dup_notes: list[str],
) -> list[str]:
    """Return up to max_per_strategy candidate_ids; prefer distinct pure_signal_hash first."""
    if sub.empty:
        return []
    work = sub.copy()
    work["_score"] = pd.to_numeric(work.get("candidate_score"), errors="coerce").fillna(-1e9)
    work["_rank"] = pd.to_numeric(work.get("candidate_rank"), errors="coerce").fillna(999)
    work = work.sort_values(["_score", "_rank"], ascending=[False, True])
    picked: list[str] = []
    if not prefer_unique:
        for _, r in work.iterrows():
            if len(picked) >= max_per_strategy:
                break
            cid = str(r.get("candidate_id", "")).strip()
            if cid:
                picked.append(cid)
        return picked
    seen_hash: set[str] = set()
    for _, r in work.iterrows():
        if len(picked) >= max_per_strategy:
            break
        cid = str(r.get("candidate_id", "")).strip()
        if not cid:
            continue
        h = str(r.get("pure_signal_hash", "") or "").strip()
        if h and h in seen_hash:
            continue
        picked.append(cid)
        if h:
            seen_hash.add(h)
    if len(picked) < max_per_strategy:
        for _, r in work.iterrows():
            if len(picked) >= max_per_strategy:
                break
            cid = str(r.get("candidate_id", "")).strip()
            if not cid or cid in picked:
                continue
            h = str(r.get("pure_signal_hash", "") or "").strip()
            if h and h in seen_hash:
                dup_notes.append(f"{cid}:duplicate_pure_hash_fill:{h[:12]}")
            picked.append(cid)
            if h:
                seen_hash.add(h)
    return picked


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate-root", type=Path, required=True)
    ap.add_argument("--diversity-root", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    ap.add_argument("--max-total-candidates", type=int, default=80)
    ap.add_argument("--max-per-strategy", type=int, default=4)
    ap.add_argument(
        "--prefer-unique-pure-signal-hash",
        dest="prefer_unique",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Prefer distinct pure_signal_hash before allowing duplicates (default: true).",
    )
    ap.add_argument(
        "--preserve-family-coverage",
        dest="preserve_family",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Try to retain at least one candidate per strategy_family before global fill.",
    )
    args = ap.parse_args(argv)

    src_csv, src_dir = _layer1_paths(args.candidate_root)
    div_root = args.diversity_root
    if not div_root.is_absolute():
        div_root = Path.cwd() / div_root
    div_csv = div_root / "candidate_signal_diversity.csv"
    if not div_csv.is_file():
        print(f"ERROR missing diversity {div_csv}", file=sys.stderr)
        return 2

    out_root = args.output_root
    if not out_root.is_absolute():
        out_root = Path.cwd() / out_root
    out_sel = out_root / "selected_candidates"
    out_sel.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(src_csv)
    if "filters_used" not in df.columns:
        print("ERROR selected_candidates.csv missing filters_used", file=sys.stderr)
        return 2
    strict_mask = df["filters_used"].astype(str).str.strip().str.lower() == "strict"
    strict_df = df.loc[strict_mask].copy()
    if strict_df.empty:
        print("ERROR no strict rows in selected_candidates.csv", file=sys.stderr)
        return 2

    div = pd.read_csv(div_csv)
    if "candidate_id" not in div.columns:
        print("ERROR diversity CSV missing candidate_id", file=sys.stderr)
        return 2
    div_small = div[["candidate_id"] + [c for c in ("pure_signal_hash",) if c in div.columns]].copy()
    merged = strict_df.merge(div_small, on="candidate_id", how="left")

    dup_notes: list[str] = []
    per_strat: dict[str, list[str]] = {}
    for strat, grp in merged.groupby("strategy", sort=False):
        per_strat[str(strat)] = _per_strategy_pick(
            grp,
            max_per_strategy=args.max_per_strategy,
            prefer_unique=bool(args.prefer_unique),
            dup_notes=dup_notes,
        )

    pool_rows: list[dict[str, Any]] = []
    for cid_list in per_strat.values():
        for cid in cid_list:
            row = merged.loc[merged["candidate_id"] == cid].iloc[0].to_dict()
            pool_rows.append(row)

    pool = pd.DataFrame(pool_rows)
    pool["_score"] = pd.to_numeric(pool.get("candidate_score"), errors="coerce").fillna(-1e9)
    pool["_fam"] = pool.get("strategy_family", pool["strategy"]).astype(str)

    selected_ids: list[str] = []
    per_s_count: dict[str, int] = defaultdict(int)
    fam_has: set[str] = set()

    def try_add(cid: str, fam: str, strat: str) -> bool:
        if cid in selected_ids:
            return False
        if len(selected_ids) >= args.max_total_candidates:
            return False
        if per_s_count[strat] >= args.max_per_strategy:
            return False
        selected_ids.append(cid)
        per_s_count[strat] += 1
        fam_has.add(fam)
        return True

    if args.preserve_family:
        fams = sorted({str(x) for x in pool["_fam"].unique() if str(x).strip()})
        for fam in fams:
            if len(selected_ids) >= args.max_total_candidates:
                break
            sub = pool[pool["_fam"] == fam].sort_values("_score", ascending=False)
            for _, r in sub.iterrows():
                if try_add(str(r["candidate_id"]), fam, str(r["strategy"])):
                    break

    pool_sorted = pool.sort_values("_score", ascending=False, kind="mergesort")
    for _, r in pool_sorted.iterrows():
        if len(selected_ids) >= args.max_total_candidates:
            break
        try_add(str(r["candidate_id"]), str(r["_fam"]), str(r["strategy"]))

    selected_set = set(selected_ids)
    sel_rows = []
    for cid in selected_ids:
        hit = merged.loc[merged["candidate_id"].astype(str) == cid]
        if hit.empty:
            print(f"ERROR missing merged row for {cid}", file=sys.stderr)
            return 2
        sel_rows.append(hit.iloc[0].to_dict())
    out_df = pd.DataFrame(sel_rows)

    for _, r in out_df.iterrows():
        cid = str(r["candidate_id"])
        src_y = src_dir / f"{cid}.yaml"
        if not src_y.is_file():
            print(f"ERROR missing yaml {src_y}", file=sys.stderr)
            return 2
        shutil.copy2(src_y, out_sel / f"{cid}.yaml")

    out_df = out_df.drop(columns=[c for c in out_df.columns if c.startswith("_")], errors="ignore")
    out_df["config_yaml"] = out_df["candidate_id"].map(lambda c: f"selected_candidates/{c}.yaml")
    out_csv = out_root / "selected_candidates.csv"
    out_df.to_csv(out_csv, index=False)

    all_strict_ids = set(strict_df["candidate_id"].astype(str))
    dropped = sorted(all_strict_ids - selected_set)
    drop_path = out_root / "l2_core_dropped_candidates.csv"
    with drop_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["candidate_id", "reason"])
        w.writeheader()
        for cid in dropped:
            w.writerow({"candidate_id": cid, "reason": "not_selected_in_l2_core_cap"})

    fam_g = (
        out_df.groupby("strategy_family", dropna=False)
        .size()
        .reset_index(name="n_candidates")
        .sort_values("n_candidates", ascending=False)
    )
    fam_path = out_root / "l2_core_family_summary.csv"
    fam_g.to_csv(fam_path, index=False)

    warn_path = out_root / "duplicate_fill_warning.txt"
    if dup_notes:
        warn_path.write_text("\n".join(dup_notes) + "\n", encoding="utf-8")
    else:
        warn_path.write_text("(none)\n", encoding="utf-8")

    summary_lines = [
        "# Layer 2 core candidate selection",
        "",
        f"- source: `{src_csv}`",
        f"- diversity: `{div_csv}`",
        f"- max_total: **{args.max_total_candidates}**",
        f"- max_per_strategy: **{args.max_per_strategy}**",
        f"- selected: **{len(selected_ids)}**",
        f"- families: **{out_df['strategy_family'].nunique() if 'strategy_family' in out_df.columns else 0}**",
        "",
        "Strict-only rows from `selected_candidates.csv` were considered.",
    ]
    (out_root / "l2_core_selection_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_csv} ({len(selected_ids)} rows)", flush=True)
    print(f"YAMLs -> {out_sel}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
