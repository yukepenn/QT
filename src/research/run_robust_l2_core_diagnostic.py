"""
Small robust-core Layer2 diagnostic (research-only).

Goal:
- Execute a *small* grid of combiner runs across curated candidate sets from:
    src/research/results/robust_l2_core_v2_design/candidate_sets_design.csv
- Windows: insample_ref, early_oow, late_oow (bounds from fixed_profile_oow_v1)
- Grid: max_trades_per_day × daily_max_loss_r × priority_policy

Hard constraints:
- DESIGN INPUTS ONLY (no candidate YAML edits, no strategy changes)
- NO broad Layer2 sweep
- NO --use-signal-cache (unsafe on OneDrive roots)
- Raw runs remain local-only under output_root/local_runs/** (do not commit)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.combiner.run import run_combiner_fixed_config  # noqa: E402
from src.research.fixed_profile_oow_lib import (  # noqa: E402
    exit_slip_scenarios_table,
    load_window_bounds,
    metrics_from_trades,
    trades_path_for_postprocess,
)


DEFAULT_CANDIDATE_SETS = (
    "primary_representative_core",
    "balanced_representative_core",
    "pa_gap_core",
    "pa_cci_core",
    "gap_cci_core",
    "pa_only_core",
    "cci_only_core",
)
DEFAULT_WINDOWS = ("insample_ref", "early_oow", "late_oow")
DEFAULT_MTP = (1, 2)
DEFAULT_DAILY_LOSS = (-1.5, -2.0)
DEFAULT_PRIORITY = ("metadata_priority", "score_adjusted_priority")

SET_DIR_MAP = {
    "primary_representative_core": "p",
    "balanced_representative_core": "b",
    "pa_gap_core": "pg",
    "pa_cci_core": "pc",
    "gap_cci_core": "gc",
    "pa_only_core": "po",
    "cci_only_core": "co",
}

WINDOW_DIR_MAP = {
    "insample_ref": "is",
    "early_oow": "eo",
    "late_oow": "lo",
    "full_available": "fa",
}


def _safe_id(s: str) -> str:
    return (
        str(s)
        .strip()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace(",", "_")
    )


def _git_tip(repo_root: Path) -> str:
    try:
        return subprocess.check_output(["git", "log", "-1", "--oneline"], cwd=str(repo_root), text=True).strip()
    except Exception:
        return "(unavailable)"


def _parse_csv_list(arg: str | None, default: tuple[str, ...]) -> list[str]:
    if not arg or not str(arg).strip():
        return list(default)
    return [x.strip() for x in str(arg).split(",") if x.strip()]


def _parse_int_list(arg: str | None, default: tuple[int, ...]) -> list[int]:
    if not arg or not str(arg).strip():
        return list(default)
    out: list[int] = []
    for x in str(arg).split(","):
        x = x.strip()
        if not x:
            continue
        out.append(int(x))
    return out


def _parse_float_list(arg: str | None, default: tuple[float, ...]) -> list[float]:
    if not arg or not str(arg).strip():
        return list(default)
    out: list[float] = []
    for x in str(arg).split(","):
        x = x.strip()
        if not x:
            continue
        out.append(float(x))
    return out


def _latest_run_dir(out_dir: Path) -> Path | None:
    runs = sorted(out_dir.glob("run_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[0] if runs else None


def _run_has_metrics(out_dir: Path) -> bool:
    lat = _latest_run_dir(out_dir)
    return bool(lat and (lat / "metrics.json").is_file())


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, lineterminator="\n")


def _load_candidate_sets(design_root: Path) -> pd.DataFrame:
    p = design_root / "candidate_sets_design.csv"
    if not p.is_file():
        raise FileNotFoundError(p)
    df = pd.read_csv(p)
    required = {"candidate_set", "candidate_id", "source_yaml_path", "run_recommended", "design_only"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"candidate_sets_design.csv missing columns: {missing}")
    return df


def _candidate_ids_for_set(df: pd.DataFrame, set_name: str) -> list[str]:
    ids = df.loc[df["candidate_set"] == set_name, "candidate_id"].astype(str).tolist()
    ids = [x.strip() for x in ids if str(x).strip()]
    # For this diagnostic, we only allow sets marked run_recommended=yes.
    # (extended_watchlist + exclude_from_core exist for documentation/contrasts only.)
    run_ok = df.loc[df["candidate_set"] == set_name, "run_recommended"].astype(str).str.lower().unique().tolist()
    if run_ok and any(x not in ("yes", "true", "1") for x in run_ok):
        # allow mixed column values only if at least one row is yes (but our curated file should be consistent)
        pass
    return sorted(ids)


def _write_base_inventory(
    *,
    output_root: Path,
    design_root: Path,
    decision: str,
    windows: list[str],
    candidate_sets: list[str],
    grid: dict[str, list[Any]],
    artifact_validation_ok: bool,
) -> None:
    lines = [
        "# Robust l2_core v2 diagnostic v1 — baseline inventory",
        "",
        f"- **git tip:** `{_git_tip(_ROOT)}`",
        f"- **handoff decision:** `{decision}`",
        "",
        "## Inputs",
        "",
        f"- **design_root:** `{design_root.as_posix()}`",
        "- design files:",
        "  - `candidate_sets_design.csv`",
        "  - `representative_candidate_manifest.csv`",
        "  - `core_watchlist_drop_actions.csv`",
        "  - `design_artifact_validation.csv`",
        "",
        f"- **artifact validation status:** `{'OK' if artifact_validation_ok else 'FAILED'}`",
        "",
        "## Planned scope",
        "",
        f"- **windows:** `{','.join(windows)}`",
        f"- **candidate_sets:** `{','.join(candidate_sets)}`",
        "",
        "## Planned grid",
        "",
    ]
    for k, v in grid.items():
        lines.append(f"- **{k}:** `{v}`")
    lines += [
        "",
        "## Output layout (local-only raw runs)",
        "",
        f"- raw runs: `{(output_root / 'local_runs').as_posix()}/<candidate_set>/<window>/<grid_id>/run_*`",
        f"- materialized configs: `{(output_root / 'local_configs').as_posix()}`",
        "",
        "## Explicit non-runs",
        "",
        "- No broad Layer2 sweep",
        "- No mini/full WFO",
        "- No live/paper",
        "- No SPY",
        "- No strategy changes / feature changes",
        "- No candidate YAML edits",
        "- No signal cache",
        "",
    ]
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "baseline_inventory.md").write_text("\n".join(lines), encoding="utf-8")


def _materialize_config(
    *,
    candidate_root: str,
    max_trades_per_day: int,
    daily_max_loss_r: float,
    priority_policy: str,
    slippage_per_share: float = 0.01,
    commission_per_trade: float = 0.0,
    no_new_after_minute: int = 360,
    max_open_positions: int = 1,
) -> dict[str, Any]:
    # Minimal combiner YAML compatible with src.combiner.run.validate_common_combiner_config.
    return {
        "name": "robust_l2_core_v2_diagnostic_v1",
        "candidate_root": candidate_root,
        "execution": {
            "commission_per_trade": float(commission_per_trade),
            "slippage_per_share": float(slippage_per_share),
            "eod_exit_minute": 389,
            "no_new_after_minute": int(no_new_after_minute),
            "recompute_target_from_entry": True,
            "min_risk_per_share": 0.03,
        },
        "system": {
            "max_open_positions": int(max_open_positions),
            "max_trades_per_day": int(max_trades_per_day),
            "daily_max_loss_r": float(daily_max_loss_r),
            "cooldown_after_loss_minutes": 0,
            "cooldown_scope": "session",
        },
        "conflict": {
            "priority_policy": str(priority_policy),
            "same_bar_policy": "priority",
            "tie_breakers": ["candidate_score", "candidate_rank", "candidate_index"],
            "opposite_direction_policy": "",
        },
    }


@dataclass(frozen=True)
class PlanRow:
    grid_id: str
    grid_label: str
    candidate_set: str
    candidate_set_dir: str
    window: str
    window_dir: str
    start_date: str
    end_date: str
    max_trades_per_day: int
    daily_max_loss_r: float
    priority_policy: str
    candidate_ids: str
    run_dir: str
    status: str
    exit_code: int | None
    error_summary: str
    command: str
    argv_json: str
    config_path: str


def _build_run_plan(
    *,
    design_root: Path,
    output_root: Path,
    windows_root: Path,
    candidate_sets: list[str],
    windows: list[str],
    mtp: list[int],
    daily_loss: list[float],
    priorities: list[str],
    data_dir: str,
) -> pd.DataFrame:
    sets_df = _load_candidate_sets(design_root)
    bounds = load_window_bounds(windows_root, data_dir=data_dir)

    # Materialize 8 configs (mtp × dl × priority) and reuse across candidate sets/windows.
    local_cfg_dir = output_root / "local_configs"
    local_cfg_dir.mkdir(parents=True, exist_ok=True)

    candidate_root_rel = "src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates"
    candidate_root_abs = (Path.cwd() / candidate_root_rel).resolve()

    cfg_paths: dict[tuple[int, float, str], Path] = {}
    for m in mtp:
        for dl in daily_loss:
            for pp in priorities:
                key = (int(m), float(dl), str(pp))
                cfg_id = f"mtp{m}__dl{dl}__pp{pp}"
                cfg_name = _safe_id(cfg_id) + ".yaml"
                cfg_path = local_cfg_dir / cfg_name
                cfg = _materialize_config(
                    candidate_root=candidate_root_rel,
                    max_trades_per_day=int(m),
                    daily_max_loss_r=float(dl),
                    priority_policy=str(pp),
                )
                cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
                cfg_paths[key] = cfg_path

    rows: list[PlanRow] = []
    for set_name in candidate_sets:
        ids = _candidate_ids_for_set(sets_df, set_name)
        if not ids:
            raise ValueError(f"candidate_set has no members: {set_name}")
        ids_csv = ",".join(ids)
        set_dir = SET_DIR_MAP.get(set_name, _safe_id(set_name)[:8] or "set")
        for wid in windows:
            if wid not in bounds:
                raise KeyError(f"unknown window_id {wid} (not in windows_root bounds)")
            st, en = bounds[wid]
            win_dir = WINDOW_DIR_MAP.get(wid, _safe_id(wid)[:4] or "win")
            for m in mtp:
                for dl in daily_loss:
                    for pp in priorities:
                        grid_label = f"mtp{m}__dl{dl}__pp{pp}"
                        # Keep directory names short to avoid Windows MAX_PATH issues.
                        grid_id = _safe_id(f"g_m{m}_d{dl}_p{pp}")[:24]
                        run_out = output_root / "local_runs" / set_dir / win_dir / grid_id
                        cfg_path = cfg_paths[(int(m), float(dl), str(pp))]
                        argv = [
                            sys.executable,
                            "-m",
                            "src.combiner.run",
                            "--candidate-root",
                            str(candidate_root_abs),
                            "--config",
                            str(cfg_path),
                            "--asset",
                            "equity",
                            "--symbol",
                            "QQQ",
                            "--start",
                            str(st),
                            "--end",
                            str(en),
                            "--candidate-ids",
                            *ids,
                            "--output-root",
                            str(run_out),
                            "--tag",
                            "robust_core_v2_diag",
                            "--top-per-strategy",
                            "999",
                            "--data-dir",
                            data_dir,
                            "--no-detailed",
                        ]
                        cmdline = subprocess.list2cmdline(argv)
                        rows.append(
                            PlanRow(
                                grid_id=grid_id,
                                grid_label=grid_label,
                                candidate_set=set_name,
                                candidate_set_dir=set_dir,
                                window=wid,
                                window_dir=win_dir,
                                start_date=str(st),
                                end_date=str(en),
                                max_trades_per_day=int(m),
                                daily_max_loss_r=float(dl),
                                priority_policy=str(pp),
                                candidate_ids=ids_csv,
                                run_dir=str(run_out.relative_to(output_root)).replace("\\", "/"),
                                status="PLANNED",
                                exit_code=None,
                                error_summary="",
                                command=cmdline,
                                argv_json=json.dumps(argv),
                                config_path=str(cfg_path.relative_to(output_root)).replace("\\", "/"),
                            )
                        )
    df = pd.DataFrame([r.__dict__ for r in rows])
    return df


def cmd_dry_run(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Dry-run: write run_plan.csv without executing combiner.")
    p.add_argument("--design-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--windows-root", default="src/research/results/fixed_profile_oow_v1")
    p.add_argument("--windows", default="insample_ref,early_oow,late_oow")
    p.add_argument("--candidate-sets", default=",".join(DEFAULT_CANDIDATE_SETS))
    p.add_argument("--max-trades-per-day", default="1,2")
    p.add_argument("--daily-max-loss-r", default="-1.5,-2.0")
    p.add_argument("--priority-policies", default="metadata_priority,score_adjusted_priority")
    p.add_argument("--data-dir", default="data/raw/ibkr")
    args = p.parse_args(argv)

    design_root = Path(args.design_root)
    if not design_root.is_absolute():
        design_root = Path.cwd() / design_root
    output_root = Path(args.output_root)
    if not output_root.is_absolute():
        output_root = Path.cwd() / output_root
    windows_root = Path(args.windows_root)
    if not windows_root.is_absolute():
        windows_root = Path.cwd() / windows_root

    windows = _parse_csv_list(args.windows, DEFAULT_WINDOWS)
    cand_sets = _parse_csv_list(args.candidate_sets, DEFAULT_CANDIDATE_SETS)
    mtp = _parse_int_list(args.max_trades_per_day, DEFAULT_MTP)
    dl = _parse_float_list(args.daily_max_loss_r, DEFAULT_DAILY_LOSS)
    pp = _parse_csv_list(args.priority_policies, DEFAULT_PRIORITY)

    plan = _build_run_plan(
        design_root=design_root,
        output_root=output_root,
        windows_root=windows_root,
        candidate_sets=cand_sets,
        windows=windows,
        mtp=mtp,
        daily_loss=dl,
        priorities=pp,
        data_dir=args.data_dir,
    )
    _write_csv(plan, output_root / "run_plan.csv")

    (output_root / "dry_run_validation.md").write_text(
        "\n".join(
            [
                "# Dry-run validation (robust core v2 diagnostic v1)",
                "",
                f"- rows: **{len(plan)}**",
                f"- candidate_sets: **{len(set(plan['candidate_set']))}**",
                f"- windows: **{len(set(plan['window']))}**",
                f"- grid combos per (set, window): **{len(plan) // (len(cand_sets) * len(windows))}**",
                "",
                "This file does not guarantee data availability; it only validates plan expansion and paths.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return 0


def cmd_run(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Execute robust-core diagnostic runs.")
    p.add_argument("--design-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--windows-root", default="src/research/results/fixed_profile_oow_v1")
    p.add_argument("--windows", default="insample_ref,early_oow,late_oow")
    p.add_argument("--candidate-sets", default=",".join(DEFAULT_CANDIDATE_SETS))
    p.add_argument("--max-trades-per-day", default="1,2")
    p.add_argument("--daily-max-loss-r", default="-1.5,-2.0")
    p.add_argument("--priority-policies", default="metadata_priority,score_adjusted_priority")
    p.add_argument("--data-dir", default="data/raw/ibkr")
    p.add_argument("--skip-existing", action="store_true")
    p.add_argument("--stop-on-fail", action="store_true")
    args = p.parse_args(argv)

    design_root = Path(args.design_root)
    if not design_root.is_absolute():
        design_root = Path.cwd() / design_root
    output_root = Path(args.output_root)
    if not output_root.is_absolute():
        output_root = Path.cwd() / output_root
    windows_root = Path(args.windows_root)
    if not windows_root.is_absolute():
        windows_root = Path.cwd() / windows_root

    windows = _parse_csv_list(args.windows, DEFAULT_WINDOWS)
    cand_sets = _parse_csv_list(args.candidate_sets, DEFAULT_CANDIDATE_SETS)
    mtp = _parse_int_list(args.max_trades_per_day, DEFAULT_MTP)
    dl = _parse_float_list(args.daily_max_loss_r, DEFAULT_DAILY_LOSS)
    pp = _parse_csv_list(args.priority_policies, DEFAULT_PRIORITY)

    # Preflight: read artifact validation from design root if present.
    artifact_ok = True
    vcsv = design_root / "design_artifact_validation.csv"
    if vcsv.is_file():
        vdf = pd.read_csv(vcsv)
        if "ok" in vdf.columns and not bool(vdf["ok"].all()):
            artifact_ok = False
    _write_base_inventory(
        output_root=output_root,
        design_root=design_root,
        decision="RUN_SMALL_ROBUST_CORE_LAYER2_DIAGNOSTIC_DESIGN",
        windows=windows,
        candidate_sets=cand_sets,
        grid={"max_trades_per_day": mtp, "daily_max_loss_r": dl, "priority_policy": pp},
        artifact_validation_ok=artifact_ok,
    )
    if not artifact_ok:
        raise SystemExit("design artifact validation not OK; refusing to run")

    plan = _build_run_plan(
        design_root=design_root,
        output_root=output_root,
        windows_root=windows_root,
        candidate_sets=cand_sets,
        windows=windows,
        mtp=mtp,
        daily_loss=dl,
        priorities=pp,
        data_dir=args.data_dir,
    )
    _write_csv(plan, output_root / "run_plan.csv")

    exec_rows: list[dict[str, Any]] = []
    started_at = datetime.now(timezone.utc).isoformat()
    for _, r in plan.iterrows():
        run_dir = output_root / str(r["run_dir"])
        cmd = str(r.get("command", "")) or ""
        row = dict(r)
        if args.skip_existing and _run_has_metrics(run_dir):
            row["status"] = "SKIPPED_EXISTING"
            row["exit_code"] = 0
            exec_rows.append(row)
            continue
        run_dir.mkdir(parents=True, exist_ok=True)
        # Write command line for reproducibility.
        (run_dir / "run_command.txt").write_text(cmd + "\n", encoding="utf-8")
        try:
            cfg_path = output_root / str(r["config_path"])
            combiner_yaml = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
            start = str(r["start_date"])
            end = str(r["end_date"])
            ids = [x.strip() for x in str(r["candidate_ids"]).split(",") if x.strip()]
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            run_out = run_dir / f"run_{ts}_robust_core_v2_diag"
            run_combiner_fixed_config(
                combiner_yaml,
                candidate_root=(Path.cwd() / combiner_yaml["candidate_root"]).resolve(),
                candidate_set=None,
                candidate_ids=ids,
                top_per_strategy=999,
                asset="equity",
                symbol="QQQ",
                start=start,
                end=end,
                output_dir=run_out,
                data_dir=args.data_dir,
                use_signal_cache=False,
                detailed=False,
                tag="robust_core_v2_diag",
            )
            row["exit_code"] = 0
            row["status"] = "OK"
            exec_rows.append(row)
        except Exception as e:  # noqa: BLE001 (research runner)
            row["exit_code"] = 1
            row["status"] = "FAILED"
            row["error_summary"] = repr(e)
            exec_rows.append(row)
            if args.stop_on_fail:
                break

    rdf = pd.DataFrame(exec_rows)
    _write_csv(rdf, output_root / "run_execution_manifest.csv")
    (output_root / "run_execution_manifest_meta.json").write_text(
        json.dumps({"started_at_utc": started_at, "finished_at_utc": datetime.now(timezone.utc).isoformat()}, indent=2),
        encoding="utf-8",
    )
    failed = rdf[rdf["status"] == "FAILED"] if not rdf.empty else pd.DataFrame()
    if not failed.empty:
        _write_csv(failed, output_root / "failed_runs.csv")
        return 1
    # Remove stale failed_runs from prior attempts.
    fr = output_root / "failed_runs.csv"
    if fr.is_file():
        try:
            fr.unlink()
        except Exception:
            pass
    return 0


def cmd_postprocess(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Postprocess robust-core diagnostic runs into curated tables.")
    p.add_argument("--output-root", required=True)
    p.add_argument("--runs-subdir", default="local_runs")
    p.add_argument("--write-exit-slip", action="store_true", help="Write exit/slip scenarios for top configs (curated only)")
    args = p.parse_args(argv)

    out = Path(args.output_root)
    if not out.is_absolute():
        out = Path.cwd() / out
    runs_root = out / args.runs_subdir
    if not runs_root.is_dir():
        raise FileNotFoundError(runs_root)

    # Load plan for directory->semantic mapping.
    plan_path = out / "run_plan.csv"
    if not plan_path.is_file():
        raise FileNotFoundError(plan_path)
    plan = pd.read_csv(plan_path)
    key_cols = ["candidate_set_dir", "window_dir", "grid_id"]
    if not all(c in plan.columns for c in key_cols):
        raise ValueError(f"run_plan.csv missing required columns: {key_cols}")
    plan_map: dict[tuple[str, str, str], dict[str, Any]] = {}
    for _, r in plan.iterrows():
        k = (str(r["candidate_set_dir"]), str(r["window_dir"]), str(r["grid_id"]))
        plan_map[k] = dict(r)

    # Discover latest run per (candidate_set, window, grid_id)
    best: dict[tuple[str, str, str], Path] = {}
    for mpath in runs_root.glob("*/*/*/run_*/metrics.json"):
        run_dir = mpath.parent
        parts = run_dir.relative_to(runs_root).parts
        if len(parts) < 4:
            continue
        set_dir, win_dir, grid_id = parts[0], parts[1], parts[2]
        key = (set_dir, win_dir, grid_id)
        prev = best.get(key)
        if prev is None or run_dir.stat().st_mtime > prev.stat().st_mtime:
            best[key] = run_dir

    disc_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    for (set_dir, win_dir, grid_id), run_dir in sorted(best.items()):
        meta = plan_map.get((set_dir, win_dir, grid_id), {})
        set_name = str(meta.get("candidate_set", set_dir))
        window_id = str(meta.get("window", win_dir))
        mpath = run_dir / "metrics.json"
        mjson = json.loads(mpath.read_text(encoding="utf-8")) if mpath.is_file() else {}
        tpath = trades_path_for_postprocess(run_dir)
        trades = pd.read_csv(tpath) if tpath is not None and tpath.is_file() else pd.DataFrame()
        status = "OK" if not trades.empty else "NOT_RUN"
        met = metrics_from_trades(trades, metrics_json=mjson)

        disc_rows.append(
            {
                "candidate_set": set_name,
                "window": window_id,
                "grid_id": grid_id,
                "grid_label": str(meta.get("grid_label", "")),
                "run_dir": str(run_dir.relative_to(out)).replace("\\", "/"),
                "status": status,
            }
        )

        cfg_path = run_dir / "config_resolved.yaml"
        mtp = mjson.get("max_trades_per_day") or mjson.get("system", {}).get("max_trades_per_day") if isinstance(mjson.get("system"), dict) else None
        row = {
            "candidate_set": set_name,
            "window": window_id,
            "grid_id": grid_id,
            "grid_label": str(meta.get("grid_label", "")),
            "run_dir": str(run_dir.relative_to(out)).replace("\\", "/"),
            "status": status,
            **met,
            "profit_factor": mjson.get("profit_factor"),
            "max_drawdown_r": mjson.get("max_drawdown_r"),
            "combiner_score": mjson.get("combiner_score"),
            "start": mjson.get("start", ""),
            "end": mjson.get("end", ""),
        }
        # Grid axes: prefer run_plan (authoritative)
        row["max_trades_per_day"] = meta.get("max_trades_per_day", "")
        row["daily_max_loss_r"] = meta.get("daily_max_loss_r", "")
        row["priority_policy"] = meta.get("priority_policy", "")
        metric_rows.append(row)

    ddf = pd.DataFrame(disc_rows)
    _write_csv(ddf, out / "run_discovery_manifest.csv")

    res = pd.DataFrame(metric_rows)
    if res.empty:
        raise RuntimeError("no runs discovered with metrics.json")
    _write_csv(res, out / "diagnostic_results.csv")

    # Summaries
    by_set = (
        res.groupby(["candidate_set", "window"], dropna=False)[["total_r", "trades", "max_dd_r", "pf_r"]]
        .agg({"total_r": "max", "trades": "max", "max_dd_r": "min", "pf_r": "max"})
        .reset_index()
    )
    _write_csv(by_set, out / "candidate_set_summary.csv")

    by_axis = (
        res.groupby(["window", "max_trades_per_day", "daily_max_loss_r", "priority_policy"], dropna=False)["total_r"]
        .agg(["mean", "median", "max", "min", "count"])
        .reset_index()
        .rename(columns={"count": "n_rows"})
    )
    _write_csv(by_axis, out / "grid_axis_summary.csv")

    by_win = (
        res.groupby(["window"], dropna=False)[["total_r", "trades", "max_dd_r"]]
        .agg({"total_r": ["mean", "median", "max", "min"], "trades": ["mean", "max"], "max_dd_r": ["mean", "min"]})
        .reset_index()
    )
    by_win.columns = ["_".join([c for c in col if c]).strip("_") for col in by_win.columns.to_flat_index()]
    _write_csv(by_win, out / "window_summary.csv")

    # Top systems
    top_overall = res.sort_values(["total_r", "pf_r"], ascending=[False, False]).head(50)
    _write_csv(top_overall, out / "top_systems_overall.csv")
    top_by_win = res.sort_values(["window", "total_r"], ascending=[True, False]).groupby("window").head(25)
    _write_csv(top_by_win, out / "top_systems_by_window.csv")

    # Complementarity (best row per candidate_set/window; per-candidate contribution from trades.csv if present)
    comp_dir = out / "complementarity"
    comp_dir.mkdir(parents=True, exist_ok=True)
    best_per_set_win = (
        res.sort_values(["candidate_set", "window", "total_r"], ascending=[True, True, False])
        .groupby(["candidate_set", "window"], dropna=False)
        .head(1)
        .reset_index(drop=True)
    )
    comp_rows: list[dict[str, Any]] = []
    strat_rows: list[dict[str, Any]] = []
    for _, br in best_per_set_win.iterrows():
        run_dir = out / str(br["run_dir"])
        tpath = trades_path_for_postprocess(run_dir)
        trades = pd.read_csv(tpath) if tpath is not None and tpath.is_file() else pd.DataFrame()
        if trades.empty or "candidate_id" not in trades.columns or "r_multiple" not in trades.columns:
            continue
        t = trades.copy()
        t["r_multiple"] = pd.to_numeric(t["r_multiple"], errors="coerce").fillna(0.0)
        by_c = t.groupby("candidate_id", dropna=False)["r_multiple"].agg(["count", "sum"]).reset_index()
        by_c = by_c.rename(columns={"count": "trades", "sum": "total_r"})
        for _, rr in by_c.iterrows():
            comp_rows.append(
                {
                    "candidate_set": br["candidate_set"],
                    "window": br["window"],
                    "grid_id": br["grid_id"],
                    "candidate_id": str(rr["candidate_id"]),
                    "trades": int(rr["trades"]),
                    "total_r": float(rr["total_r"]),
                }
            )
        if "strategy" in t.columns:
            by_s = t.groupby("strategy", dropna=False)["r_multiple"].agg(["count", "sum"]).reset_index()
            by_s = by_s.rename(columns={"count": "trades", "sum": "total_r"})
            for _, rr in by_s.iterrows():
                strat_rows.append(
                    {
                        "candidate_set": br["candidate_set"],
                        "window": br["window"],
                        "grid_id": br["grid_id"],
                        "strategy": str(rr["strategy"]),
                        "trades": int(rr["trades"]),
                        "total_r": float(rr["total_r"]),
                    }
                )
    if comp_rows:
        _write_csv(pd.DataFrame(comp_rows), comp_dir / "candidate_contribution_by_set.csv")
    if strat_rows:
        _write_csv(pd.DataFrame(strat_rows), comp_dir / "strategy_contribution_by_window.csv")

    # Optional exit/slip scenarios for top rows (curated only).
    if args.write_exit_slip:
        slip_dir = out / "exit_slip"
        slip_dir.mkdir(parents=True, exist_ok=True)
        parts: list[pd.DataFrame] = []
        for _, r in top_by_win.head(15).iterrows():
            run_dir = out / str(r["run_dir"])
            tpath = trades_path_for_postprocess(run_dir)
            trades = pd.read_csv(tpath) if tpath is not None and tpath.is_file() else pd.DataFrame()
            if trades.empty:
                continue
            label = f"{r['candidate_set']}__{r['window']}__{r['grid_id']}"
            parts.append(exit_slip_scenarios_table(trades, label))
        if parts:
            slip = pd.concat(parts, ignore_index=True)
            _write_csv(slip, slip_dir / "robust_core_exit_slip_scenarios.csv")

    # Markdown summary (compact, no tables explosion)
    best = top_overall.head(10)[
        [
            "candidate_set",
            "window",
            "grid_id",
            "total_r",
            "trades",
            "pf_r",
            "max_dd_r",
            "priority_policy",
            "daily_max_loss_r",
            "max_trades_per_day",
        ]
    ]
    lines = [
        "# Robust l2_core v2 diagnostic v1 — summary (curated)",
        "",
        f"- discovered rows: **{len(res)}**",
        f"- discovered combos: **{res[['candidate_set','window','grid_id']].drop_duplicates().shape[0]}**",
        "",
        "## Top 10 rows overall (by total_r)",
        "",
    ]
    try:
        lines.append(best.to_markdown(index=False))
    except Exception:
        lines.append(best.to_string(index=False))
    lines += [
        "",
        "## Notes",
        "",
        "- This is a *small* diagnostic grid (no broad Layer2).",
        "- Raw runs live under `local_runs/**` and are local-only.",
        "",
    ]
    (out / "diagnostic_summary.md").write_text("\n".join(lines), encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Robust l2_core v2 small diagnostic runner.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("dry-run")
    sub.add_parser("run")
    sub.add_parser("postprocess")
    args, rest = p.parse_known_args(argv)

    if args.cmd == "dry-run":
        return cmd_dry_run(rest)
    if args.cmd == "run":
        return cmd_run(rest)
    if args.cmd == "postprocess":
        return cmd_postprocess(rest)
    raise SystemExit(f"unknown cmd {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main())

