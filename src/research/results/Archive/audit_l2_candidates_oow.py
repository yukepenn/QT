"""
Per-candidate Layer2 combiner OOW audit (research-only).

Does not edit candidate YAMLs or optimize on OOW. Default: no signal cache.
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.research.audit_l2_candidates_oow_lib import (
    collect_long_metrics_frame,
    discover_singleton_runs,
    family_label_counts,
    filter_by_families,
    fixed_profile_strategy_candidates,
    iter_candidate_metas,
    labels_table_from_wide,
    merge_metrics_for_labels,
    strategy_label_counts,
)
from src.research.audit_l2_candidates_oow_report import (
    write_candidate_oow_summary_md,
    write_compact_highlights,
    write_family_interpretation,
    write_full_candidate_interpretation,
    write_policy_action_summary,
    write_robust_core_dry_run,
    write_side_flip_watchlist,
)
from src.research.fixed_profile_oow import cmd_inspect_data as fixed_cmd_inspect_data
from src.research.fixed_profile_oow_lib import load_window_bounds


def _parse_csv_ids(s: str | None) -> list[str]:
    if not s or not str(s).strip():
        return []
    return [x.strip() for x in str(s).split(",") if x.strip()]


def _parse_windows(s: str) -> list[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def _default_combiner_config(repo_root: Path) -> Path:
    return repo_root / "src/research/results/fixed_profile_oow_v1/configs/layer2_fixed_vwap_mtp2.yaml"


def _fixed_profile_config_map(repo_root: Path) -> dict[str, Path]:
    base = repo_root / "src/research/results/fixed_profile_oow_v1/configs"
    return {
        "vwap_mtp2": base / "layer2_fixed_vwap_mtp2.yaml",
        "vwap_mtp1": base / "layer2_fixed_vwap_mtp1.yaml",
        "indicator_mtp1": base / "layer2_fixed_indicator_mtp1.yaml",
        "indicator_mtp2": base / "layer2_fixed_indicator_mtp2.yaml",
        "indicator_mtp3": base / "layer2_fixed_indicator_mtp3.yaml",
    }


def _combiner_singleton_argv(
    *,
    python_exe: str,
    candidate_root: Path,
    combiner_config: Path,
    candidate_id: str,
    start: str,
    end: str,
    out_window_root: Path,
    data_dir: str,
    use_signal_cache: bool,
    tag: str,
) -> list[str]:
    argv: list[str] = [
        python_exe,
        "-m",
        "src.combiner.run",
        "--candidate-root",
        str(candidate_root),
        "--config",
        str(combiner_config),
        "--asset",
        "equity",
        "--symbol",
        "QQQ",
        "--start",
        start,
        "--end",
        end,
        "--candidate-ids",
        candidate_id,
        "--output-root",
        str(out_window_root),
        "--tag",
        tag,
        "--top-per-strategy",
        "999",
        "--data-dir",
        data_dir,
        "--no-detailed",
    ]
    if use_signal_cache:
        argv.append("--use-signal-cache")
    return argv


def _latest_run_dir(window_dir: Path) -> Path | None:
    runs = sorted(window_dir.glob("run_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[0] if runs else None


def _run_has_metrics(run_dir: Path) -> bool:
    return (run_dir / "metrics.json").is_file()


def cmd_print_commands(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Print example combiner lines for l2 candidate audit.")
    p.add_argument("--candidate-root", required=True)
    p.add_argument("--combiner-config", default=None)
    p.add_argument("--windows-root", default="src/research/results/fixed_profile_oow_v1")
    p.add_argument("--windows", default="early_oow,insample_ref,late_oow")
    p.add_argument("--candidate-id", default="VWAP_RECLAIM_REJECT_001")
    p.add_argument("--data-dir", default="data/raw/ibkr")
    args = p.parse_args(argv)
    cwd = Path.cwd()
    repo = _ROOT
    cr = Path(args.candidate_root)
    if not cr.is_absolute():
        cr = cwd / cr
    wr = Path(args.windows_root)
    if not wr.is_absolute():
        wr = cwd / wr
    cfg = Path(args.combiner_config) if args.combiner_config else _default_combiner_config(repo)
    if not cfg.is_absolute():
        cfg = cwd / cfg
    bounds = load_window_bounds(wr, data_dir=args.data_dir)
    seg = __import__("src.research.audit_l2_candidates_oow_lib", fromlist=["safe_run_segment"]).safe_run_segment(
        args.candidate_id
    )
    for wid in _parse_windows(args.windows):
        if wid not in bounds:
            print(f"# skip unknown window {wid}", file=sys.stderr)
            continue
        st, en = bounds[wid]
        out_root = cwd / "src/research/results/layer2_candidate_robustness_v1/local_runs" / seg / wid
        line = _combiner_singleton_argv(
            python_exe=sys.executable,
            candidate_root=cr,
            combiner_config=cfg,
            candidate_id=args.candidate_id,
            start=st,
            end=en,
            out_window_root=out_root,
            data_dir=args.data_dir,
            use_signal_cache=False,
            tag="l2_candidate_audit",
        )
        print(" ".join(line))
    return 0


def cmd_inventory(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Write remaining_candidate_inventory.* and extended_audit_inventory.md.")
    p.add_argument("--candidate-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--windows-root", default="src/research/results/fixed_profile_oow_v1")
    p.add_argument("--windows", default="early_oow,insample_ref,late_oow")
    p.add_argument("--families", default=None, help="Comma-separated audit families for planned_for_extended_audit flag")
    p.add_argument("--data-dir", default="data/raw/ibkr")
    args = p.parse_args(argv)
    cwd = Path.cwd()
    cr = Path(args.candidate_root)
    if not cr.is_absolute():
        cr = cwd / cr
    out = Path(args.output_root)
    if not out.is_absolute():
        out = cwd / out
    runs_sub = out / "local_runs"
    wids = _parse_windows(args.windows)
    from src.research.audit_l2_candidates_oow_lib import family_group, safe_run_segment

    def has_metrics(cid: str, wid: str) -> bool:
        seg = safe_run_segment(cid)
        wdir = runs_sub / seg / wid
        if not wdir.is_dir():
            return False
        lat = _latest_run_dir(wdir)
        return bool(lat and (lat / "metrics.json").is_file())

    all_metas = iter_candidate_metas(cr)
    aud_ids = {m.candidate_id for m in all_metas if all(has_metrics(m.candidate_id, w) for w in wids)}
    fam_filter: set[str] | None = None
    if args.families:
        fam_filter = {x.strip().lower() for x in args.families.split(",") if x.strip()}
    rows: list[dict[str, Any]] = []
    for m in all_metas:
        g = family_group(m)
        aid = m.candidate_id in aud_ids
        planned = (not aid) and (not fam_filter or g in fam_filter)
        rows.append(
            {
                "candidate_id": m.candidate_id,
                "strategy": m.strategy,
                "family": g,
                "side": m.side,
                "yaml_path": m.yaml_path,
                "already_audited": "yes" if aid else "no",
                "planned_for_extended_audit": "yes" if planned else "no",
                "reason": "all windows have metrics.json" if aid else ("matches family filter" if planned else "outside filter or already done"),
                "notes": "",
            }
        )
    import pandas as pd

    inv = pd.DataFrame(rows).sort_values(["already_audited", "family", "candidate_id"])
    inv.to_csv(out / "remaining_candidate_inventory.csv", index=False)
    n_all = len(all_metas)
    n_aud = len(aud_ids)
    n_plan = int((inv["planned_for_extended_audit"] == "yes").sum())
    git_tip = ""
    try:
        git_tip = subprocess.check_output(
            ["git", "log", "-1", "--oneline"],
            cwd=str(_ROOT),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        git_tip = "(unavailable)"
    nh_path = _ROOT / "NEXT_HANDOFF.md"
    handoff_decision = "(see NEXT_HANDOFF.md §J. Decision)"
    for path in (out / "layer2_candidate_robustness_decision.md", nh_path):
        if not path.is_file():
            continue
        nh = path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"\*\*`([^`]+)`\*\*", nh)
        if m:
            handoff_decision = m.group(1).strip()
            break
    aud_fams = sorted({str(x) for x in inv.loc[inv["already_audited"] == "yes", "family"].unique()})
    rem_fams = sorted({str(x) for x in inv.loc[inv["already_audited"] == "no", "family"].unique()})
    plan_ids = inv.loc[inv["planned_for_extended_audit"] == "yes", "candidate_id"].astype(str).tolist()
    skip_ids = inv.loc[inv["already_audited"] == "yes", "candidate_id"].astype(str).tolist()
    post_paths = [
        "candidate_oow_metrics.csv",
        "candidate_oow_wide_metrics.csv",
        "candidate_robustness_labels.csv",
        "family_oow_summary.csv",
        "strategy_oow_summary.csv",
        "candidate_audit_run_manifest.csv",
        "run_execution_manifest.csv",
        "run_discovery_manifest.csv",
        "l2_core_failure_analysis.csv",
        "l2_core_policy_v2_candidate_actions.csv",
    ]
    if n_aud >= n_all:
        skip_section_title = "### All l2_core candidates (metrics complete on all windows)"
        skip_note = f"**{n_all}** candidates — list for inventory reconciliation (not only last-wave skips)."
    else:
        skip_section_title = "### Candidates with prior full-window metrics (typical `--skip-existing` hits)"
        skip_note = ""
    lines = [
        "# Extended audit inventory",
        "",
        "## Repo / handoff",
        "",
        f"- **git tip:** `{git_tip}`",
        f"- **handoff decision (parsed from `layer2_candidate_robustness_decision.md` then `NEXT_HANDOFF.md`):** `{handoff_decision}`",
        "",
        "## Candidate root and coverage",
        "",
        f"- candidate root: `{cr.as_posix()}`",
        f"- total l2_core YAMLs: **{n_all}**",
        f"- fully replayed (metrics.json on all **{len(wids)}** windows): **{n_aud}**",
        f"- remaining without full metrics grid: **{n_all - n_aud}**",
        f"- planned in filtered slice (`planned_for_extended_audit=yes`): **{n_plan}**",
        f"- **audit families already complete:** {', '.join(aud_fams) or '(none)'}",
        f"- **families still incomplete (if any):** {', '.join(rem_fams) if n_all - n_aud else '(none — full grid)'}",
        "",
        "## Candidate IDs",
        "",
        "### Planned for extended singleton run (this filter)",
        "",
        ("- " + "\n- ".join(plan_ids)) if plan_ids else "- *(none — all candidates have metrics on all windows, or filter excluded remaining)*",
        "",
        skip_section_title,
        "",
        skip_note,
        "",
        ("- " + "\n- ".join(skip_ids)) if skip_ids else "- *(none)*",
        "",
        "## Local raw runs (do not commit)",
        "",
        f"- `{runs_sub.as_posix()}/<candidate_id>/<window_id>/run_*`",
        "",
        "## Postprocess outputs (curated, under output root)",
        "",
        "\n".join(f"- `{p}`" for p in post_paths),
        "",
        "## Reconciliation",
        "",
        f"- `n_all` ({n_all}) = `n_aud` ({n_aud}) + incomplete ({n_all - n_aud})",
        "",
    ]
    (out / "extended_audit_inventory.md").write_text("\n".join(lines), encoding="utf-8")
    try:
        md_body = inv.to_markdown(index=False)
    except Exception:
        md_body = "```\n" + inv.to_csv(index=False) + "\n```\n"
    (out / "remaining_candidate_inventory.md").write_text("# Remaining candidate inventory\n\n" + md_body, encoding="utf-8")
    print(f"[audit] wrote {out / 'remaining_candidate_inventory.csv'}", flush=True)
    return 0


def cmd_run(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Run singleton combiner replays per candidate × window.")
    p.add_argument("--candidate-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--combiner-config", default=None)
    p.add_argument("--windows-root", default="src/research/results/fixed_profile_oow_v1")
    p.add_argument("--windows", default="early_oow,insample_ref,late_oow")
    p.add_argument("--families", default=None, help="Comma-separated: vwap,indicator,opening_trap,pa,afternoon,other,all")
    p.add_argument("--candidates", default=None, help="Comma-separated candidate_ids (overrides families)")
    p.add_argument("--max-candidates", type=int, default=0)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--skip-existing", action="store_true")
    p.add_argument("--stop-on-fail", action="store_true")
    p.add_argument("--data-dir", default="data/raw/ibkr")
    p.add_argument("--tag", default="l2_candidate_audit")
    p.add_argument("--use-signal-cache", action="store_true")
    p.add_argument(
        "--no-signal-cache",
        action="store_true",
        help="Default-safe: do not use disk signal cache (same as omitting --use-signal-cache).",
    )
    args = p.parse_args(argv)
    cwd = Path.cwd()
    repo = _ROOT
    out = Path(args.output_root)
    if not out.is_absolute():
        out = cwd / out
    cr = Path(args.candidate_root)
    if not cr.is_absolute():
        cr = cwd / cr
    wr = Path(args.windows_root)
    if not wr.is_absolute():
        wr = cwd / wr
    cfg = Path(args.combiner_config) if args.combiner_config else _default_combiner_config(repo)
    if not cfg.is_absolute():
        cfg = cwd / cfg
    bounds = load_window_bounds(wr, data_dir=args.data_dir)
    windows = [w for w in _parse_windows(args.windows) if w in bounds]
    for w in _parse_windows(args.windows):
        if w not in bounds:
            print(f"[audit] skip unknown window {w}", file=sys.stderr)

    metas = iter_candidate_metas(cr)
    want_ids = set(_parse_csv_ids(args.candidates))
    if want_ids:
        metas = [m for m in metas if m.candidate_id in want_ids]
    elif args.families:
        fams = {x.strip().lower() for x in args.families.split(",") if x.strip()}
        metas = filter_by_families(metas, fams)
    if args.max_candidates and args.max_candidates > 0:
        metas = metas[: args.max_candidates]

    runs_sub = out / "local_runs"
    runs_sub.mkdir(parents=True, exist_ok=True)
    exec_rows: list[dict[str, Any]] = []
    from src.research.audit_l2_candidates_oow_lib import safe_run_segment

    n_planned = 0
    abort = False
    for m in metas:
        if abort:
            break
        seg = safe_run_segment(m.candidate_id)
        for wid in windows:
            n_planned += 1
            st, en = bounds[wid]
            wdir = runs_sub / seg / wid
            wdir.mkdir(parents=True, exist_ok=True)
            existing = _latest_run_dir(wdir)
            if args.skip_existing and existing and _run_has_metrics(existing):
                exec_rows.append(
                    {
                        "candidate_id": m.candidate_id,
                        "window_id": wid,
                        "status": "SKIPPED",
                        "returncode": "",
                        "run_dir": str(existing),
                        "argv": "",
                    }
                )
                continue
            argv = _combiner_singleton_argv(
                python_exe=sys.executable,
                candidate_root=cr,
                combiner_config=cfg,
                candidate_id=m.candidate_id,
                start=st,
                end=en,
                out_window_root=wdir,
                data_dir=args.data_dir,
                use_signal_cache=bool(args.use_signal_cache) and not bool(args.no_signal_cache),
                tag=args.tag,
            )
            if args.dry_run:
                print(" ".join(argv))
                exec_rows.append(
                    {
                        "candidate_id": m.candidate_id,
                        "window_id": wid,
                        "status": "DRY_RUN",
                        "returncode": "",
                        "run_dir": str(wdir),
                        "argv": " ".join(argv),
                    }
                )
                continue
            print(f"[audit] {m.candidate_id} {wid} {st}..{en}", flush=True)
            rc = subprocess.call(argv, cwd=str(cwd))
            latest = _latest_run_dir(wdir)
            exec_rows.append(
                {
                    "candidate_id": m.candidate_id,
                    "window_id": wid,
                    "status": "OK" if rc == 0 else "FAIL",
                    "returncode": rc,
                    "run_dir": str(latest) if latest else "",
                    "argv": " ".join(argv),
                }
            )
            if args.stop_on_fail and rc != 0:
                abort = True
                break

    manifest_path = out / "candidate_audit_run_manifest.csv"
    fieldnames = ["candidate_id", "window_id", "status", "returncode", "run_dir", "argv"]
    for path in (manifest_path, out / "run_execution_manifest.csv"):
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for row in exec_rows:
                w.writerow({k: row.get(k, "") for k in fieldnames})
    disc_rows: list[dict[str, str]] = []
    for cid, wid, rdir in discover_singleton_runs(runs_sub):
        disc_rows.append(
            {
                "candidate_id": cid,
                "window_id": wid,
                "run_dir": str(rdir),
                "has_metrics": str(_run_has_metrics(rdir)),
            }
        )
    pdisc = out / "run_discovery_manifest.csv"
    with pdisc.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["candidate_id", "window_id", "run_dir", "has_metrics"])
        w.writeheader()
        for row in disc_rows:
            w.writerow(row)
    print(f"[audit] wrote {manifest_path} ({len(exec_rows)} execution rows, {len(disc_rows)} discovered runs)", flush=True)
    failed = [r for r in exec_rows if r.get("status") == "FAIL"]
    return 1 if failed else 0


def cmd_postprocess(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Aggregate singleton runs into curated CSVs.")
    p.add_argument("--candidate-root", required=True)
    p.add_argument("--output-root", required=True)
    args = p.parse_args(argv)
    cwd = Path.cwd()
    out = Path(args.output_root)
    if not out.is_absolute():
        out = cwd / out
    cr = Path(args.candidate_root)
    if not cr.is_absolute():
        cr = cwd / cr
    runs_sub = out / "local_runs"
    long_df = collect_long_metrics_frame(runs_root=runs_sub, candidate_root=cr)
    long_df.to_csv(out / "candidate_oow_metrics.csv", index=False)
    wide = merge_metrics_for_labels(long_df)
    if not wide.empty:
        wide.to_csv(out / "candidate_oow_wide_metrics.csv", index=False)
    labels = labels_table_from_wide(wide)
    labels.to_csv(out / "candidate_robustness_labels.csv", index=False)
    fam = family_label_counts(wide)
    if not fam.empty:
        fam.to_csv(out / "family_oow_summary.csv", index=False)
    st = strategy_label_counts(wide)
    if not st.empty:
        st.to_csv(out / "strategy_oow_summary.csv", index=False)

    repo = _ROOT
    prof_cfg = _fixed_profile_config_map(repo)
    by_prof = fixed_profile_strategy_candidates(fixed_profile_configs=prof_cfg, candidate_root=cr)
    fail_rows: list[dict[str, Any]] = []
    if not long_df.empty:
        for pid, cids in by_prof.items():
            for cid in cids:
                sub = long_df[long_df["candidate_id"] == cid]
                row: dict[str, Any] = {"profile_id": pid, "candidate_id": cid}
                for wid in ("early_oow", "insample_ref", "late_oow"):
                    s2 = sub[sub["window_id"] == wid]
                    if s2.empty:
                        row[f"total_r_{wid}"] = ""
                        row[f"trades_{wid}"] = ""
                        row[f"status_{wid}"] = "MISSING"
                    else:
                        r0 = s2.iloc[0]
                        row[f"total_r_{wid}"] = r0.get("total_r", "")
                        row[f"trades_{wid}"] = r0.get("trades", "")
                        row[f"status_{wid}"] = r0.get("status", "")
                if not wide.empty and cid in set(wide["candidate_id"].astype(str)):
                    row["robustness_label"] = str(wide[wide["candidate_id"].astype(str) == cid].iloc[0]["robustness_label"])
                else:
                    row["robustness_label"] = ""
                fail_rows.append(row)
    pd = __import__("pandas")
    pd.DataFrame(fail_rows).to_csv(out / "l2_core_failure_analysis.csv", index=False)

    # policy v2 candidate actions (same as labels policy_action column)
    if not labels.empty:
        pol = labels[["candidate_id", "audit_family", "robustness_label", "policy_action", "yaml_path"]].copy()
        pol.to_csv(out / "l2_core_policy_v2_candidate_actions.csv", index=False)
        write_candidate_oow_summary_md(out=out, labels=labels)
        write_compact_highlights(out=out, wide=wide)
        write_full_candidate_interpretation(out=out, long_df=long_df, wide=wide)
        write_family_interpretation(out=out, wide=wide, long_df=long_df)
        write_policy_action_summary(out=out, labels=labels)
        write_robust_core_dry_run(out=out, labels=labels)
        write_side_flip_watchlist(out=out, labels=labels)

    disc_rows: list[dict[str, str]] = []
    for cid, wid, rdir in discover_singleton_runs(runs_sub):
        disc_rows.append(
            {
                "candidate_id": cid,
                "window_id": wid,
                "run_dir": str(rdir),
                "has_metrics": str(_run_has_metrics(rdir)),
            }
        )
    with (out / "run_discovery_manifest.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["candidate_id", "window_id", "run_dir", "has_metrics"])
        w.writeheader()
        for row in disc_rows:
            w.writerow(row)
    man = out / "candidate_audit_run_manifest.csv"
    if man.is_file():
        shutil.copy(man, out / "run_execution_manifest.csv")
    print(f"[audit] postprocess wrote CSVs under {out}", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Layer2 candidate-level OOW audit.")
    sub = p.add_subparsers(dest="cmd", required=True)

    s0 = sub.add_parser("inspect-data", help="Write data_availability.csv (fixed-profile helper).")
    s0.add_argument("--output-root", required=True)
    s0.add_argument("--symbol", default="QQQ")
    s0.add_argument("--data-dir", default="data/raw/ibkr")

    s2 = sub.add_parser("print-commands")
    s2.add_argument("--candidate-root", required=True)
    s2.add_argument("--combiner-config", default=None)
    s2.add_argument("--windows-root", default="src/research/results/fixed_profile_oow_v1")
    s2.add_argument("--windows", default="early_oow,insample_ref,late_oow")
    s2.add_argument("--candidate-id", default="VWAP_RECLAIM_REJECT_001")
    s2.add_argument("--data-dir", default="data/raw/ibkr")

    s3 = sub.add_parser("run")
    s3.add_argument("--candidate-root", required=True)
    s3.add_argument("--output-root", required=True)
    s3.add_argument("--combiner-config", default=None)
    s3.add_argument("--windows-root", default="src/research/results/fixed_profile_oow_v1")
    s3.add_argument("--windows", default="early_oow,insample_ref,late_oow")
    s3.add_argument("--families", default=None)
    s3.add_argument("--candidates", default=None)
    s3.add_argument("--max-candidates", type=int, default=0)
    s3.add_argument("--dry-run", action="store_true")
    s3.add_argument("--skip-existing", action="store_true")
    s3.add_argument("--stop-on-fail", action="store_true")
    s3.add_argument("--data-dir", default="data/raw/ibkr")
    s3.add_argument("--tag", default="l2_candidate_audit")
    s3.add_argument("--use-signal-cache", action="store_true")
    s3.add_argument(
        "--no-signal-cache",
        action="store_true",
        help="Explicitly disable disk signal cache (default; safe on OneDrive).",
    )

    s4 = sub.add_parser("postprocess")
    s4.add_argument("--candidate-root", required=True)
    s4.add_argument("--output-root", required=True)
    s4.add_argument(
        "--windows-root",
        default=None,
        help="Optional; reserved for future window discovery (currently uses runs on disk only).",
    )

    s5 = sub.add_parser("inventory", help="Write remaining_candidate_inventory.* and extended_audit_inventory.md.")
    s5.add_argument("--candidate-root", required=True)
    s5.add_argument("--output-root", required=True)
    s5.add_argument("--windows-root", default="src/research/results/fixed_profile_oow_v1")
    s5.add_argument("--windows", default="early_oow,insample_ref,late_oow")
    s5.add_argument("--families", default=None)
    s5.add_argument("--data-dir", default="data/raw/ibkr")

    args = p.parse_args(argv)
    if args.cmd == "inspect-data":
        return fixed_cmd_inspect_data(
            [
                "--output-root",
                args.output_root,
                "--symbol",
                args.symbol,
                "--data-dir",
                args.data_dir,
            ]
        )
    if args.cmd == "print-commands":
        return cmd_print_commands(
            [
                "--candidate-root",
                args.candidate_root,
                *(["--combiner-config", args.combiner_config] if args.combiner_config else []),
                "--windows-root",
                args.windows_root,
                "--windows",
                args.windows,
                "--candidate-id",
                args.candidate_id,
                "--data-dir",
                args.data_dir,
            ]
        )
    if args.cmd == "run":
        return cmd_run(
            [
                "--candidate-root",
                args.candidate_root,
                "--output-root",
                args.output_root,
                *(["--combiner-config", args.combiner_config] if args.combiner_config else []),
                "--windows-root",
                args.windows_root,
                "--windows",
                args.windows,
                *(["--families", args.families] if args.families else []),
                *(["--candidates", args.candidates] if args.candidates else []),
                "--max-candidates",
                str(args.max_candidates),
                *(["--dry-run"] if args.dry_run else []),
                *(["--skip-existing"] if args.skip_existing else []),
                *(["--stop-on-fail"] if args.stop_on_fail else []),
                "--data-dir",
                args.data_dir,
                "--tag",
                args.tag,
                *(["--use-signal-cache"] if args.use_signal_cache else []),
                *(["--no-signal-cache"] if args.no_signal_cache else []),
            ]
        )
    if args.cmd == "inventory":
        return cmd_inventory(
            [
                "--candidate-root",
                args.candidate_root,
                "--output-root",
                args.output_root,
                "--windows-root",
                args.windows_root,
                "--windows",
                args.windows,
                *(["--families", args.families] if args.families else []),
                "--data-dir",
                args.data_dir,
            ]
        )
    if args.cmd == "postprocess":
        return cmd_postprocess(
            [
                "--candidate-root",
                args.candidate_root,
                "--output-root",
                args.output_root,
            ]
        )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
