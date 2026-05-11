from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class ValidationResult:
    rel_path: str
    ok: bool
    rows: int
    cols: int
    error: str
    abs_path_hit: str
    missing_required_columns: str


ABS_PATH_TOKENS = ("D:/", "C:/", "OneDrive", "\\OneDrive")


REQUIRED_COLUMNS: dict[str, list[str]] = {
    "representative_candidate_manifest.csv": [
        "candidate_id",
        "representative_role",
        "include_in_primary_core",
        "include_in_balanced_core",
        "source_yaml_path",
    ],
    "candidate_sets_design.csv": [
        "candidate_set",
        "candidate_id",
        "source_yaml_path",
        "run_recommended",
        "design_only",
    ],
    "core_watchlist_drop_actions.csv": [
        "candidate_id",
        "action",
        "family",
        "source_label",
        "robust_label",
    ],
    "effective_signal_clusters.csv": [
        "cluster_id",
        "cluster_kind",
        "members",
        "raw_cluster_representative",
        "design_representative",
    ],
    "robust_candidate_dedupe_table.csv": [
        "candidate_id",
        "audit_family",
        "cluster_id",
    ],
}


def _abs_path_hit(df: pd.DataFrame) -> str:
    # Convert to strings once; keep it cheap-ish for these small curated CSVs.
    s = df.astype(str).to_string()
    for tok in ABS_PATH_TOKENS:
        if tok in s:
            return tok
    return ""


def _missing_required_columns(filename: str, cols: list[str]) -> list[str]:
    required = REQUIRED_COLUMNS.get(filename)
    if not required:
        return []
    present = set(cols)
    return [c for c in required if c not in present]


def validate_root(root: Path, *, csv_only: bool = True) -> list[ValidationResult]:
    return validate_root_with_excludes(root, csv_only=csv_only, exclude_subdirs=())


def validate_root_with_excludes(
    root: Path,
    *,
    csv_only: bool = True,
    exclude_subdirs: tuple[str, ...] = (),
    exclude_filenames: tuple[str, ...] = (),
) -> list[ValidationResult]:
    patterns = ["*.csv"] if csv_only else ["*.csv", "*.tsv"]
    files: list[Path] = []
    excl = {str(x).strip().strip("/").strip("\\") for x in exclude_subdirs if str(x).strip()}
    excl_files = {str(x).strip() for x in exclude_filenames if str(x).strip()}
    for pat in patterns:
        for p in root.rglob(pat):
            rel_parts = p.relative_to(root).parts
            if any(part in excl for part in rel_parts):
                continue
            if p.name in excl_files:
                continue
            files.append(p)
    files = sorted(files)

    out: list[ValidationResult] = []
    for p in files:
        rel = p.relative_to(root).as_posix()
        try:
            df = pd.read_csv(p)
            miss = _missing_required_columns(p.name, [str(c) for c in df.columns])
            out.append(
                ValidationResult(
                    rel_path=rel,
                    ok=True,
                    rows=int(len(df)),
                    cols=int(len(df.columns)),
                    error="",
                    abs_path_hit=_abs_path_hit(df),
                    missing_required_columns=",".join(miss),
                )
            )
        except Exception as e:  # noqa: BLE001 (tooling script)
            out.append(
                ValidationResult(
                    rel_path=rel,
                    ok=False,
                    rows=0,
                    cols=0,
                    error=repr(e),
                    abs_path_hit="",
                    missing_required_columns="",
                )
            )
    return out


def _write_md_summary(results: list[ValidationResult], md_path: Path) -> None:
    ok = [r for r in results if r.ok]
    bad = [r for r in results if not r.ok]
    abs_hits = [r for r in ok if r.abs_path_hit]
    missing_cols = [r for r in ok if r.missing_required_columns]

    lines: list[str] = []
    lines += ["# Research artifact validation", ""]
    lines += [f"- CSV files checked: **{len(results)}**"]
    lines += [f"- Parse failures: **{len(bad)}**"]
    lines += [f"- Absolute-path token hits: **{len(abs_hits)}**"]
    lines += [f"- Missing required columns: **{len(missing_cols)}**", ""]

    if bad:
        lines += ["## Parse failures", ""]
        for r in bad:
            lines += [f"- `{r.rel_path}`: `{r.error}`"]
        lines += [""]

    if abs_hits:
        lines += ["## Absolute-path hits (should be zero)", ""]
        for r in abs_hits:
            lines += [f"- `{r.rel_path}`: `{r.abs_path_hit}`"]
        lines += [""]

    if missing_cols:
        lines += ["## Missing required columns (should be zero)", ""]
        for r in missing_cols:
            lines += [f"- `{r.rel_path}`: `{r.missing_required_columns}`"]
        lines += [""]

    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate curated research artifact CSVs.")
    ap.add_argument("--root", required=True, help="Root directory to scan (e.g. src/research/results/robust_l2_core_v2_design)")
    ap.add_argument("--csv-only", action="store_true", help="Only validate *.csv files")
    ap.add_argument(
        "--exclude-subdirs",
        default="",
        help="Comma-separated subdir names to ignore (e.g. local_runs,local_configs)",
    )
    ap.add_argument(
        "--include-local-runs",
        action="store_true",
        help="Include local_runs/local_configs in scanning (default: excluded).",
    )
    ap.add_argument("--output", required=True, help="Output CSV path for results (under repo)")
    args = ap.parse_args(argv)

    root = Path(args.root)
    out_csv = Path(args.output)
    out_md = out_csv.with_suffix(".md")

    exclude = tuple([x.strip() for x in str(args.exclude_subdirs).split(",") if x.strip()])
    if not args.include_local_runs:
        # Safety: local_runs/local_configs can be huge and include local-only CSVs.
        # By default we validate curated root-level CSVs only.
        exclude = tuple(sorted(set(exclude) | {"local_runs", "local_configs"}))
    # Avoid the validation output file self-triggering absolute-path hits.
    results = validate_root_with_excludes(
        root,
        csv_only=bool(args.csv_only),
        exclude_subdirs=exclude,
        exclude_filenames=(out_csv.name,),
    )
    df = pd.DataFrame([r.__dict__ for r in results]).sort_values(["ok", "rel_path"], ascending=[True, True])
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False, lineterminator="\n")
    _write_md_summary(results, out_md)

    # Non-zero exit if any failure conditions exist.
    any_parse_fail = any(not r.ok for r in results)
    any_abs = any(r.ok and r.abs_path_hit for r in results)
    any_missing = any(r.ok and r.missing_required_columns for r in results)
    return 1 if (any_parse_fail or any_abs or any_missing) else 0


if __name__ == "__main__":
    raise SystemExit(main())

