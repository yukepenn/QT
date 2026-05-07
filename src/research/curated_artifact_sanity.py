from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Check:
    root: Path
    name: str
    ok: bool
    reason: str | None = None


def _exists(p: Path) -> bool:
    return p.is_file()


def _any_glob(p: Path, pattern: str) -> bool:
    return any(p.glob(pattern))


def build_checks() -> list[Check]:
    layer1_roots = [
        Path("src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1"),
        Path("src/research/results/layer1_all10_qqq_2025_20260430_posthardening_v1"),
    ]
    layer2_roots = [
        Path("src/combiner/results/layer2_qqq_2020_20260430_posthardening_strict_v1"),
        Path("src/combiner/results/layer2_qqq_2020_20260430_posthardening_relaxed_v1"),
        Path("src/combiner/results/layer2_qqq_2025_20260430_recent_check_v1"),
    ]

    checks: list[Check] = []

    for r in layer1_roots:
        checks.append(Check(r, "dir", r.is_dir()))
        checks.append(Check(r, "selected_candidates.csv", _exists(r / "selected_candidates.csv")))
        checks.append(Check(r, "selected_candidates/*.yaml", _any_glob(r / "selected_candidates", "*.yaml")))
        checks.append(Check(r, "sweep_manifest.csv", _exists(r / "sweep_manifest.csv")))
        # optional but nice-to-have
        if (r / "candidate_summary.md").exists():
            checks.append(Check(r, "candidate_summary.md", _exists(r / "candidate_summary.md")))

    for r in layer2_roots:
        d = r / "diagnostics"
        checks.append(Check(r, "dir", r.is_dir()))
        checks.append(Check(r, "top_unique_systems.csv", _exists(r / "top_unique_systems.csv")))
        checks.append(Check(r, "fixed_run_summary.csv", _exists(r / "fixed_run_summary.csv")))
        checks.append(Check(r, "cost_stress/cost_stress_summary.md", _exists(r / "cost_stress" / "cost_stress_summary.md")))
        checks.append(Check(r, "diagnostics/diagnostics_summary.md", _exists(d / "diagnostics_summary.md")))
        checks.append(Check(r, "diagnostics/candidate_signal_summary.csv", _exists(d / "candidate_signal_summary.csv")))
        checks.append(Check(r, "diagnostics/candidate_overlap_matrix.csv", _exists(d / "candidate_overlap_matrix.csv")))
        checks.append(Check(r, "diagnostics/candidate_conflict_summary.csv", _exists(d / "candidate_conflict_summary.csv")))

    return checks


def write_md(path: Path, checks: list[Check]) -> None:
    lines: list[str] = []
    lines.append("# Curated artifact sanity check")
    lines.append("")
    lines.append("Active roots only. Required items must be present.")
    lines.append("")

    any_missing = False
    for c in checks:
        status = "OK" if c.ok else "MISSING"
        if not c.ok:
            any_missing = True
        extra = f" — {c.reason}" if (c.reason and not c.ok) else ""
        lines.append(f"- `{c.root.as_posix()}` **{c.name}**: {status}{extra}")

    lines.append("")
    lines.append(f"Overall: **{'PASS' if not any_missing else 'FAIL'}**")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    checks = build_checks()
    write_md(Path("src/research/results/curated_artifact_sanity_check.md"), checks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

