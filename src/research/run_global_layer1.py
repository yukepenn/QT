"""
Global Layer 1 orchestration: read global_strategy_audit CSV, run sweep.py per
runnable strategy (READY_* and raw grid <= --max-grid-size), write extended
manifest, optional strict candidate selection.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.research.run_layer1_focused import (
    SWEEP_PY,
    _best_row_metrics,
    _latest_tagged_sweep_folder,
    _parse_summary_txt,
    _safe_tag,
)
from src.strategies.metadata import get_strategy_metadata

RUNNABLE_STATUSES = frozenset(
    {"READY_GLOBAL_L1", "READY_LONG_ONLY", "READY_SHORT_OR_BOTH"}
)

GLOBAL_MANIFEST_FIELDS = [
    "strategy",
    "family",
    "status",
    "side_policy",
    "testing_config",
    "raw_grid_size",
    "capped",
    "max_combos",
    "result_rows",
    "best_trades",
    "best_total_r",
    "best_profit_factor",
    "best_profit_factor_r",
    "best_max_drawdown_r",
    "best_avg_bars_held",
    "sweep_folder",
    "results_csv",
    "notes",
]


def _read_audit(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=GLOBAL_MANIFEST_FIELDS, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in GLOBAL_MANIFEST_FIELDS})


def _write_manifest_md(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Global Layer 1 sweep manifest",
        "",
        "| strategy | family | status | raw_grid | rows | best_pf | best_total_r | sweep |",
        "|----------|--------|--------|----------|------|---------|--------------|-------|",
    ]
    for row in rows:
        sf = Path(str(row.get("sweep_folder", ""))).name if row.get("sweep_folder") else ""
        lines.append(
            f"| {row.get('strategy','')} | {row.get('family','')} | {row.get('status','')} | "
            f"{row.get('raw_grid_size','')} | {row.get('result_rows','')} | "
            f"{row.get('best_profit_factor','')} | {row.get('best_total_r','')} | `{sf}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_skipped(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("strategy,reason\n", encoding="utf-8")
        return
    keys = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def _write_skipped_md(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = ["# Skipped strategies (global Layer 1)", ""]
    if not rows:
        lines.append("(none)")
    else:
        lines.append("| strategy | reason |")
        lines.append("|----------|--------|")
        for r in rows:
            lines.append(f"| {r.get('strategy','')} | {r.get('reason','')} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def _write_strategy_diversity_summary_md(div_out: Path) -> None:
    pcsv = div_out / "strategy_diversity_summary.csv"
    if not pcsv.is_file():
        return
    df = pd.read_csv(pcsv)
    headers = list(df.columns)
    body = [[str(v) for v in row] for row in df.values.tolist()]
    text = "# Strategy diversity summary\n\n" + _md_table(headers, body) + "\n"
    (div_out / "strategy_diversity_summary.md").write_text(text, encoding="utf-8")


def _write_family_candidate_summary(sel_csv: Path, out_csv: Path, out_md: Path) -> None:
    if not sel_csv.is_file():
        return
    df = pd.read_csv(sel_csv)
    if df.empty or "strategy" not in df.columns:
        return
    if "strategy_family" in df.columns:
        fam_series = df["strategy_family"].astype(str)
    else:
        fam_series = df["strategy"].astype(str).map(
            lambda s: str(get_strategy_metadata(s).get("family", "unknown"))
        )
    work = df.assign(_family=fam_series)
    g = (
        work.groupby("_family", dropna=False)
        .size()
        .reset_index(name="n_candidates")
        .sort_values("n_candidates", ascending=False)
        .rename(columns={"_family": "family"})
    )
    g.to_csv(out_csv, index=False)
    headers = ["family", "n_candidates"]
    body = [[str(r["family"]), str(int(r["n_candidates"]))] for _, r in g.iterrows()]
    out_md.write_text("# Family candidate summary\n\n" + _md_table(headers, body) + "\n", encoding="utf-8")


def _run_post_analysis(args: argparse.Namespace, out_root: Path, manifest_rows: list[dict[str, Any]]) -> None:
    div_out = args.diversity_output_root
    if div_out is None:
        div_out = (
            _ROOT
            / "src"
            / "research"
            / "results"
            / "global_candidate_signal_diversity_qqq_2023_2024_v1"
        )
    else:
        if not div_out.is_absolute():
            div_out = Path.cwd() / div_out
    div_out.mkdir(parents=True, exist_ok=True)
    sel_dir = out_root / "selected_candidates"
    yamls = sorted(sel_dir.glob("*.yaml")) if sel_dir.is_dir() else []

    div_cmd = [
        sys.executable,
        str(_ROOT / "src" / "research" / "candidate_signal_diversity.py"),
        "--candidate-root",
        str(out_root.resolve()),
        "--asset",
        args.asset,
        "--symbol",
        args.symbol,
        "--start",
        args.start,
        "--end",
        args.end,
        "--output-root",
        str(div_out.resolve()),
    ]
    print("=" * 60, flush=True)
    print("[GLOBAL L1] candidate_signal_diversity", flush=True)
    div_rc = 0
    if yamls:
        print(" ".join(div_cmd), flush=True)
        div_rc = subprocess.call(div_cmd, cwd=str(_ROOT))
        if div_rc == 0:
            _write_strategy_diversity_summary_md(div_out)
        else:
            print(f"WARNING diversity exit {div_rc}", flush=True)
    else:
        print("SKIP diversity (no selected YAMLs)", flush=True)

    fc_csv = out_root / "fast_context_check.csv"
    fc_md = out_root / "fast_context_check.md"
    fc_cmd = [
        sys.executable,
        str(_ROOT / "src" / "research" / "check_selected_candidates_fast_context.py"),
        "--candidate-root",
        str(out_root.resolve()),
        "--asset",
        args.asset,
        "--symbol",
        args.symbol,
        "--start",
        "2023-01-03",
        "--end",
        "2023-01-31",
        "--out-csv",
        str(fc_csv.resolve()),
        "--out-md",
        str(fc_md.resolve()),
    ]
    print("=" * 60, flush=True)
    print("[GLOBAL L1] check_selected_candidates_fast_context", flush=True)
    fc_rc = 0
    if yamls:
        print(" ".join(fc_cmd), flush=True)
        fc_rc = subprocess.call(fc_cmd, cwd=str(_ROOT))
    else:
        print("SKIP fast-context (no selected YAMLs)", flush=True)

    sel_csv = out_root / "selected_candidates.csv"
    fam_csv = div_out / "family_candidate_summary.csv"
    fam_md = div_out / "family_candidate_summary.md"
    _write_family_candidate_summary(sel_csv, fam_csv, fam_md)

    mf = pd.DataFrame(manifest_rows)
    n_families_strict = 0
    if sel_csv.is_file():
        sdf_gate = pd.read_csv(sel_csv)
        if not sdf_gate.empty:
            if "strategy_family" in sdf_gate.columns:
                fams = {
                    str(x)
                    for x in sdf_gate["strategy_family"].dropna().unique()
                    if str(x).strip()
                }
            else:
                fams = {
                    str(get_strategy_metadata(strat).get("family", "unknown"))
                    for strat in sdf_gate["strategy"].astype(str).unique()
                }
            n_families_strict = len(fams)
    dup_n = 0
    dup_path = div_out / "duplicate_signal_groups.csv"
    if dup_path.is_file():
        dup_n = max(0, len(dup_path.read_text(encoding="utf-8").splitlines()) - 1)

    gate_lines = [
        "# Global Layer 2 gate (post Layer 1)",
        "",
        f"- strict_candidate_yaml_count: **{len(yamls)}**",
        f"- distinct_families_in_strict_selected: **{n_families_strict}** (need ≥3)",
        f"- duplicate_signal_group_rows: **{dup_n}** (readability heuristic)",
        f"- fast_context_exit_code: **{fc_rc}** (0 = all rows ok)",
        f"- diversity_exit_code: **{div_rc}**",
        "",
    ]
    gate_ok = (
        n_families_strict >= 3
        and len(yamls) <= 80
        and fc_rc == 0
        and div_rc == 0
        and dup_n <= 200
    )
    if len(yamls) > 80:
        gate_lines.append(f"- **gate block:** strict YAML count **{len(yamls)}** > **80** (Layer 2 prerun cap).")
    gate_lines.append(f"**gate_passes_layer2_prerun:** {'YES' if gate_ok else 'NO'}")
    gate_lines.append("")
    if not gate_ok:
        gate_lines.append(
            "Conditional Global Layer 2 **not** executed (see `global_layer2_qqq_2023_2024_design.md`)."
        )
    gate_body = "\n".join(gate_lines) + "\n"
    (out_root / "global_layer2_gate_decision.md").write_text(gate_body, encoding="utf-8")
    if args.copy_gate_md_to is not None:
        gpath = args.copy_gate_md_to
        if not gpath.is_absolute():
            gpath = Path.cwd() / gpath
        gpath.parent.mkdir(parents=True, exist_ok=True)
        gpath.write_text(gate_body, encoding="utf-8")

    # layer1_global_summary.md
    summary_parts = [
        "# Global Layer 1 summary (QQQ, in-sample)",
        "",
        f"- window: `{args.start}` → `{args.end}`",
        f"- tag: `{args.tag}`",
        f"- manifest_rows: **{len(manifest_rows)}**",
        f"- strict_selected_yaml: **{len(yamls)}**",
        "",
        "Interpretation: in-sample sweep rankings; not live-ready.",
        "",
        "## Manifest overview",
        "",
    ]
    if not mf.empty and "strategy" in mf.columns:
        show = mf[
            [
                c
                for c in (
                    "strategy",
                    "family",
                    "status",
                    "raw_grid_size",
                    "result_rows",
                    "best_total_r",
                    "best_profit_factor",
                    "best_max_drawdown_r",
                )
                if c in mf.columns
            ]
        ]
        summary_parts.append(_md_table(list(show.columns), [[str(x) for x in row] for row in show.values.tolist()]))
    summary_parts.extend(["", "## Gate snapshot", "", f"See `global_layer2_gate_decision.md`."])
    (out_root / "layer1_global_summary.md").write_text("\n".join(summary_parts) + "\n", encoding="utf-8")

    # Branch leaderboard (repo-level research/results)
    lb_csv = args.branch_leaderboard_csv
    lb_md = args.branch_leaderboard_md
    if lb_csv is None:
        lb_csv = _ROOT / "src" / "research" / "results" / "global_branch_leaderboard_v1.csv"
    elif not lb_csv.is_absolute():
        lb_csv = Path.cwd() / lb_csv
    if lb_md is None:
        lb_md = _ROOT / "src" / "research" / "results" / "global_branch_leaderboard_v1.md"
    elif not lb_md.is_absolute():
        lb_md = Path.cwd() / lb_md
    lb_rows: list[dict[str, Any]] = []
    div_by_strat: dict[str, dict[str, Any]] = {}
    dsum = div_out / "strategy_diversity_summary.csv"
    if dsum.is_file():
        ddf = pd.read_csv(dsum)
        for _, r in ddf.iterrows():
            div_by_strat[str(r.get("strategy", ""))] = r.to_dict()

    per_strat_sel: dict[str, int] = {}
    if sel_csv.is_file():
        s2 = pd.read_csv(sel_csv)
        if not s2.empty and "strategy" in s2.columns:
            per_strat_sel = s2.groupby("strategy").size().to_dict()

    for row in manifest_rows:
        strat = str(row.get("strategy", ""))
        drow = div_by_strat.get(strat, {})
        lb_rows.append(
            {
                "strategy": strat,
                "family": row.get("family", ""),
                "side_policy": row.get("side_policy", ""),
                "manifest_status": row.get("status", ""),
                "strict_candidate_count": int(per_strat_sel.get(strat, 0)),
                "best_total_r_manifest": row.get("best_total_r", ""),
                "best_pf_manifest": row.get("best_profit_factor", ""),
                "best_max_dd_r_manifest": row.get("best_max_drawdown_r", ""),
                "best_trades_manifest": row.get("best_trades", ""),
                "n_unique_pure_hash": drow.get("n_unique_pure_signal_hash", ""),
                "result_rows_sweep": row.get("result_rows", ""),
            }
        )
    lb_df = pd.DataFrame(lb_rows)
    lb_df.to_csv(lb_csv, index=False)
    lb_title = "Global branch leaderboard v2" if "v2" in lb_csv.name else "Global branch leaderboard v1"
    if not lb_df.empty:
        headers = list(lb_df.columns)
        body = [[str(v) for v in r] for r in lb_df.values.tolist()]
        lb_md.write_text(f"# {lb_title}\n\n" + _md_table(headers, body) + "\n", encoding="utf-8")
    else:
        lb_md.write_text(f"# {lb_title}\n\n(no rows)\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--asset", default="equity")
    p.add_argument("--symbol", default="QQQ")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--audit", type=Path, required=True, help="strategy_eligibility_matrix.csv")
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--max-grid-size", type=int, default=1500)
    p.add_argument("--top", type=int, default=50)
    p.add_argument("--min-trades", type=int, default=30)
    p.add_argument("--progress-every", type=int, default=50)
    p.add_argument("--strategy-limit", type=int, default=None, help="Max runnable sweeps (smallest grids first).")
    p.add_argument(
        "--preflight-only",
        action="store_true",
        help="Write manifest/skipped rows only; do not invoke sweep.py.",
    )
    p.add_argument(
        "--select-candidates",
        action="store_true",
        help="After sweeps, run select_candidates.py with strict thresholds.",
    )
    p.add_argument(
        "--no-post-analysis",
        action="store_true",
        help="Skip diversity, fast-context check, Layer1 summary, and branch leaderboard.",
    )
    p.add_argument(
        "--diversity-output-root",
        type=Path,
        default=None,
        help="Output root for candidate_signal_diversity.py (default: legacy v1 path).",
    )
    p.add_argument(
        "--branch-leaderboard-csv",
        type=Path,
        default=None,
        help="Write global branch leaderboard CSV here (default: v1 path under research/results).",
    )
    p.add_argument(
        "--branch-leaderboard-md",
        type=Path,
        default=None,
        help="Write global branch leaderboard MD here (default: v1 path under research/results).",
    )
    p.add_argument(
        "--copy-gate-md-to",
        type=Path,
        default=None,
        help="Also write global_layer2_gate_decision.md body to this path (e.g. research/results gate v2).",
    )
    args = p.parse_args(argv)

    out_root = args.output_root
    if not out_root.is_absolute():
        out_root = Path.cwd() / out_root
    out_root.mkdir(parents=True, exist_ok=True)

    audit_path = args.audit
    if not audit_path.is_absolute():
        audit_path = Path.cwd() / audit_path
    if not audit_path.is_file():
        print(f"ERROR missing audit {audit_path}", file=sys.stderr)
        return 2

    tag_safe = _safe_tag(args.tag)
    manifest_csv = out_root / "sweep_manifest.csv"
    manifest_md = out_root / "sweep_manifest.md"
    skipped_csv = out_root / "skipped_strategies.csv"
    skipped_md = out_root / "skipped_strategies.md"

    cfg_doc = [
        "# Global Layer 1 run configuration",
        "",
        f"- asset: `{args.asset}`",
        f"- symbol: `{args.symbol}`",
        f"- window: `{args.start}` → `{args.end}`",
        f"- audit: `{audit_path}`",
        f"- tag: `{args.tag}` (safe: `{tag_safe}`)",
        f"- max_grid_size: **{args.max_grid_size}**",
        f"- strategy_limit: **{args.strategy_limit}**",
        f"- preflight_only: **{args.preflight_only}**",
        f"- select_candidates: **{args.select_candidates}**",
        "",
        "Re-run without `--strategy-limit` after validating disk/time budget.",
    ]
    (out_root / "global_layer1_run_config.md").write_text("\n".join(cfg_doc) + "\n", encoding="utf-8")

    audit_rows = _read_audit(audit_path)
    manifest_rows: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    runnable: list[dict[str, str]] = []
    for r in audit_rows:
        st = (r.get("current_status") or "").strip()
        try:
            gs = int(float(r.get("raw_grid_size") or 0))
        except ValueError:
            gs = 0
        if st not in RUNNABLE_STATUSES:
            skipped.append(
                {
                    "strategy": r.get("strategy", ""),
                    "reason": f"audit_status:{st}",
                }
            )
            continue
        if gs > args.max_grid_size:
            skipped.append(
                {
                    "strategy": r.get("strategy", ""),
                    "reason": f"REVIEW_GRID_TOO_LARGE raw_grid={gs}",
                }
            )
            continue
        rr = dict(r)
        rr["_gs"] = gs
        runnable.append(rr)

    runnable.sort(key=lambda x: x["_gs"])

    if args.strategy_limit is not None:
        rest = runnable[args.strategy_limit :]
        runnable = runnable[: args.strategy_limit]
        for r in rest:
            skipped.append(
                {
                    "strategy": r.get("strategy", ""),
                    "reason": f"strategy_limit>{args.strategy_limit} (grid={r.get('_gs')})",
                }
            )

    sym = str(args.symbol).upper()

    for r in runnable:
        strategy = r["strategy"]
        family = r.get("family", "")
        testing = Path(r.get("recommended_testing_yaml", "").strip())
        side_policy = r.get("short_support_label", "long_only")
        raw_gs = int(r["_gs"])
        if args.preflight_only:
            manifest_rows.append(
                {
                    "strategy": strategy,
                    "family": family,
                    "status": "preflight_only",
                    "side_policy": side_policy,
                    "testing_config": str(testing),
                    "raw_grid_size": raw_gs,
                    "capped": "false",
                    "max_combos": "",
                    "result_rows": "",
                    "best_trades": "",
                    "best_total_r": "",
                    "best_profit_factor": "",
                    "best_profit_factor_r": "",
                    "best_max_drawdown_r": "",
                    "best_avg_bars_held": "",
                    "sweep_folder": "",
                    "results_csv": "",
                    "notes": "preflight_only",
                }
            )
            continue

        if not testing.is_file():
            manifest_rows.append(
                {
                    "strategy": strategy,
                    "family": family,
                    "status": "missing_testing_yaml",
                    "side_policy": side_policy,
                    "testing_config": str(testing),
                    "raw_grid_size": raw_gs,
                    "capped": "false",
                    "max_combos": "",
                    "result_rows": "",
                    "best_trades": "",
                    "best_total_r": "",
                    "best_profit_factor": "",
                    "best_profit_factor_r": "",
                    "best_max_drawdown_r": "",
                    "best_avg_bars_held": "",
                    "sweep_folder": "",
                    "results_csv": "",
                    "notes": "missing yaml",
                }
            )
            continue

        cmd = [
            sys.executable,
            str(SWEEP_PY),
            "--strategy",
            strategy,
            "--testing-config",
            str(testing.resolve()),
            "--asset",
            args.asset,
            "--symbols",
            sym,
            "--start",
            args.start,
            "--end",
            args.end,
            "--top",
            str(args.top),
            "--min-trades",
            str(args.min_trades),
            "--profile",
            "--tag",
            args.tag,
            "--progress-every",
            str(args.progress_every),
        ]
        print("=" * 60, flush=True)
        print(f"[GLOBAL L1] strategy={strategy} grid={raw_gs}", flush=True)
        print(" ".join(cmd), flush=True)
        t0 = time.perf_counter()
        proc = subprocess.Popen(
            cmd,
            cwd=str(_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="", flush=True)
        code = proc.wait()
        elapsed = time.perf_counter() - t0

        sweep_dir = _latest_tagged_sweep_folder(strategy, args.tag)
        results_csv = sweep_dir / "results.csv" if sweep_dir else Path("")
        summary_txt = sweep_dir / "summary.txt" if sweep_dir else Path("")
        summ = _parse_summary_txt(summary_txt) if summary_txt.is_file() else {}

        notes = ""
        result_rows = 0
        best: dict[str, Any] = {}
        df = pd.DataFrame()
        sweep_status: str
        if code != 0:
            notes = f"subprocess_exit_{code}"
            sweep_status = f"exit_{code}"
        elif not results_csv.is_file():
            notes = "missing_results_csv"
            sweep_status = "missing_results"
        else:
            df = pd.read_csv(results_csv)
            result_rows = len(df)
            best = _best_row_metrics(df)
            if result_rows == 0:
                notes = "no_rows"
                sweep_status = "ok_zero_trade"
            else:
                sweep_status = "ok"
        manifest_rows.append(
            {
                "strategy": strategy,
                "family": family,
                "status": sweep_status,
                "side_policy": side_policy,
                "testing_config": str(testing.resolve()),
                "raw_grid_size": raw_gs,
                "capped": "false",
                "max_combos": summ.get("combinations_completed", ""),
                "result_rows": result_rows,
                "best_trades": best.get("best_trades", ""),
                "best_total_r": best.get("best_total_r", ""),
                "best_profit_factor": best.get("best_profit_factor", ""),
                "best_profit_factor_r": best.get("best_profit_factor_r", ""),
                "best_max_drawdown_r": best.get("best_max_drawdown_r", ""),
                "best_avg_bars_held": best.get("best_avg_bars_held", ""),
                "sweep_folder": str(sweep_dir.resolve()) if sweep_dir else "",
                "results_csv": str(results_csv.resolve()) if results_csv.is_file() else "",
                "notes": f"elapsed_sec={round(elapsed,3)};{notes}",
            }
        )

    _write_manifest(manifest_csv, manifest_rows)
    _write_manifest_md(manifest_md, manifest_rows)
    _write_skipped(skipped_csv, skipped)
    _write_skipped_md(skipped_md, skipped)

    if args.select_candidates and not args.preflight_only:
        sel_cmd = [
            sys.executable,
            str(_ROOT / "src" / "research" / "select_candidates.py"),
            "--manifest",
            str(manifest_csv.resolve()),
            "--output-root",
            str(out_root.resolve()),
            "--top-per-strategy",
            "5",
            "--min-trades",
            "30",
            "--min-profit-factor",
            "1.05",
            "--min-total-r",
            "0",
            "--max-drawdown-r",
            "-60",
            "--max-avg-bars-held",
            "150",
            "--max-eod-count",
            "0",
            "--max-end-of-data-count",
            "0",
            "--sort-by",
            "candidate_score",
        ]
        print("=" * 60, flush=True)
        print("[GLOBAL L1] select_candidates strict", flush=True)
        print(" ".join(sel_cmd), flush=True)
        rc = subprocess.call(sel_cmd, cwd=str(_ROOT))
        sel_lines = [
            "# Candidate selection (strict)",
            "",
            "Command:",
            "",
            "```bash",
            " ".join(sel_cmd),
            "```",
            "",
            f"Exit code: **{rc}**",
        ]
        (out_root / "candidate_selection_config.md").write_text("\n".join(sel_lines) + "\n", encoding="utf-8")
        if rc != 0:
            print(f"WARNING select_candidates exit {rc}", flush=True)

        # no_candidate_strategies: manifest ok but zero YAMLs exported for that strategy
        sel_dir = out_root / "selected_candidates"
        yamls = list(sel_dir.glob("*.yaml")) if sel_dir.is_dir() else []
        per_strat: dict[str, int] = {}
        for yp in yamls:
            try:
                doc = yaml.safe_load(yp.read_text(encoding="utf-8"))
                s = str(doc.get("strategy", "")).strip()
                if s:
                    per_strat[s] = per_strat.get(s, 0) + 1
            except Exception:
                continue
        no_cand: list[str] = []
        for row in manifest_rows:
            if str(row.get("status", "")) not in ("ok", "ok_zero_trade"):
                continue
            s = row.get("strategy", "")
            if per_strat.get(s, 0) == 0:
                no_cand.append(s)
        (out_root / "no_candidate_strategies.txt").write_text(
            "\n".join(no_cand) if no_cand else "(none)\n", encoding="utf-8"
        )

        if not args.no_post_analysis:
            _run_post_analysis(args, out_root, manifest_rows)

    print(f"Wrote manifest -> {manifest_csv}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
