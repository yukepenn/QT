"""Post-selection helper: export diversified candidate YAMLs using diversity CSV."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_REQUIRED_DIV_COLS = (
    "candidate_id",
    "strategy",
    "pure_signal_hash",
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate-root", type=Path, required=True)
    p.add_argument("--diversity-csv", type=Path, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--top-per-strategy", type=int, default=5)
    p.add_argument("--min-unique-signal-hashes", type=int, default=2)
    args = p.parse_args(argv)

    root = args.candidate_root
    if not root.is_absolute():
        root = Path.cwd() / root
    div_path = args.diversity_csv
    if not div_path.is_absolute():
        div_path = Path.cwd() / div_path
    out_root = args.output_root
    if not out_root.is_absolute():
        out_root = Path.cwd() / out_root

    sel_in = root / "selected_candidates" if (root / "selected_candidates").is_dir() else root
    csv_in = root / "selected_candidates.csv"
    if not csv_in.is_file():
        print(f"ERROR missing {csv_in}", file=sys.stderr)
        return 2
    if not div_path.is_file():
        print(f"ERROR missing diversity csv {div_path}", file=sys.stderr)
        return 2

    div = pd.read_csv(div_path)
    for c in _REQUIRED_DIV_COLS:
        if c not in div.columns:
            print(f"ERROR diversity csv missing column {c!r}", file=sys.stderr)
            return 2

    div_small = div[["candidate_id", "strategy", "pure_signal_hash"]].copy()
    meta = pd.read_csv(csv_in)
    if "candidate_id" not in meta.columns or "strategy" not in meta.columns:
        print("ERROR selected_candidates.csv missing columns", file=sys.stderr)
        return 2

    merged = meta.merge(div_small, on=["candidate_id", "strategy"], how="left")

    out_sel = out_root / "selected_candidates"
    out_sel.mkdir(parents=True, exist_ok=True)
    dup_warn: list[str] = []
    written_rows: list[dict[str, Any]] = []

    top_k = int(args.top_per_strategy)
    min_u = int(args.min_unique_signal_hashes)

    for strat, g in merged.groupby("strategy"):
        g = g.copy()
        g["_sc"] = pd.to_numeric(g.get("candidate_score"), errors="coerce")
        g["_rn"] = pd.to_numeric(g.get("candidate_rank"), errors="coerce")
        g = g.sort_values(by=["_sc", "_rn"], ascending=[False, True], na_position="last")

        chosen_ids: list[str] = []
        seen_pure: set[str] = set()
        used_fill = False

        for _, row in g.iterrows():
            if len(chosen_ids) >= top_k:
                break
            cid = str(row["candidate_id"]).strip()
            ysrc = sel_in / f"{cid}.yaml"
            if not ysrc.is_file():
                dup_warn.append(f"missing_yaml {strat} {cid}")
                continue
            ph = str(row.get("pure_signal_hash", "") or "").strip()
            if ph and ph in seen_pure:
                continue
            if ph:
                seen_pure.add(ph)
            chosen_ids.append(cid)
            shutil.copy2(ysrc, out_sel / f"{cid}.yaml")
            written_rows.append(
                row.drop(labels=["_sc", "_rn"], errors="ignore").to_dict()
            )

        if len(chosen_ids) < top_k:
            for _, row in g.iterrows():
                if len(chosen_ids) >= top_k:
                    break
                cid = str(row["candidate_id"]).strip()
                if cid in chosen_ids:
                    continue
                ysrc = sel_in / f"{cid}.yaml"
                if not ysrc.is_file():
                    continue
                used_fill = True
                chosen_ids.append(cid)
                shutil.copy2(ysrc, out_sel / f"{cid}.yaml")
                written_rows.append(
                    row.drop(labels=["_sc", "_rn"], errors="ignore").to_dict()
                )

        if used_fill:
            dup_warn.append(
                f"{strat}: filled_remaining_slots_with_duplicate_or_lower_rank_rows"
            )

    out_csv = out_root / "selected_candidates.csv"
    pd.DataFrame(written_rows).to_csv(out_csv, index=False)

    summary_lines = [
        "# Diversity-aware candidate export",
        "",
        f"- **source_root:** `{root.as_posix()}`",
        f"- **diversity_csv:** `{div_path.as_posix()}`",
        f"- **top_per_strategy:** {top_k}",
        f"- **min_unique_signal_hashes (first-pass preference):** {min_u}",
        f"- **rows_written:** {len(written_rows)}",
        "",
    ]
    if dup_warn:
        summary_lines.append("## Warnings")
        for w in dup_warn:
            summary_lines.append(f"- {w}")
    (out_root / "diversity_selection_summary.md").write_text(
        "\n".join(summary_lines) + "\n", encoding="utf-8"
    )

    warn_path = out_root / "duplicate_fill_warning.txt"
    if dup_warn:
        warn_path.write_text(json.dumps(dup_warn, indent=2) + "\n", encoding="utf-8")
    elif warn_path.exists():
        warn_path.unlink()

    print(f"Wrote {out_csv} ({len(written_rows)} rows)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
