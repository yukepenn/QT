"""Validate curated research artifacts (CSV-only scan, no secrets)."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Scan research CSVs for obvious hygiene issues.")
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--csv-only", action="store_true")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)
    root = args.root.resolve()
    rows: list[dict[str, str]] = []
    abs_pat = re.compile(r"[A-Za-z]:\\\\|/Users/|\\\\Users\\\\")
    for path in sorted(root.rglob("*.csv")):
        rel = str(path.relative_to(root))
        issues: list[str] = []
        try:
            with path.open(encoding="utf-8", newline="") as f:
                head = f.read(8000)
            if abs_pat.search(head):
                issues.append("possible_abs_path")
        except OSError as e:
            issues.append(str(e))
        rows.append({"path": rel, "status": "FAIL" if issues else "OK", "notes": ";".join(issues)})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["path", "status", "notes"])
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {args.output} rows={len(rows)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
