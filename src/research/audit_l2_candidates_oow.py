"""
Per-candidate Layer2 combiner OOW audit (research-only).

Does not edit candidate YAMLs or optimize on OOW. Default: no signal cache.
"""
from __future__ import annotations

import argparse
import csv
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
    for m in metas:
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
                use_signal_cache=bool(args.use_signal_cache),
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

    s4 = sub.add_parser("postprocess")
    s4.add_argument("--candidate-root", required=True)
    s4.add_argument("--output-root", required=True)

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
