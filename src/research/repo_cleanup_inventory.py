"""
Build repo_cleanup_inventory.csv / .md and optional delete plan + test audit.

Usage (from repo root):
  python src/research/repo_cleanup_inventory.py
  python src/research/repo_cleanup_inventory.py --test-audit-only
"""

from __future__ import annotations

import argparse
import ast
import csv
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "src" / "research" / "results"

# Scan zones (relative to repo root)
SCAN_ZONES = [
    "src/research/results",
    "src/combiner/results",
    "src/combiner/configs",
    "src/strategies/testing_parameters",
    "src/strategies/testing_parameters_results",
    "tests",
    "docs",
]

ROOT_DOC_FILES = [
    "README.md",
    "PROJECT_STATUS.md",
    "PROGRESS.md",
    "CHANGES.md",
    "NEXT_HANDOFF.md",
]

# Large trees: one row per immediate child only
AGGREGATE_TOP_LEVEL = frozenset(
    {"src/research/results", "src/combiner/results", "src/strategies/testing_parameters_results"}
)

# Paths that must never be recommended for deletion by this script
HARD_KEEP_PREFIXES = (
    "src/features/",
    "src/strategies/strategy/",
    "src/strategies/common/",
    "src/strategies/testing_parameters/",
    "src/backtest/",
    "src/combiner/",
    "src/data/",
    "src/utils/",
    "src/walkforward/",
    "tests/",
    "requirements.txt",
    "pytest.ini",
)

ACTIVE_RESEARCH_KEEP = (
    "src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v3",
    "src/research/results/pa_batch_bc_candidate_signal_diversity_repaired_v3",
    "src/research/results/pa_batch_bc_raw_signal_diversity_v3",
    "src/combiner/results/layer2_qqq_pa_batch_bc_repaired_v3_2023_2024",
)

LOW_RISK_DELETE_PREFIXES = (
    "src/research/results/layer1_all10_qqq_2020_20260430_v1",
    "src/research/results/layer1_all10_qqq_v1",
    "src/combiner/results/layer2_qqq_2020_20260430_v2_relaxed",
    "src/combiner/results/layer2_qqq_v1",
)


def _is_low_risk_delete_path(rel: str) -> bool:
    r = rel.replace("\\", "/")
    if r == "src/strategies/testing_parameters_results" or r.startswith(
        "src/strategies/testing_parameters_results/"
    ):
        return True
    for p in LOW_RISK_DELETE_PREFIXES:
        if r == p or r.startswith(p + "/"):
            return True
    return False


def _run_git_ls_files() -> set[str]:
    r = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return {line.strip().replace("\\", "/") for line in r.stdout.splitlines() if line.strip()}


def _load_index_blob() -> str:
    parts = []
    for rel in (
        "src/research/results/RESULTS_INDEX.md",
        "src/combiner/results/RESULTS_INDEX.md",
        "src/combiner/configs/CONFIG_INDEX.md",
    ):
        p = REPO_ROOT / rel
        if p.is_file():
            parts.append(p.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def _subtree_flags(root: Path) -> dict[str, bool]:
    has_sel = False
    has_pre = False
    has_stale = False
    has_summary = False
    total = 0
    if not root.exists():
        return {
            "has_selected_candidates": False,
            "has_pre_hardening_stale": False,
            "has_stale_md": False,
            "has_summary_artifact": False,
            "file_count": 0,
        }
    for dirpath, dirnames, filenames in os.walk(root):
        lp = dirpath.replace("\\", "/").lower()
        if "selected_candidates" in lp:
            has_sel = True
        for fn in filenames:
            total += 1
            fl = fn.lower()
            if fn == "PRE_HARDENING_STALE.md":
                has_pre = True
            if fn == "STALE.md":
                has_stale = True
            if "summary" in fl and fl.endswith(".md"):
                has_summary = True
            if fn in ("candidate_summary.md", "summary.md", "RESULTS_INDEX.md"):
                has_summary = True
    return {
        "has_selected_candidates": has_sel,
        "has_pre_hardening_stale": has_pre,
        "has_stale_md": has_stale,
        "has_summary_artifact": has_summary,
        "file_count": total,
    }


def _dir_size_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for fn in filenames:
            fp = Path(dirpath) / fn
            try:
                total += fp.stat().st_size
            except OSError:
                pass
    return total


def _mtime_iso(path: Path) -> str:
    try:
        ts = path.stat().st_mtime
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except OSError:
        return ""


def _tracked_for_path(rel_posix: str, tracked: set[str]) -> str:
    rel = rel_posix.replace("\\", "/").strip("/")
    if not rel:
        return "no"
    if rel in tracked:
        return "yes"
    prefix = rel + "/"
    for t in tracked:
        if t.startswith(prefix) or t == rel:
            return "yes"
    return "no"


def _in_index(rel_posix: str, index_blob: str) -> str:
    key = rel_posix.replace("\\", "/")
    if key in index_blob or key.replace("src/", "") in index_blob:
        return "yes"
    # basename match for folder
    base = Path(key).name
    if base and base in index_blob:
        return "maybe"
    return "no"


def _recommend_row(
    rel: str,
    is_dir: bool,
    flags: dict,
    tracked: str,
    in_index: str,
) -> str:
    r = rel.replace("\\", "/")
    for keep in ACTIVE_RESEARCH_KEEP:
        if r == keep or r.startswith(keep + "/"):
            return "KEEP_ACTIVE"
    if r.startswith("tests/"):
        return "KEEP_TEST"
    if r.startswith("src/strategies/testing_parameters/") and r.endswith(".yaml"):
        return "KEEP_CONFIG"
    if r.startswith("src/combiner/configs/"):
        return "KEEP_CONFIG"
    if flags.get("has_pre_hardening_stale"):
        return "DELETE_STALE_RESULT"
    if flags.get("has_stale_md") and in_index in ("yes", "maybe"):
        return "DELETE_SUPERSEDED_RESULT"
    if flags.get("has_stale_md"):
        return "REVIEW_MANUAL"
    if r == "src/strategies/testing_parameters_results":
        return "DELETE_LOCAL_HEAVY"
    if r.startswith("src/research/results/") or r.startswith("src/combiner/results/"):
        if tracked == "no" and any(
            x in r for x in ("sweep_", "/top_runs", "/fixed_runs", "/run_")
        ):
            return "DELETE_LOCAL_HEAVY"
        return "REVIEW_MANUAL"
    if r in ROOT_DOC_FILES or r.startswith("docs/"):
        return "KEEP_ACTIVE"
    return "REVIEW_MANUAL"


def collect_inventory_rows(tracked: set[str], index_blob: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for zone in SCAN_ZONES:
        base = REPO_ROOT / zone.replace("/", os.sep)
        if not base.exists():
            rows.append(
                {
                    "path": zone,
                    "type": "missing",
                    "size_bytes": "0",
                    "tracked": "no",
                    "has_selected_candidates": "no",
                    "has_pre_hardening_stale": "no",
                    "has_stale_md": "no",
                    "has_summary_or_index_ref": "no",
                    "last_modified_utc": "",
                    "recommended_action": "ARCHIVE_OPTIONAL",
                }
            )
            continue
        rel_base = zone.replace("\\", "/")
        if rel_base in AGGREGATE_TOP_LEVEL:
            if rel_base == "src/strategies/testing_parameters_results":
                rel = rel_base
                child = base
                st = _subtree_flags(child)
                sz = _dir_size_bytes(child)
                tracked_y = _tracked_for_path(rel, tracked)
                idx = _in_index(rel, index_blob)
                has_sum = "yes" if st["has_summary_artifact"] else idx if idx != "no" else "no"
                if has_sum == "maybe":
                    has_sum = "yes"
                flag_dict = {
                    "has_selected_candidates": st["has_selected_candidates"],
                    "has_pre_hardening_stale": st["has_pre_hardening_stale"],
                    "has_stale_md": st["has_stale_md"],
                    "has_summary_artifact": st["has_summary_artifact"],
                }
                rows.append(
                    {
                        "path": rel,
                        "type": "dir",
                        "size_bytes": str(sz),
                        "tracked": tracked_y,
                        "has_selected_candidates": "yes" if st["has_selected_candidates"] else "no",
                        "has_pre_hardening_stale": "yes" if st["has_pre_hardening_stale"] else "no",
                        "has_stale_md": "yes" if st["has_stale_md"] else "no",
                        "has_summary_or_index_ref": has_sum,
                        "last_modified_utc": _mtime_iso(child),
                        "recommended_action": _recommend_row(
                            rel, True, flag_dict, tracked_y, idx
                        ),
                    }
                )
                continue
            for child in sorted(base.iterdir(), key=lambda p: p.name.lower()):
                rel = str(child.relative_to(REPO_ROOT)).replace("\\", "/")
                st = _subtree_flags(child)
                sz = _dir_size_bytes(child)
                tracked_y = _tracked_for_path(rel, tracked)
                idx = _in_index(rel, index_blob)
                has_sum = "yes" if st["has_summary_artifact"] else idx if idx != "no" else "no"
                if has_sum == "maybe":
                    has_sum = "yes"
                flag_dict = {
                    "has_selected_candidates": st["has_selected_candidates"],
                    "has_pre_hardening_stale": st["has_pre_hardening_stale"],
                    "has_stale_md": st["has_stale_md"],
                    "has_summary_artifact": st["has_summary_artifact"],
                }
                rows.append(
                    {
                        "path": rel,
                        "type": "dir" if child.is_dir() else "file",
                        "size_bytes": str(sz),
                        "tracked": tracked_y,
                        "has_selected_candidates": "yes" if st["has_selected_candidates"] else "no",
                        "has_pre_hardening_stale": "yes" if st["has_pre_hardening_stale"] else "no",
                        "has_stale_md": "yes" if st["has_stale_md"] else "no",
                        "has_summary_or_index_ref": has_sum,
                        "last_modified_utc": _mtime_iso(child),
                        "recommended_action": _recommend_row(
                            rel, child.is_dir(), flag_dict, tracked_y, idx
                        ),
                    }
                )
            continue
        for dirpath, _, filenames in os.walk(base):
            dp = Path(dirpath)
            for fn in sorted(filenames):
                fp = dp / fn
                rel = str(fp.relative_to(REPO_ROOT)).replace("\\", "/")
                try:
                    sz = fp.stat().st_size
                    mtime = _mtime_iso(fp)
                except OSError:
                    sz = 0
                    mtime = ""
                tracked_y = "yes" if rel in tracked else "no"
                st = {
                    "has_selected_candidates": "yes" if "selected_candidates" in rel else "no",
                    "has_pre_hardening_stale": "yes" if fn == "PRE_HARDENING_STALE.md" else "no",
                    "has_stale_md": "yes" if fn == "STALE.md" else "no",
                    "has_summary_artifact": "yes"
                    if ("summary" in fn.lower() and fn.endswith(".md"))
                    or fn
                    in ("candidate_summary.md", "summary.md")
                    else "no",
                }
                idx = _in_index(rel, index_blob)
                has_sum = (
                    "yes"
                    if st["has_summary_artifact"] == "yes"
                    else (idx if idx != "no" else "no")
                )
                rows.append(
                    {
                        "path": rel,
                        "type": "file",
                        "size_bytes": str(sz),
                        "tracked": tracked_y,
                        "has_selected_candidates": st["has_selected_candidates"],
                        "has_pre_hardening_stale": st["has_pre_hardening_stale"],
                        "has_stale_md": st["has_stale_md"],
                        "has_summary_or_index_ref": has_sum,
                        "last_modified_utc": mtime,
                        "recommended_action": _recommend_row(
                            rel,
                            False,
                            {
                                "has_selected_candidates": st["has_selected_candidates"] == "yes",
                                "has_pre_hardening_stale": st["has_pre_hardening_stale"] == "yes",
                                "has_stale_md": st["has_stale_md"] == "yes",
                                "has_summary_artifact": st["has_summary_artifact"] == "yes",
                            },
                            tracked_y,
                            idx,
                        ),
                    }
                )

    for fn in ROOT_DOC_FILES:
        fp = REPO_ROOT / fn
        if not fp.is_file():
            continue
        rel = fn.replace("\\", "/")
        rows.append(
            {
                "path": rel,
                "type": "file",
                "size_bytes": str(fp.stat().st_size),
                "tracked": "yes" if rel in tracked else "no",
                "has_selected_candidates": "no",
                "has_pre_hardening_stale": "no",
                "has_stale_md": "no",
                "has_summary_or_index_ref": "yes",
                "last_modified_utc": _mtime_iso(fp),
                "recommended_action": "KEEP_ACTIVE",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def write_inventory_md(csv_path: Path, md_path: Path, generated_utc: str) -> None:
    lines = [
        "# Repo cleanup inventory",
        "",
        f"Generated **{generated_utc}** (run `python src/research/repo_cleanup_inventory.py`).",
        "",
        "See `repo_cleanup_inventory.csv` for machine-readable rows. Large result trees are **one row per top-level child** under `src/research/results/` and `src/combiner/results/`.",
        "",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_delete_plan(rows: list[dict[str, str]], tracked: set[str]) -> list[dict[str, str]]:
    plan: list[dict[str, str]] = []
    for row in rows:
        rel = row["path"].replace("\\", "/")
        action = row["recommended_action"]
        tracked_y = row["tracked"]
        if action not in ("DELETE_STALE_RESULT", "DELETE_SUPERSEDED_RESULT", "DELETE_LOCAL_HEAVY"):
            continue
        if not _is_low_risk_delete_path(rel):
            continue
        replacement = ""
        if "layer1_all10_qqq_2020_20260430_v1" in rel:
            replacement = "src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1/"
        elif "layer1_all10_qqq_v1" in rel:
            replacement = "src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1/ ; layer1_all10_qqq_2025_20260430_posthardening_v1/"
        elif "layer2_qqq_2020_20260430_v2_relaxed" in rel:
            replacement = "src/combiner/results/layer2_qqq_2023_20260430_posthardening_strict_v1/ (see RESULTS_INDEX.md)"
        elif "layer2_qqq_v1" in rel:
            replacement = "post-hardening Layer 2 roots (RESULTS_INDEX.md)"
        elif rel == "src/strategies/testing_parameters_results":
            replacement = "recreated by Layer 1 sweeps (see ARTIFACT_POLICY.md)"
        method = "git_rm" if tracked_y == "yes" else "local_delete"
        if rel == "src/strategies/testing_parameters_results":
            method = "local_delete"
        risk = "LOW"
        reason = action
        if row.get("has_pre_hardening_stale") == "yes":
            reason = "PRE_HARDENING_STALE.md; superseded by post-hardening roots"
        elif row.get("has_stale_md") == "yes":
            reason = "STALE.md + replacement documented in RESULTS_INDEX.md"
        elif action == "DELETE_LOCAL_HEAVY":
            reason = (
                "Layer 1 sweep scratch outputs under testing_parameters_results/"
                if rel == "src/strategies/testing_parameters_results"
                else "local / untracked heavy artifact under policy"
            )
        plan.append(
            {
                "path": rel,
                "tracked": tracked_y,
                "delete_method": method,
                "reason": reason,
                "replacement_path": replacement,
                "risk_level": risk,
            }
        )
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for p in plan:
        if p["path"] in seen:
            continue
        seen.add(p["path"])
        out.append(p)
    return out


def write_delete_plan_md(plan: list[dict[str, str]], md_path: Path, generated_utc: str) -> None:
    lines = [
        "# Repo cleanup delete plan (LOW risk only)",
        "",
        f"Generated **{generated_utc}**. Medium/high-risk rows are **not** listed here.",
        "",
        "| path | tracked | delete_method | risk | replacement | reason |",
        "|------|---------|-----------------|------|---------------|--------|",
    ]
    for p in plan:
        lines.append(
            f"| `{p['path']}` | {p['tracked']} | {p['delete_method']} | {p['risk_level']} | {p.get('replacement_path','')} | {p['reason']} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _src_package_exists(module: str) -> bool:
    """Return True if `module` (e.g. src.features.feature_key) resolves to a file or package."""
    if not module.startswith("src."):
        return True
    rel = Path(*module.split("."))
    base = REPO_ROOT / rel
    if base.with_suffix(".py").is_file():
        return True
    if (base / "__init__.py").is_file():
        return True
    if base.is_dir() and any(base.glob("*.py")):
        return True
    cur = base.parent
    for _ in range(24):
        if cur == REPO_ROOT or not str(cur).startswith(str(REPO_ROOT)):
            break
        if (cur / "__init__.py").is_file():
            return True
        if cur.with_suffix(".py").is_file():
            return True
        cur = cur.parent
    return False


def _test_imports_current(test_path: Path) -> tuple[str, list[str]]:
    """Parse test file; verify only `src.*` import targets exist."""
    try:
        src = test_path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(test_path))
    except SyntaxError:
        return "parse_error", []
    missing: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module
            if mod and mod.startswith("src.") and not _src_package_exists(mod):
                missing.append(mod)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                m = alias.name
                if m.startswith("src.") and not _src_package_exists(m):
                    missing.append(m)
    if missing:
        return "no", sorted(set(missing))
    return "yes", []


def _test_category(path: Path) -> str:
    name = path.name.lower()
    parts = str(path).lower()
    if "lookahead" in name or "no_lookahead" in parts:
        return "feature_no_lookahead"
    if "parity" in name or "fast_parity" in name:
        return "parity"
    if "combiner" in parts:
        return "combiner"
    if "candidate" in parts or "select" in parts:
        return "candidate_selection"
    if "artifact" in parts:
        return "artifact_policy"
    if "obsolete" in parts:
        return "obsolete_candidate"
    return "correctness"


def run_test_audit() -> list[dict[str, str]]:
    tests_dir = REPO_ROOT / "tests"
    rows: list[dict[str, str]] = []
    for fp in sorted(tests_dir.rglob("test_*.py")):
        rel = str(fp.relative_to(REPO_ROOT)).replace("\\", "/")
        ok, miss = _test_imports_current(fp)
        cat = _test_category(fp)
        rec = "KEEP"
        if ok == "parse_error":
            rec = "REVIEW"
        elif ok == "no" and miss:
            rec = "REVIEW"
        rows.append(
            {
                "path": rel,
                "imports_current_modules": ok,
                "missing_src_modules": ";".join(miss),
                "category": cat,
                "recommendation": rec,
            }
        )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-audit-only", action="store_true")
    args = ap.parse_args()
    generated = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if args.test_audit_only:
        rows = run_test_audit()
        write_csv(OUT_DIR / "test_suite_cleanup_audit.csv", rows)
        lines = [
            "# Test suite cleanup audit",
            "",
            f"Generated **{generated}**. No tests were deleted.",
            "",
            "| path | imports_ok | category | recommendation |",
            "|------|------------|----------|----------------|",
        ]
        for r in rows:
            lines.append(
                f"| `{r['path']}` | {r['imports_current_modules']} | {r['category']} | {r['recommendation']} |"
            )
        (OUT_DIR / "test_suite_cleanup_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote {OUT_DIR / 'test_suite_cleanup_audit.csv'}")
        return 0

    tracked = _run_git_ls_files()
    index_blob = _load_index_blob()
    rows = collect_inventory_rows(tracked, index_blob)
    write_csv(OUT_DIR / "repo_cleanup_inventory.csv", rows)
    write_inventory_md(OUT_DIR / "repo_cleanup_inventory.csv", OUT_DIR / "repo_cleanup_inventory.md", generated)
    print(f"Wrote {OUT_DIR / 'repo_cleanup_inventory.csv'} ({len(rows)} rows)")

    plan = build_delete_plan(rows, tracked)
    write_csv(OUT_DIR / "repo_cleanup_delete_plan.csv", plan)
    write_delete_plan_md(plan, OUT_DIR / "repo_cleanup_delete_plan.md", generated)
    print(f"Wrote delete plan ({len(plan)} LOW-risk rows)")

    audit = run_test_audit()
    write_csv(OUT_DIR / "test_suite_cleanup_audit.csv", audit)
    lines = [
        "# Test suite cleanup audit",
        "",
        f"Generated **{generated}**. No tests were deleted.",
        "",
        "| path | imports_ok | category | recommendation |",
        "|------|------------|----------|----------------|",
    ]
    for r in audit:
        lines.append(
            f"| `{r['path']}` | {r['imports_current_modules']} | {r['category']} | {r['recommendation']} |"
        )
    (OUT_DIR / "test_suite_cleanup_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote test audit ({len(audit)} tests)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
