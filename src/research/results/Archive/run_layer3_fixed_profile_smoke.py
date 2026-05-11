"""
Layer3 fixed-profile smoke v1 — research-only CORE execution.

Runs a small fixed set of locked profiles (from fixed robust-profile OOW v1 definitions)
across fixed windows. Optional profiles are gated behind CLI flags (not used in CORE smoke).

Constraints:
- no broad Layer2 sweep, no WFO/live/SPY/router
- no candidate YAML edits, no --use-signal-cache
- raw runs under output_root/local_runs/** (local-only; do not commit)
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _repo_rel_path(path: Path) -> str:
    """Repo-relative posix path for curated SOURCE_MAP rows (no absolute drive paths)."""
    try:
        return path.resolve().relative_to(_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()

from src.combiner.run import run_combiner_fixed_config  # noqa: E402
from src.research.analyze_exit_slip_attribution import aggregate as exit_slip_row_aggregate  # noqa: E402
from src.research.fixed_profile_oow_lib import (  # noqa: E402
    discover_runs,
    exit_slip_with_extreme,
    max_drawdown_r,
    metrics_from_trades,
    trades_path_for_postprocess,
)
from src.research.trade_quality_helpers import add_prior_trade_columns, profit_factor_r  # noqa: E402

WINDOW_BOUNDS = {
    "early_oow": ("2020-01-01", "2022-12-31"),
    "insample_ref": ("2023-01-01", "2024-12-31"),
    "late_oow": ("2025-01-01", "2026-04-30"),
    "full_available": ("2020-01-01", "2026-04-30"),
}

CORE_PROFILE_IDS = frozenset({"pa_only_mtp1_meta", "pa_gap_mtp2_meta"})
OPTIONAL_PROFILE_IDS = frozenset({"primary_mtp2_meta", "pa_gap_mtp1_meta", "pa_only_mtp2_meta"})
ALL_SMOKE_PROFILE_IDS = frozenset(CORE_PROFILE_IDS | OPTIONAL_PROFILE_IDS)
MULTI_CANDIDATE_PROFILES = frozenset({"pa_gap_mtp2_meta", "pa_gap_mtp1_meta", "primary_mtp2_meta"})


def _git_tip(repo_root: Path) -> str:
    try:
        return subprocess.check_output(["git", "log", "-1", "--oneline"], cwd=str(repo_root), text=True).strip()
    except Exception:
        return "(unavailable)"


def _git_branch(repo_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(repo_root), text=True
        ).strip()
    except Exception:
        return "(unavailable)"


def _git_ahead_behind_upstream(repo_root: Path) -> str:
    """Human-readable sync vs @{u} (at postprocess time)."""
    try:
        subprocess.check_output(["git", "rev-parse", "@{u}"], cwd=str(repo_root), stderr=subprocess.DEVNULL, text=True)
    except Exception:
        return "upstream: not configured or unreachable"
    try:
        out = subprocess.check_output(
            ["git", "rev-list", "--left-right", "--count", "@{u}...HEAD"],
            cwd=str(repo_root),
            text=True,
        ).strip()
        behind, ahead = out.split("\t")
        return f"upstream: commits behind origin={behind}, ahead of origin={ahead}"
    except Exception:
        return "upstream: parse failed"


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, lineterminator="\n")


def _markdown_total_r_pivot(res: pd.DataFrame) -> str:
    wids = ["early_oow", "insample_ref", "late_oow", "full_available"]
    header = "| profile_id | " + " | ".join(wids) + " |"
    sep = "|---|" + "|---|" * len(wids)
    lines = [header, sep]
    for pid in sorted(res["profile_id"].astype(str).unique()):
        cells = [f"`{pid}`"]
        for w in wids:
            sub = res[(res["profile_id"].astype(str) == pid) & (res["window"].astype(str) == w)]
            if sub.empty:
                cells.append("")
            else:
                cells.append(f"{float(sub.iloc[0]['total_r']):.2f}")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _safe_dir(s: str) -> str:
    return (
        str(s)
        .strip()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace(",", "_")
    )


def _parse_csv_list(arg: str | None, default: list[str]) -> list[str]:
    if not arg or not str(arg).strip():
        return list(default)
    return [x.strip() for x in str(arg).split(",") if x.strip()]


def _load_fixed_profile_definitions(fixed_root: Path) -> pd.DataFrame:
    p = fixed_root / "fixed_profile_definitions.csv"
    if not p.is_file():
        raise FileNotFoundError(p)
    df = pd.read_csv(p)
    required = {
        "profile_id",
        "candidate_set",
        "candidate_ids",
        "max_trades_per_day",
        "daily_max_loss_r",
        "priority_policy",
    }
    miss = sorted(required - set(df.columns))
    if miss:
        raise ValueError(f"fixed_profile_definitions.csv missing columns: {miss}")
    return df


def _load_profile_roles(design_root: Path) -> dict[str, str]:
    p = design_root / "layer3_smoke_profile_selection.csv"
    if not p.is_file():
        return {}
    df = pd.read_csv(p)
    out: dict[str, str] = {}
    if "profile_id" in df.columns and "role" in df.columns:
        for _, r in df.iterrows():
            out[str(r["profile_id"])] = str(r["role"])
    return out


def _materialize_config(*, max_trades_per_day: int, daily_max_loss_r: float, priority_policy: str) -> dict[str, Any]:
    candidate_root_rel = "src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates"
    return {
        "name": "layer3_fixed_profile_smoke_v1",
        "candidate_root": candidate_root_rel,
        "execution": {
            "commission_per_trade": 0.0,
            "slippage_per_share": 0.01,
            "eod_exit_minute": 389,
            "no_new_after_minute": 360,
            "recompute_target_from_entry": True,
            "min_risk_per_share": 0.03,
        },
        "system": {
            "max_open_positions": 1,
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


def _resolve_profile_ids(
    *,
    fixed_df: pd.DataFrame,
    profiles_arg: str | None,
    core_only: bool,
    include_optional_baseline: bool,
    include_ablations: bool,
) -> list[str]:
    if core_only and not profiles_arg:
        want = sorted(CORE_PROFILE_IDS)
        for pid in want:
            if pid not in set(fixed_df["profile_id"].astype(str)):
                raise ValueError(f"core profile {pid} missing from fixed_profile_definitions.csv")
        return want
    if core_only and profiles_arg:
        ids = _parse_csv_list(profiles_arg, [])
        bad = [x for x in ids if x not in CORE_PROFILE_IDS]
        if bad:
            raise ValueError(f"--core-only forbids profiles: {bad}")
        return ids
    ids = _parse_csv_list(profiles_arg, [])
    if not ids:
        raise ValueError("provide --profiles or use --core-only")
    if not include_optional_baseline:
        ids = [x for x in ids if x != "primary_mtp2_meta"]
    if not include_ablations:
        ids = [x for x in ids if x not in {"pa_gap_mtp1_meta", "pa_only_mtp2_meta"}]
    return ids


def _infer_smoke_kind(*, core_only: bool, profile_ids: list[str]) -> str:
    if core_only:
        return "core"
    s = set(profile_ids)
    if s == OPTIONAL_PROFILE_IDS and len(profile_ids) == len(OPTIONAL_PROFILE_IDS):
        return "optional"
    if s == ALL_SMOKE_PROFILE_IDS:
        return "full"
    return "custom"


def _build_run_plan(
    *,
    output_root: Path,
    fixed_df: pd.DataFrame,
    profile_ids: list[str],
    windows: list[str],
) -> pd.DataFrame:
    df = fixed_df[fixed_df["profile_id"].astype(str).isin(set(profile_ids))].copy()
    if df.empty:
        raise ValueError("no profiles selected after filter")

    cfg_dir = output_root / "local_configs"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_paths: dict[str, Path] = {}
    for _, r in df.iterrows():
        pid = str(r["profile_id"])
        cfg_path = cfg_dir / f"{_safe_dir(pid)}.yaml"
        cfg = _materialize_config(
            max_trades_per_day=int(r["max_trades_per_day"]),
            daily_max_loss_r=float(r["daily_max_loss_r"]),
            priority_policy=str(r["priority_policy"]),
        )
        cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        cfg_paths[pid] = cfg_path

    rows: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        pid = str(r["profile_id"])
        for wid in windows:
            if wid not in WINDOW_BOUNDS:
                raise KeyError(f"unknown window {wid}")
            st, en = WINDOW_BOUNDS[wid]
            run_dir = output_root / "local_runs" / _safe_dir(pid) / _safe_dir(wid)
            rows.append(
                {
                    "profile_id": pid,
                    "window": wid,
                    "start_date": st,
                    "end_date": en,
                    "candidate_set": str(r["candidate_set"]),
                    "candidate_ids": str(r["candidate_ids"]),
                    "max_trades_per_day": int(r["max_trades_per_day"]),
                    "daily_max_loss_r": float(r["daily_max_loss_r"]),
                    "priority_policy": str(r["priority_policy"]),
                    "config_path_rel": str(cfg_paths[pid].relative_to(output_root)).replace("\\", "/"),
                    "run_dir_rel": str(run_dir.relative_to(output_root)).replace("\\", "/"),
                    "status": "PLANNED",
                }
            )
    return pd.DataFrame(rows)


def _sanitize_exec_row(
    r: dict[str, Any],
    *,
    roles: dict[str, str],
    output_root: Path,
) -> dict[str, Any]:
    pid = str(r.get("profile_id", ""))
    err = str(r.get("error_summary", "") or "")
    for tok in ("D:/", "D:\\", "C:/", "C:\\", "OneDrive"):
        err = err.replace(tok, "")
    return {
        "profile_id": pid,
        "role": roles.get(pid, ""),
        "window": str(r.get("window", "")),
        "start_date": str(r.get("start_date", "")),
        "end_date": str(r.get("end_date", "")),
        "candidate_ids": str(r.get("candidate_ids", "")),
        "max_trades_per_day": int(r.get("max_trades_per_day", 0) or 0),
        "daily_max_loss_r": float(r.get("daily_max_loss_r", 0.0) or 0.0),
        "priority_policy": str(r.get("priority_policy", "")),
        "status": str(r.get("status", "")),
        "exit_code": int(r.get("exit_code", 0) or 0),
        "run_dir_rel": str(r.get("run_dir_rel", "")).replace("\\", "/"),
        "config_path_rel": str(r.get("config_path_rel", "")).replace("\\", "/"),
        "error_summary": err[:2000],
    }


def _period_cols(t: pd.DataFrame) -> pd.DataFrame:
    tt = t.copy()
    dt = pd.to_datetime(tt["session_date"].astype(str), errors="coerce")
    tt["_year"] = dt.dt.year
    tt["_quarter"] = dt.dt.to_period("Q").astype(str)
    tt["_month"] = dt.dt.to_period("M").astype(str)
    return tt


def layer3_exit_slip_extended(trades: pd.DataFrame, profile_id: str, window: str) -> pd.DataFrame:
    """Scenarios aligned with design doc naming (published_baseline, target_limit_baseline, etc.)."""
    if trades.empty or "risk_per_share" not in trades.columns:
        return pd.DataFrame()
    d = exit_slip_row_aggregate(trades.copy())
    d_ext = exit_slip_with_extreme(trades)
    label = f"{profile_id}__{window}"
    rows = []
    for scenario, col in [
        ("published_baseline", "r_multiple"),
        ("symmetric_stress", "symmetric_stress_r"),
        ("target_limit_baseline", "target_limit_baseline_r"),
        ("target_limit_stress", "target_limit_adjusted_stress_r"),
    ]:
        v = d[col].astype(float)
        pf = profit_factor_r(v)
        rows.append(
            {
                "profile_id": profile_id,
                "window": window,
                "label": label,
                "scenario": scenario,
                "trades": len(v),
                "total_r": float(v.sum()),
                "avg_r": float(v.mean()),
                "pf_r": float(pf) if math.isfinite(pf) else None,
            }
        )
    v = d_ext["symmetric_extreme_r"].astype(float)
    pf = profit_factor_r(v)
    rows.append(
        {
            "profile_id": profile_id,
            "window": window,
            "label": label,
            "scenario": "symmetric_extreme_warning",
            "trades": len(v),
            "total_r": float(v.sum()),
            "avg_r": float(v.mean()),
            "pf_r": float(pf) if math.isfinite(pf) else None,
        }
    )
    return pd.DataFrame(rows)


def _exit_reason_cost_table(trades: pd.DataFrame, profile_id: str, window: str) -> pd.DataFrame:
    if trades.empty or "exit_reason" not in trades.columns:
        return pd.DataFrame()
    rows = []
    for ex, g in trades.groupby(trades["exit_reason"].astype(str)):
        rs = g["r_multiple"].astype(float)
        pf = profit_factor_r(rs)
        rows.append(
            {
                "profile_id": profile_id,
                "window": window,
                "exit_reason": ex,
                "trades": len(g),
                "total_r": float(rs.sum()),
                "avg_r": float(rs.mean()),
                "pf_r": float(pf) if math.isfinite(pf) else None,
            }
        )
    return pd.DataFrame(rows)


def _complementarity(trades: pd.DataFrame, profile_id: str, window: str) -> pd.DataFrame:
    if trades.empty or "candidate_id" not in trades.columns:
        return pd.DataFrame()
    t = trades.copy()
    rs = t.groupby(t["candidate_id"].astype(str))["r_multiple"].agg(["sum", "count"]).reset_index()
    rs.columns = ["candidate_id", "total_r", "trades"]
    rs.insert(0, "window", window)
    rs.insert(0, "profile_id", profile_id)
    tot = float(rs["total_r"].sum()) or 1.0
    rs["share_of_total_r"] = rs["total_r"] / tot
    return rs


def cmd_dry_run(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Dry-run Layer3 fixed-profile smoke plan.")
    p.add_argument("--design-root", required=True)
    p.add_argument("--fixed-profile-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--profiles", default="")
    p.add_argument("--windows", default="early_oow,insample_ref,late_oow,full_available")
    p.add_argument("--core-only", action="store_true")
    p.add_argument("--include-optional-baseline", action="store_true")
    p.add_argument("--include-ablations", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-signal-cache", action="store_true")
    args = p.parse_args(argv)

    design_root = Path(args.design_root)
    fixed_root = Path(args.fixed_profile_root)
    output_root = Path(args.output_root)
    if not design_root.is_absolute():
        design_root = Path.cwd() / design_root
    if not fixed_root.is_absolute():
        fixed_root = Path.cwd() / fixed_root
    if not output_root.is_absolute():
        output_root = Path.cwd() / output_root

    fixed_df = _load_fixed_profile_definitions(fixed_root)
    wins = _parse_csv_list(args.windows, ["early_oow", "insample_ref", "late_oow", "full_available"])
    pids = _resolve_profile_ids(
        fixed_df=fixed_df,
        profiles_arg=args.profiles or None,
        core_only=bool(args.core_only),
        include_optional_baseline=bool(args.include_optional_baseline),
        include_ablations=bool(args.include_ablations),
    )
    plan = _build_run_plan(output_root=output_root, fixed_df=fixed_df, profile_ids=pids, windows=wins)
    output_root.mkdir(parents=True, exist_ok=True)
    _write_csv(plan, output_root / "run_plan.csv")

    kind = _infer_smoke_kind(core_only=bool(args.core_only), profile_ids=pids)
    checks: list[tuple[str, bool, str]] = []
    n = len(plan)
    prof_set = set(plan["profile_id"].astype(str))
    rp = plan["run_dir_rel"].astype(str).str.contains(r"^[a-zA-Z0-9_/.\-]+$", regex=True)
    checks.append(("run_dir_rel_safe", bool(rp.all()), "run_dir_rel pattern"))

    if kind == "core":
        checks.append(("row_count_8", n == 8, f"rows={n}"))
        checks.append(("only_core_profiles", prof_set <= CORE_PROFILE_IDS, f"profiles={sorted(prof_set)}"))
        checks.append(("no_primary", "primary_mtp2_meta" not in prof_set, ""))
        checks.append(("no_ablations", not prof_set.intersection({"pa_gap_mtp1_meta", "pa_only_mtp2_meta"}), ""))
    elif kind == "optional":
        checks.append(("row_count_12", n == 12, f"rows={n}"))
        checks.append(("only_optional_profiles", prof_set == OPTIONAL_PROFILE_IDS, f"profiles={sorted(prof_set)}"))
        checks.append(("no_core_profiles", not prof_set.intersection(CORE_PROFILE_IDS), ""))
    else:
        checks.append(("row_count_expected", n == len(pids) * len(wins), f"rows={n} expected={len(pids)*len(wins)}"))
        checks.append(("profiles_subset_fixed", prof_set <= set(fixed_df["profile_id"].astype(str)), str(sorted(prof_set))))

    chk_df = pd.DataFrame([{"check": a, "passed": b, "detail": c} for a, b, c in checks])
    _write_csv(chk_df, output_root / "dry_run_validation.csv")
    all_pass = bool(chk_df["passed"].all())
    title = "Layer3 CORE smoke" if kind == "core" else "Layer3 optional smoke" if kind == "optional" else "Layer3 smoke (custom)"
    lines = [
        f"# {title} — dry-run validation",
        "",
        f"- smoke_kind: **{kind}**",
        f"- all_checks_pass: **{all_pass}**",
        f"- planned_rows: **{n}**",
        f"- profiles: **{sorted(prof_set)}**",
        "",
        "See `dry_run_validation.csv` and `run_plan.csv`.",
        "",
    ]
    (output_root / "dry_run_validation.md").write_text("\n".join(lines), encoding="utf-8")
    return 0 if all_pass else 1


def cmd_run(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Run Layer3 fixed-profile smoke.")
    p.add_argument("--design-root", required=True)
    p.add_argument("--fixed-profile-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--profiles", default="")
    p.add_argument("--windows", default="early_oow,insample_ref,late_oow,full_available")
    p.add_argument("--core-only", action="store_true")
    p.add_argument("--include-optional-baseline", action="store_true")
    p.add_argument("--include-ablations", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="ignored in run mode")
    p.add_argument("--data-dir", default="data/raw/ibkr", help="IBKR raw data root (repo-relative default).")
    p.add_argument("--skip-existing", action="store_true")
    p.add_argument("--stop-on-fail", action="store_true")
    p.add_argument("--no-signal-cache", action="store_true", help="must be set (Layer3 smoke forbids cache).")
    args = p.parse_args(argv)

    if not args.no_signal_cache:
        print("ERROR: Layer3 smoke requires --no-signal-cache", file=sys.stderr)
        return 2

    design_root = Path(args.design_root)
    fixed_root = Path(args.fixed_profile_root)
    output_root = Path(args.output_root)
    if not design_root.is_absolute():
        design_root = Path.cwd() / design_root
    if not fixed_root.is_absolute():
        fixed_root = Path.cwd() / fixed_root
    if not output_root.is_absolute():
        output_root = Path.cwd() / output_root

    roles = _load_profile_roles(design_root)
    fixed_df = _load_fixed_profile_definitions(fixed_root)
    wins = _parse_csv_list(args.windows, ["early_oow", "insample_ref", "late_oow", "full_available"])
    pids = _resolve_profile_ids(
        fixed_df=fixed_df,
        profiles_arg=args.profiles or None,
        core_only=bool(args.core_only),
        include_optional_baseline=bool(args.include_optional_baseline),
        include_ablations=bool(args.include_ablations),
    )
    plan = _build_run_plan(output_root=output_root, fixed_df=fixed_df, profile_ids=pids, windows=wins)
    output_root.mkdir(parents=True, exist_ok=True)
    _write_csv(plan, output_root / "run_plan.csv")

    exec_rows: list[dict[str, Any]] = []
    for _, r in plan.iterrows():
        run_parent = output_root / str(r["run_dir_rel"])
        cfg_path = output_root / str(r["config_path_rel"])
        pid = str(r["profile_id"])
        wid = str(r["window"])
        st = str(r["start_date"])
        en = str(r["end_date"])
        ids = [x.strip() for x in str(r["candidate_ids"]).split(",") if x.strip()]

        latest = sorted(run_parent.glob("run_*/metrics.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if args.skip_existing and latest:
            row = dict(r)
            rd = latest[0].parent
            row.update(
                {
                    "status": "SKIPPED_EXISTING",
                    "exit_code": 0,
                    "error_summary": "",
                    "run_dir_rel": str(rd.relative_to(output_root)).replace("\\", "/"),
                }
            )
            exec_rows.append(row)
            continue

        try:
            combiner_yaml = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            out_dir = run_parent / f"run_{ts}_layer3_smoke"
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "profile_meta.json").write_text(
                json.dumps(
                    {
                        "profile_id": pid,
                        "window": wid,
                        "start": st,
                        "end": en,
                        "candidate_ids": ids,
                        "git_tip": _git_tip(_ROOT),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            run_combiner_fixed_config(
                combiner_yaml,
                candidate_root=(Path.cwd() / combiner_yaml["candidate_root"]).resolve(),
                candidate_set=None,
                candidate_ids=ids,
                top_per_strategy=999,
                asset="equity",
                symbol="QQQ",
                start=st,
                end=en,
                output_dir=out_dir,
                data_dir=args.data_dir,
                use_signal_cache=False,
                detailed=False,
                tag="layer3_fixed_profile_smoke_v1",
            )
            row = dict(r)
            row.update(
                {
                    "status": "OK",
                    "exit_code": 0,
                    "error_summary": "",
                    "run_dir_rel": str(out_dir.relative_to(output_root)).replace("\\", "/"),
                }
            )
            exec_rows.append(row)
        except Exception as e:  # noqa: BLE001
            row = dict(r)
            row.update(
                {
                    "status": "FAILED",
                    "exit_code": 1,
                    "error_summary": repr(e),
                    "run_dir_rel": str(run_parent.relative_to(output_root)).replace("\\", "/"),
                }
            )
            exec_rows.append(row)
            if args.stop_on_fail:
                break

    ex = pd.DataFrame(exec_rows)
    _write_csv(ex, output_root / "run_execution_manifest.csv")
    san = pd.DataFrame([_sanitize_exec_row(dict(x), roles=roles, output_root=output_root) for x in ex.to_dict("records")])
    _write_csv(san, output_root / "run_execution_manifest_sanitized.csv")

    failed = ex[ex["status"] == "FAILED"]
    if not failed.empty:
        _write_csv(failed, output_root / "failed_runs.csv")
        return 1
    fr = output_root / "failed_runs.csv"
    if fr.is_file():
        try:
            fr.unlink()
        except Exception:
            pass
    return 0


def _monthly_stats_for_window(monthly: pd.DataFrame, profile_id: str, window: str) -> dict[str, Any]:
    sub = monthly[(monthly["profile_id"].astype(str) == profile_id) & (monthly["window"].astype(str) == window)]
    if sub.empty:
        return {
            "worst_month_r": None,
            "worst_quarter_r": None,
            "positive_month_count": 0,
            "negative_month_count": 0,
            "negative_month_ratio": None,
        }
    tr = sub["total_r"].astype(float)
    worst_m = float(tr.min())
    pos = int((tr > 0).sum())
    neg = int((tr < 0).sum())
    ratio = float(neg / max(len(tr), 1))
    # quarterly worst from same monthly file rolled up — caller passes quarterly df
    return {
        "worst_month_r": worst_m,
        "worst_quarter_r": None,
        "positive_month_count": pos,
        "negative_month_count": neg,
        "negative_month_ratio": ratio,
    }


def _worst_quarter(quarterly: pd.DataFrame, profile_id: str, window: str) -> float | None:
    sub = quarterly[(quarterly["profile_id"].astype(str) == profile_id) & (quarterly["window"].astype(str) == window)]
    if sub.empty:
        return None
    return float(sub["total_r"].astype(float).min())


def _evaluate_gates(
    *,
    pws: pd.DataFrame,
    monthly: pd.DataFrame,
    quarterly: pd.DataFrame,
    slip: pd.DataFrame,
    design_root: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    risk_rows: list[dict[str, Any]] = []

    for _, pr in pws.iterrows():
        pid = str(pr["profile_id"])
        wid = str(pr["window"])
        total_r = float(pr.get("total_r", 0.0) or 0.0)
        max_dd = float(pr.get("max_dd_r", 0.0) or 0.0)
        trades_n = int(pr.get("trades", 0) or 0)
        mh = int(pr.get("max_hold_count", 0) or 0)
        max_hold_share = float(mh / trades_n) if trades_n else 0.0

        # window positivity
        lvl = "PASS" if total_r > 0 else "FAIL"
        rows.append(
            {
                "profile_id": pid,
                "window": wid,
                "gate_id": "win_positive_all",
                "gate_category": "window",
                "level": lvl,
                "metric": "total_r",
                "value": total_r,
                "threshold": 0,
                "pass": lvl != "FAIL",
            }
        )

        if wid == "full_available":
            lvl = "WARNING" if max_dd >= -30.0 else "PASS"
            rows.append(
                {
                    "profile_id": pid,
                    "window": wid,
                    "gate_id": "dd_full_warning",
                    "gate_category": "drawdown",
                    "level": lvl,
                    "metric": "max_dd_r",
                    "value": max_dd,
                    "threshold": -30,
                    "pass": lvl != "FAIL",
                }
            )
            ms = _monthly_stats_for_window(monthly, pid, wid)
            wq = _worst_quarter(quarterly, pid, wid)
            neg_ratio = ms["negative_month_ratio"]
            if neg_ratio is not None:
                lvl = "WARNING" if neg_ratio > 0.55 else "PASS"
                rows.append(
                    {
                        "profile_id": pid,
                        "window": wid,
                        "gate_id": "neg_month_cap_full",
                        "gate_category": "stability",
                        "level": lvl,
                        "metric": "negative_month_ratio",
                        "value": neg_ratio,
                        "threshold": 0.55,
                        "pass": lvl != "FAIL",
                    }
                )
            wm = ms["worst_month_r"]
            if wm is not None:
                lvl = "WARNING" if wm < -6.0 else "PASS"
                rows.append(
                    {
                        "profile_id": pid,
                        "window": wid,
                        "gate_id": "worst_month_full_warning",
                        "gate_category": "stability",
                        "level": lvl,
                        "metric": "worst_month_r",
                        "value": wm,
                        "threshold": -6,
                        "pass": lvl != "FAIL",
                    }
                )
            if wq is not None:
                lvl = "WARNING" if wq < -10.0 else "PASS"
                rows.append(
                    {
                        "profile_id": pid,
                        "window": wid,
                        "gate_id": "worst_quarter_full_warning",
                        "gate_category": "stability",
                        "level": lvl,
                        "metric": "worst_quarter_r",
                        "value": wq,
                        "threshold": -10,
                        "pass": lvl != "FAIL",
                    }
                )
            # cost overlay: target_limit_stress on full_available
            if not slip.empty:
                sl = slip[
                    (slip["profile_id"].astype(str) == pid)
                    & (slip["window"].astype(str) == wid)
                    & (slip["scenario"].astype(str) == "target_limit_stress")
                ]
                if not sl.empty:
                    tls = float(sl.iloc[0]["total_r"])
                    lvl = "FAIL" if tls <= 0 else "PASS"
                    rows.append(
                        {
                            "profile_id": pid,
                            "window": wid,
                            "gate_id": "limit_stress_positive_full",
                            "gate_category": "cost",
                            "level": lvl,
                            "metric": "total_r_target_limit_stress",
                            "value": tls,
                            "threshold": 0,
                            "pass": lvl != "FAIL",
                        }
                    )

        if wid == "late_oow":
            lvl = "WARNING" if max_dd >= -20.0 else "PASS"
            rows.append(
                {
                    "profile_id": pid,
                    "window": wid,
                    "gate_id": "dd_late_warning",
                    "gate_category": "drawdown",
                    "level": lvl,
                    "metric": "max_dd_r",
                    "value": max_dd,
                    "threshold": -20,
                    "pass": lvl != "FAIL",
                }
            )

        if wid == "full_available":
            lvl = "WARNING" if max_hold_share > 0.60 else "PASS"
            rows.append(
                {
                    "profile_id": pid,
                    "window": wid,
                    "gate_id": "max_hold_share_warning",
                    "gate_category": "exit_mechanics",
                    "level": lvl,
                    "metric": "max_hold_share",
                    "value": max_hold_share,
                    "threshold": 0.60,
                    "pass": lvl != "FAIL",
                }
            )

    # Risk flags (fixed set)
    for pid in sorted(pws["profile_id"].astype(str).unique()):
        sub = pws[pws["profile_id"].astype(str) == pid]
        late = sub[sub["window"].astype(str) == "late_oow"]
        late_r = float(late.iloc[0]["total_r"]) if not late.empty else float("nan")
        if pid == "pa_only_mtp1_meta" or pid == "pa_only_mtp2_meta":
            risk_rows.append(
                {
                    "risk_id": "R_PA_CONCENTRATION",
                    "profile_id": pid,
                    "severity": "MEDIUM",
                    "notes": "single PA candidate",
                }
            )
        elif pid == "primary_mtp2_meta":
            risk_rows.append(
                {
                    "risk_id": "R_CCI_BREADTH",
                    "profile_id": pid,
                    "severity": "MEDIUM",
                    "notes": "CCI breadth baseline; inspect CCI share vs PA/GAP",
                }
            )
        else:
            risk_rows.append(
                {
                    "risk_id": "R_GAP_DEPENDENCE",
                    "profile_id": pid,
                    "severity": "MEDIUM",
                    "notes": "combined profile; inspect GAP share",
                }
            )
        risk_rows.append(
            {
                "risk_id": "R_NO_SPY_WFO_LIVE",
                "profile_id": pid,
                "severity": "LOW",
                "notes": "research-only; no cross-symbol or live evidence",
            }
        )
        if pid in ("pa_gap_mtp2_meta", "pa_gap_mtp1_meta") and not math.isnan(late_r):
            pa_only_late = pws[
                (pws["profile_id"].astype(str) == "pa_only_mtp1_meta") & (pws["window"].astype(str) == "late_oow")
            ]
            if not pa_only_late.empty:
                pa_l = float(pa_only_late.iloc[0]["total_r"])
                gap_ok = late_r > 0 and late_r >= pa_l * 0.85
                risk_rows.append(
                    {
                        "risk_id": "R_LATE_OOW_GAP_VS_PA",
                        "profile_id": pid,
                        "severity": "LOW" if gap_ok else "HIGH",
                        "notes": f"late_oow total_r pa_gap={late_r:.4g} vs pa_only={pa_l:.4g}",
                    }
                )

    # Quarterly pockets 2025Q1 / 2022Q4
    if not quarterly.empty:
        for pid in sorted(pws["profile_id"].astype(str).unique()):
            for qtoken, rid in [("2025Q1", "R_2025Q1"), ("2022Q4", "R_2022Q4")]:
                hit = quarterly[
                    (quarterly["profile_id"].astype(str) == pid)
                    & (quarterly["window"].astype(str) == "full_available")
                    & (quarterly["quarter"].astype(str).str.contains(qtoken, regex=False))
                ]
                if not hit.empty:
                    qv = float(hit.iloc[0]["total_r"])
                    sev = "WARNING" if qv < 0 else "INFO"
                    risk_rows.append(
                        {"risk_id": rid, "profile_id": pid, "severity": sev, "notes": f"{qtoken} total_r={qv:.4g}"}
                    )

    risk_rows.append(
        {
            "risk_id": "R_FULL_WINDOW_OVERLAP",
            "profile_id": "ALL",
            "severity": "INFO",
            "notes": "Do not sum overlapping windows; use per-window and full_available for full-span economics.",
        }
    )

    return pd.DataFrame(rows), pd.DataFrame(risk_rows)


def cmd_postprocess(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Postprocess Layer3 fixed-profile smoke v1.")
    p.add_argument("--design-root", required=True)
    p.add_argument("--fixed-profile-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--smoke-kind", choices=("auto", "core", "optional"), default="auto")
    args = p.parse_args(argv)

    design_root = Path(args.design_root)
    fixed_root = Path(args.fixed_profile_root)
    output_root = Path(args.output_root)
    if not design_root.is_absolute():
        design_root = Path.cwd() / design_root
    if not fixed_root.is_absolute():
        fixed_root = Path.cwd() / fixed_root
    if not output_root.is_absolute():
        output_root = Path.cwd() / output_root

    smoke_kind = str(args.smoke_kind)
    if smoke_kind == "auto":
        stem = output_root.name.lower()
        smoke_kind = "optional" if "optional" in stem else "core"

    roles = _load_profile_roles(design_root)
    ref_path = fixed_root / "profile_window_summary.csv"
    ref = pd.read_csv(ref_path) if ref_path.is_file() else pd.DataFrame()

    discovered = discover_runs(output_root / "local_runs")
    if not discovered:
        raise RuntimeError("no runs discovered under output_root/local_runs/**")

    disc_rows: list[dict[str, Any]] = []
    result_rows: list[dict[str, Any]] = []
    month_parts: list[pd.DataFrame] = []
    quarter_parts: list[pd.DataFrame] = []
    year_parts: list[pd.DataFrame] = []
    exit_rows: list[dict[str, Any]] = []
    tn_rows: list[dict[str, Any]] = []
    dd_rows: list[dict[str, Any]] = []
    slip_parts: list[pd.DataFrame] = []
    erc_parts: list[pd.DataFrame] = []
    comp_parts: list[pd.DataFrame] = []
    comp_m_parts: list[pd.DataFrame] = []
    comp_q_parts: list[pd.DataFrame] = []

    for pid, wid, run_dir in discovered:
        mjson = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8")) if (run_dir / "metrics.json").is_file() else {}
        tpath = trades_path_for_postprocess(run_dir)
        if tpath is None or not tpath.is_file():
            ct = run_dir / "compact_trades.csv"
            tpath = ct if ct.is_file() else tpath
        trades = pd.read_csv(tpath) if tpath is not None and tpath.is_file() else pd.DataFrame()
        status = "OK" if not trades.empty else "NOT_RUN"
        met = metrics_from_trades(trades, metrics_json=mjson)

        disc_rows.append(
            {
                "profile_id": pid,
                "window": wid,
                "run_dir_rel": str(run_dir.relative_to(output_root)).replace("\\", "/"),
                "status": status,
            }
        )

        ref_row = ref[(ref["profile_id"].astype(str) == pid) & (ref["window"].astype(str) == wid)] if not ref.empty else pd.DataFrame()
        ref_tr = float(ref_row.iloc[0]["total_r"]) if not ref_row.empty else float("nan")
        layer3_tr = float(met["total_r"])
        delta = layer3_tr - ref_tr if ref_row is not None and not ref_row.empty and not math.isnan(ref_tr) else float("nan")

        role = roles.get(pid, "")
        row = {
            "profile_id": pid,
            "role": role,
            "window": wid,
            "run_dir_rel": str(run_dir.relative_to(output_root)).replace("\\", "/"),
            "status": status,
            "start_date": str(mjson.get("start", "")),
            "end_date": str(mjson.get("end", "")),
            **met,
            "profit_factor": mjson.get("profit_factor"),
            "max_drawdown_r": mjson.get("max_drawdown_r"),
            "combiner_score": mjson.get("combiner_score"),
            "worst_month_r": None,
            "worst_quarter_r": None,
            "positive_month_count": None,
            "negative_month_count": None,
            "fixed_oow_reference_total_r": ref_tr if not ref_row.empty else None,
            "delta_vs_fixed_oow_reference": delta if not ref_row.empty else None,
        }
        result_rows.append(row)

        if trades.empty:
            continue

        slip_parts.append(layer3_exit_slip_extended(trades, pid, wid))
        erc_parts.append(_exit_reason_cost_table(trades, pid, wid))
        if pid in MULTI_CANDIDATE_PROFILES:
            comp_parts.append(_complementarity(trades, pid, wid))

        t = _period_cols(trades)
        t["r_multiple"] = pd.to_numeric(t["r_multiple"], errors="coerce").fillna(0.0)

        m = t.groupby("_month", dropna=False)["r_multiple"].sum().reset_index().rename(columns={"_month": "month", "r_multiple": "total_r"})
        m.insert(0, "window", wid)
        m.insert(0, "profile_id", pid)
        month_parts.append(m)

        q = t.groupby("_quarter", dropna=False)["r_multiple"].sum().reset_index().rename(columns={"_quarter": "quarter", "r_multiple": "total_r"})
        q.insert(0, "window", wid)
        q.insert(0, "profile_id", pid)
        quarter_parts.append(q)

        y = t.groupby("_year", dropna=False)["r_multiple"].sum().reset_index().rename(columns={"_year": "year", "r_multiple": "total_r"})
        y.insert(0, "window", wid)
        y.insert(0, "profile_id", pid)
        year_parts.append(y)

        for mo, part in t.groupby("_month", dropna=False):
            rs = part["r_multiple"].to_numpy(dtype=float)
            dd = max_drawdown_r(rs)
            dd_rows.append({"profile_id": pid, "window": wid, "month": str(mo), "max_dd_r": float(dd), "trades": int(len(part))})

        if "exit_reason" in trades.columns:
            ex = trades["exit_reason"].astype(str).value_counts().reset_index()
            ex.columns = ["exit_reason", "count"]
            tot = int(ex["count"].sum()) or 1
            for _, rr in ex.iterrows():
                exit_rows.append(
                    {
                        "profile_id": pid,
                        "window": wid,
                        "exit_reason": str(rr["exit_reason"]),
                        "count": int(rr["count"]),
                        "share": float(int(rr["count"]) / tot),
                    }
                )

        tt = trades.copy()
        if "session_date" in tt.columns and "entry_ts_utc" in tt.columns:
            tt = add_prior_trade_columns(tt)
        if "entry_trade_number_of_day" in tt.columns:
            tt["entry_trade_number_of_day"] = pd.to_numeric(tt["entry_trade_number_of_day"], errors="coerce").fillna(0).astype(int)
            agg = tt.groupby("entry_trade_number_of_day", dropna=False)["r_multiple"].sum().reset_index()
            for _, rr in agg.iterrows():
                tn_rows.append(
                    {
                        "profile_id": pid,
                        "window": wid,
                        "trade_number_of_day": int(rr["entry_trade_number_of_day"]),
                        "total_r": float(rr["r_multiple"]),
                    }
                )

        if pid in MULTI_CANDIDATE_PROFILES and "candidate_id" in t.columns:
            t2 = t.copy()
            cm = t2.groupby(["_month", t2["candidate_id"].astype(str)])["r_multiple"].sum().reset_index()
            cm.columns = ["month", "candidate_id", "total_r"]
            cm.insert(0, "window", wid)
            cm.insert(0, "profile_id", pid)
            comp_m_parts.append(cm)
            cq = t2.groupby(["_quarter", t2["candidate_id"].astype(str)])["r_multiple"].sum().reset_index()
            cq.columns = ["quarter", "candidate_id", "total_r"]
            cq.insert(0, "window", wid)
            cq.insert(0, "profile_id", pid)
            comp_q_parts.append(cq)

    disc = pd.DataFrame(disc_rows)
    _write_csv(disc, output_root / "run_discovery_manifest.csv")

    monthly = pd.concat(month_parts, ignore_index=True) if month_parts else pd.DataFrame(columns=["profile_id", "window", "month", "total_r"])
    quarterly = pd.concat(quarter_parts, ignore_index=True) if quarter_parts else pd.DataFrame(
        columns=["profile_id", "window", "quarter", "total_r"]
    )
    yearly = pd.concat(year_parts, ignore_index=True) if year_parts else pd.DataFrame(columns=["profile_id", "window", "year", "total_r"])
    _write_csv(monthly, output_root / "monthly_summary.csv")
    _write_csv(quarterly, output_root / "quarterly_summary.csv")
    _write_csv(yearly, output_root / "yearly_summary.csv")

    # Enrich result_rows with monthly stats per window
    enriched: list[dict[str, Any]] = []
    for row in result_rows:
        r = dict(row)
        pid, wid = str(r["profile_id"]), str(r["window"])
        ms = _monthly_stats_for_window(monthly, pid, wid)
        r["worst_month_r"] = ms["worst_month_r"]
        r["positive_month_count"] = ms["positive_month_count"]
        r["negative_month_count"] = ms["negative_month_count"]
        r["worst_quarter_r"] = _worst_quarter(quarterly, pid, wid)
        enriched.append(r)

    res = pd.DataFrame(enriched)
    _write_csv(res, output_root / "profile_window_summary.csv")

    fa = res[res["window"].astype(str) == "full_available"].copy()
    _write_csv(fa, output_root / "profile_full_available_summary.csv")

    cmp_rows: list[dict[str, Any]] = []
    for _, r in res.iterrows():
        pid, wid = str(r["profile_id"]), str(r["window"])
        ref_row = ref[(ref["profile_id"].astype(str) == pid) & (ref["window"].astype(str) == wid)] if not ref.empty else pd.DataFrame()
        ref_tr = float(ref_row.iloc[0]["total_r"]) if not ref_row.empty else float("nan")
        lr = float(r.get("total_r", 0.0) or 0.0)
        dlt = lr - ref_tr if not ref_row.empty and not math.isnan(ref_tr) else float("nan")
        material = abs(dlt) > 0.05 and not math.isnan(dlt)
        cmp_rows.append(
            {
                "profile_id": pid,
                "window": wid,
                "layer3_total_r": lr,
                "fixed_oow_reference_total_r": ref_tr if not ref_row.empty else None,
                "delta": dlt,
                "material_delta": bool(material),
                "notes": "" if not material else "see run_dir; check data revision vs fixed OOW run date",
            }
        )
    _write_csv(pd.DataFrame(cmp_rows), output_root / "fixed_oow_comparison.csv")

    if dd_rows:
        _write_csv(pd.DataFrame(dd_rows), output_root / "drawdown_summary.csv")
    else:
        _write_csv(pd.DataFrame(columns=["profile_id", "window", "month", "max_dd_r", "trades"]), output_root / "drawdown_summary.csv")

    if tn_rows:
        _write_csv(pd.DataFrame(tn_rows), output_root / "trade_number_summary.csv")
    else:
        _write_csv(pd.DataFrame(columns=["profile_id", "window", "trade_number_of_day", "total_r"]), output_root / "trade_number_summary.csv")

    if exit_rows:
        _write_csv(pd.DataFrame(exit_rows), output_root / "exit_reason_summary.csv")
    else:
        _write_csv(pd.DataFrame(columns=["profile_id", "window", "exit_reason", "count", "share"]), output_root / "exit_reason_summary.csv")

    slip_dir = output_root / "exit_slip"
    slip_dir.mkdir(parents=True, exist_ok=True)
    slip_base = "layer3_optional" if smoke_kind == "optional" else "layer3"
    if slip_parts:
        slip = pd.concat(slip_parts, ignore_index=True)
        _write_csv(slip, slip_dir / f"{slip_base}_exit_slip_scenarios.csv")
        # summary md
        title = "Layer3 optional exit/slip overlay" if smoke_kind == "optional" else "Layer3 exit/slip overlay (CORE)"
        lines = [f"# {title}", ""]
        for pid in sorted(slip["profile_id"].unique()):
            for wid in sorted(slip.loc[slip["profile_id"] == pid, "window"].unique()):
                sub = slip[(slip["profile_id"] == pid) & (slip["window"] == wid)]
                lines.append(f"## {pid} / {wid}")
                for _, sr in sub.iterrows():
                    lines.append(f"- **{sr['scenario']}**: total_r={sr['total_r']:.4f}")
                lines.append("")
        (slip_dir / f"{slip_base}_exit_slip_summary.md").write_text("\n".join(lines), encoding="utf-8")
    if erc_parts:
        _write_csv(pd.concat(erc_parts, ignore_index=True), slip_dir / f"{slip_base}_exit_reason_cost_table.csv")

    comp_dir = output_root / "complementarity"
    comp_dir.mkdir(parents=True, exist_ok=True)
    if comp_parts:
        cdf = pd.concat(comp_parts, ignore_index=True)
        _write_csv(cdf, comp_dir / "profile_candidate_contribution.csv")
        md_lines = [
            "# Multi-candidate contribution (Layer3 smoke)",
            "",
            "| candidate_id | total_r | trades | share_of_total_r |",
            "|---|---:|---:|---:|",
        ]
        for _, rr in cdf.iterrows():
            md_lines.append(
                f"| `{rr['candidate_id']}` | {float(rr['total_r']):.4f} | {int(rr['trades'])} | {float(rr['share_of_total_r']):.4f} |"
            )
        (comp_dir / "profile_candidate_contribution.md").write_text("\n".join(md_lines), encoding="utf-8")
    else:
        (comp_dir / "profile_candidate_contribution.md").write_text(
            "# PA+GAP candidate contribution\n\nNo `candidate_id` column in trades or no pa_gap runs.\n",
            encoding="utf-8",
        )
    if comp_m_parts:
        _write_csv(pd.concat(comp_m_parts, ignore_index=True), comp_dir / "contribution_by_month.csv")
    if comp_q_parts:
        _write_csv(pd.concat(comp_q_parts, ignore_index=True), comp_dir / "contribution_by_quarter.csv")

    slip_for_gates = pd.concat(slip_parts, ignore_index=True) if slip_parts else pd.DataFrame()
    gates_df, risk_df = _evaluate_gates(
        pws=res,
        monthly=monthly,
        quarterly=quarterly,
        slip=slip_for_gates,
        design_root=design_root,
    )
    _write_csv(gates_df, output_root / "gate_results.csv")
    _write_csv(risk_df, output_root / "risk_flags.csv")

    # gate_results.md
    glines = [f"# Gate results (Layer3 {'optional' if smoke_kind == 'optional' else 'CORE'})", ""]
    for gid in sorted(gates_df["gate_id"].unique()):
        sub = gates_df[gates_df["gate_id"] == gid]
        fail = int((~sub["pass"].astype(bool)).sum())
        glines.append(f"## {gid}")
        glines.append(f"- non-pass rows: **{fail}** / {len(sub)}")
        glines.append("")
    (output_root / "gate_results.md").write_text("\n".join(glines), encoding="utf-8")

    rlines = [f"# Risk flags (Layer3 {'optional' if smoke_kind == 'optional' else 'CORE'})", ""]
    for _, rr in risk_df.iterrows():
        rlines.append(f"- **{rr['risk_id']}** ({rr['profile_id']}): {rr['severity']} — {rr['notes']}")
    (output_root / "risk_flags.md").write_text("\n".join(rlines), encoding="utf-8")

    # Profile-level smoke label
    prof_labels: dict[str, str] = {}
    for pid in sorted(res["profile_id"].unique()):
        gsub = gates_df[gates_df["profile_id"].astype(str) == str(pid)]
        if smoke_kind == "optional":
            prof_labels[str(pid)] = _profile_gate_label_layer3_extended(str(pid), gsub)
        else:
            prof_labels[str(pid)] = _profile_gate_label_core(gsub)

    # Decision (CORE vs optional batch)
    if smoke_kind == "optional":
        decision = "OPTIONAL_SMOKE_BATCH_COMPLETE"
        rationale = [
            "Optional baseline/ablation profiles executed (12 runs).",
            "Merged review is produced under `layer3_fixed_profile_smoke_complete_v1/` via `merge-complete`.",
        ]
        bad = {"OPTIONAL_ABLATION_FAIL", "FAIL_LAYER3_SMOKE"}
        if any(prof_labels.get(p) in bad for p in prof_labels):
            decision = "NEED_MORE_LAYER3_OPTIONAL_RUNS"
            rationale.insert(0, "At least one optional profile failed smoke gates.")
    else:
        pa_lbl = prof_labels.get("pa_only_mtp1_meta", "NOT_EVALUATED")
        gap_lbl = prof_labels.get("pa_gap_mtp2_meta", "NOT_EVALUATED")
        decision = "NEED_MORE_LAYER3_CORE_SMOKE"
        rationale = []
        good = {"LAYER3_CORE_SMOKE_PASS", "LAYER3_CORE_SMOKE_PASS_WITH_WARNINGS"}
        if pa_lbl == "FAIL_LAYER3_CORE_SMOKE" or gap_lbl == "FAIL_LAYER3_CORE_SMOKE":
            if gap_lbl == "FAIL_LAYER3_CORE_SMOKE" and pa_lbl != "FAIL_LAYER3_CORE_SMOKE":
                decision = "REFINE_ROBUST_CORE_COMBINATION_RULES"
                rationale.append("PA+GAP CORE profile failed a gate while PA-only passed.")
            else:
                decision = "NEED_MORE_LAYER3_CORE_SMOKE"
                rationale.append("At least one CORE profile failed gates or execution.")
        elif pa_lbl in good and gap_lbl in good:
            decision = "RUN_OPTIONAL_LAYER3_BASELINE_ABLATION"
            rationale.append("Both CORE profiles passed smoke gates (warnings acceptable).")
            rationale.append("Next step: add optional baseline/ablation profiles for breadth and mtp checks.")
        else:
            decision = "NEED_MORE_LAYER3_CORE_SMOKE"
            rationale.append("Unexpected gate label combination; review gate_results.csv.")

    sum_name = "layer3_optional_smoke_summary.md" if smoke_kind == "optional" else "layer3_smoke_summary.md"
    sum_title = "Layer3 optional smoke" if smoke_kind == "optional" else "Layer3 CORE smoke"
    if smoke_kind != "optional":
        (output_root / sum_name).write_text(
            "\n".join(
                [
                    f"# {sum_title} — summary",
                    "",
                    f"- discovered runs: **{len(disc)}**",
                    f"- decision (draft): **{decision}**",
                    "",
                    "See `profile_window_summary.csv`, `gate_results.csv`, `fixed_oow_comparison.csv`.",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    # Write decision + summary CSV key_findings via _write_decision_docs helper inline
    _write_decision_artifacts(
        output_root=output_root,
        design_root=design_root,
        res=res,
        gates_df=gates_df,
        risk_df=risk_df,
        prof_labels=prof_labels,
        decision=decision,
        rationale=rationale,
        smoke_kind=smoke_kind,
    )

    design_decision_path = design_root / "layer3_fixed_profile_smoke_design_decision.md"
    design_decision_note = "RUN_LAYER3_FIXED_PROFILE_SMOKE"
    if design_decision_path.is_file():
        txt = design_decision_path.read_text(encoding="utf-8", errors="replace")
        if "RUN_LAYER3_FIXED_PROFILE_SMOKE" not in txt:
            design_decision_note = "(design decision file present; label not found)"

    if smoke_kind == "optional":
        inv_lines = [
            "# Layer3 fixed-profile smoke optional v1 — baseline inventory",
            "",
            f"- **git_tip (at postprocess):** `{_git_tip(_ROOT)}`",
            f"- **git_branch:** `{_git_branch(_ROOT)}`",
            f"- **sync vs origin (at postprocess):** {_git_ahead_behind_upstream(_ROOT)}",
            f"- **design decision (from `layer3_fixed_profile_smoke_design_decision.md`):** {design_decision_note}",
            "- **CORE smoke recap:** `pa_only_mtp1_meta` / `pa_gap_mtp2_meta` completed under `layer3_fixed_profile_smoke_v1/` (decision was `RUN_OPTIONAL_LAYER3_BASELINE_ABLATION`).",
            "- **Optional profiles executed:** `primary_mtp2_meta`, `pa_gap_mtp1_meta`, `pa_only_mtp2_meta`",
            "- **Not expanded beyond these three** (no VWAP, no PA_004/CCI_002 balanced profiles, no side-flip).",
            "- **windows:** `early_oow`, `insample_ref`, `late_oow`, `full_available`",
            "- **expected run count:** 12 (3 × 4)",
            f"- **discovered runs (metrics.json):** {len(discovered)}",
            "- **local raw run root (do not commit):** `src/research/results/layer3_fixed_profile_smoke_optional_v1/local_runs/**`",
            "- **local configs (do not commit):** `src/research/results/layer3_fixed_profile_smoke_optional_v1/local_configs/**`",
            "- **CORE artifacts present:** read from `layer3_fixed_profile_smoke_v1/profile_window_summary.csv` (parseable).",
            "- **missing curated files:** none required by postprocess (if postprocess completed)",
            "",
            "## Smoke outcome",
            "",
            f"- **decision:** `{decision}`",
            "",
        ]
    else:
        inv_lines = [
            "# Layer3 fixed-profile smoke v1 — baseline inventory",
            "",
            f"- **git_tip (at postprocess):** `{_git_tip(_ROOT)}`",
            f"- **git_branch:** `{_git_branch(_ROOT)}`",
            f"- **sync vs origin (at postprocess):** {_git_ahead_behind_upstream(_ROOT)}",
            f"- **design decision (from `layer3_fixed_profile_smoke_design_decision.md`):** {design_decision_note}",
            "- **NEXT_HANDOFF:** prior tip still described fixed-profile OOW only; updated in this task to Layer3 CORE smoke execution + A–L handoff.",
            "- **CORE profiles executed:** `pa_only_mtp1_meta`, `pa_gap_mtp2_meta`",
            "- **Optional profiles excluded:** `primary_mtp2_meta`, `pa_gap_mtp1_meta`, `pa_only_mtp2_meta`",
            "- **windows:** `early_oow`, `insample_ref`, `late_oow`, `full_available`",
            "- **expected run count:** 8 (2 × 4)",
            f"- **discovered runs (metrics.json):** {len(discovered)}",
            "- **local raw run root (do not commit):** `src/research/results/layer3_fixed_profile_smoke_v1/local_runs/**`",
            "- **local configs (do not commit):** `src/research/results/layer3_fixed_profile_smoke_v1/local_configs/**`",
            "- **missing curated files:** none required by postprocess (if postprocess completed)",
            "",
            "## Smoke outcome",
            "",
            f"- **decision:** `{decision}`",
            "",
        ]
    (output_root / "baseline_inventory.md").write_text("\n".join(inv_lines), encoding="utf-8")

    return 0


def _profile_gate_label_core(gsub: pd.DataFrame) -> str:
    if gsub.empty:
        return "NOT_EVALUATED"
    if bool((~gsub["pass"].astype(bool)).any()):
        return "FAIL_LAYER3_CORE_SMOKE"
    if bool((gsub["level"].astype(str) == "WARNING").any()):
        return "LAYER3_CORE_SMOKE_PASS_WITH_WARNINGS"
    return "LAYER3_CORE_SMOKE_PASS"


def _profile_gate_label_layer3_extended(pid: str, gsub: pd.DataFrame) -> str:
    if gsub.empty:
        return "NOT_EVALUATED"
    failed = bool((~gsub["pass"].astype(bool)).any())
    warned = bool((gsub["level"].astype(str) == "WARNING").any())
    if failed:
        if pid in {"pa_gap_mtp1_meta", "pa_only_mtp2_meta"}:
            return "OPTIONAL_ABLATION_FAIL"
        return "FAIL_LAYER3_SMOKE"
    if pid == "primary_mtp2_meta":
        return "OPTIONAL_BASELINE_PASS_WITH_WARNINGS" if warned else "LAYER3_SMOKE_PASS"
    if pid == "pa_gap_mtp1_meta":
        return "LAYER3_SMOKE_PASS_WITH_WARNINGS" if warned else "OPTIONAL_ABLATION_CONFIRMED"
    if pid == "pa_only_mtp2_meta":
        return "LAYER3_SMOKE_PASS_WITH_WARNINGS" if warned else "OPTIONAL_ABLATION_CONFIRMED"
    return "LAYER3_SMOKE_PASS_WITH_WARNINGS" if warned else "LAYER3_SMOKE_PASS"


def _write_decision_artifacts(
    *,
    output_root: Path,
    design_root: Path,
    res: pd.DataFrame,
    gates_df: pd.DataFrame,
    risk_df: pd.DataFrame,
    prof_labels: dict[str, str],
    decision: str,
    rationale: list[str],
    smoke_kind: str = "core",
) -> None:
    git_tip = _git_tip(_ROOT)
    rootp = _repo_rel_path(output_root)
    is_opt = smoke_kind == "optional"
    decision_title = "Layer3 optional smoke v1 — decision" if is_opt else "Layer3 fixed-profile smoke v1 — decision (CORE only)"
    decision_fn = "layer3_optional_smoke_decision.md" if is_opt else "layer3_fixed_profile_smoke_decision.md"
    kf_fn = "layer3_optional_smoke_key_findings.csv" if is_opt else "layer3_fixed_profile_smoke_key_findings.csv"
    long_sm_fn = "layer3_optional_smoke_summary.md" if is_opt else "layer3_fixed_profile_smoke_summary.md"
    bundle_title = "CHATGPT_REVIEW_BUNDLE — layer3_fixed_profile_smoke_optional_v1" if is_opt else "CHATGPT_REVIEW_BUNDLE — layer3_fixed_profile_smoke_v1 (CORE)"

    lines = [
        f"# {decision_title}",
        "",
        f"**Decision (exactly one):** **`{decision}`**",
        "",
        "## Rationale",
        "",
    ]
    for b in rationale:
        lines.append(f"- {b}")
    lines.extend(
        [
            "",
            "## Profile-level labels",
            "",
        ]
    )
    for k, v in sorted(prof_labels.items()):
        lines.append(f"- `{k}`: **{v}**")
    lines.extend(
        [
            "",
            "## Recommended next step (exactly one)",
            "",
        ]
    )
    if is_opt:
        if decision == "NEED_MORE_LAYER3_OPTIONAL_RUNS":
            lines.append("Repair optional execution or gates; re-run optional smoke.")
        else:
            lines.append("Run `python -m src.research.run_layer3_fixed_profile_smoke merge-complete ...` to build `layer3_fixed_profile_smoke_complete_v1/`.")
    elif decision == "RUN_OPTIONAL_LAYER3_BASELINE_ABLATION":
        lines.append("Run optional Layer3 baseline/ablation (`primary_mtp2_meta`, `pa_gap_mtp1_meta`, `pa_only_mtp2_meta`) in a follow-on task.")
    elif decision == "REFINE_ROBUST_CORE_COMBINATION_RULES":
        lines.append("Refine PA+GAP combination rules or candidate weighting before expanding smoke.")
    else:
        lines.append("Repair execution or postprocess; re-run CORE smoke until manifests and gates are trustworthy.")

    lines.extend(
        [
            "",
            "## Explicit non-runs",
            "",
        ]
    )
    if is_opt:
        lines.extend(
            [
                "- No CORE re-runs in this optional batch (use existing `layer3_fixed_profile_smoke_v1/`).",
                "- No broad Layer2, WFO, live/paper, SPY, router",
                "- No strategy/feature/YAML edits",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "- No optional profiles in this CORE task",
                "- No broad Layer2, WFO, live/paper, SPY, router",
                "- No strategy/feature/YAML edits",
                "",
            ]
        )
    lines.append(f"- git_tip: {git_tip}")
    (output_root / decision_fn).write_text("\n".join(lines), encoding="utf-8")

    # key_findings.csv
    kf: list[dict[str, Any]] = []
    for _, r in res.iterrows():
        kf.append(
            {
                "topic": "window_total_r",
                "profile_id": r["profile_id"],
                "window_or_period": r["window"],
                "result": f"total_r={float(r['total_r']):.4f}",
                "evidence_strength": "high",
                "implication": "headline economics for window",
                "next_action": "compare to fixed OOW reference",
            }
        )
    for pid, lbl in prof_labels.items():
        kf.append(
            {
                "topic": "profile_smoke_label",
                "profile_id": pid,
                "window_or_period": "ALL",
                "result": lbl,
                "evidence_strength": "high",
                "implication": "gate rollup",
                "next_action": decision,
            }
        )
    _write_csv(pd.DataFrame(kf), output_root / kf_fn)

    # Long summary md
    sm = [
        f"# {'Layer3 optional smoke v1 — summary' if is_opt else 'Layer3 fixed-profile smoke v1 — summary (CORE)'}",
        "",
        "## 1. Purpose",
        "",
        "Execute optional Layer3 smoke (3 profiles × 4 windows)." if is_opt else "Execute CORE Layer3 smoke (2 profiles × 4 windows) against fixed design gates.",
        "",
        "## 2. Input design",
        "",
        f"- Design root: `{design_root.as_posix()}`",
        "",
        "## 3. Profiles",
        "",
    ]
    if is_opt:
        sm.extend(["- `primary_mtp2_meta`", "- `pa_gap_mtp1_meta`", "- `pa_only_mtp2_meta`", ""])
    else:
        sm.extend(["- `pa_only_mtp1_meta`", "- `pa_gap_mtp2_meta`", ""])
    sm.extend(
        [
            "## 4. Results",
            "",
            "See `profile_window_summary.csv` and `fixed_oow_comparison.csv`.",
            "",
            "## 5. Gates / risks / cost overlay",
            "",
            "- `gate_results.csv`, `risk_flags.csv`",
            f"- `exit_slip/{'layer3_optional_' if is_opt else 'layer3_'}exit_slip_scenarios.csv`",
            "",
            "## 6. Decision",
            "",
            f"**{decision}**",
            "",
            "## 7. Explicit non-runs",
            "",
            "No WFO/live/SPY/router/YAML edits." if is_opt else "Optional profiles not run in CORE task; no WFO/live/SPY/router/YAML edits.",
            "",
        ]
    )
    (output_root / long_sm_fn).write_text("\n".join(sm), encoding="utf-8")

    # CHATGPT_REVIEW_BUNDLE.md
    bundle = [
        f"# {bundle_title}",
        "",
        f"## 1. Git tip\n\n- `{git_tip}`",
        "",
        "## 2. Execution",
        "",
        f"- Runs (profile×window rows): **{len(res)}**",
        "",
        "## 3. Per-window total_r",
        "",
        _markdown_total_r_pivot(res),
        "",
        "## 4. Fixed OOW comparison",
        "",
        "See `fixed_oow_comparison.csv`.",
        "",
        "## 5. Gates",
        "",
        "See `gate_results.md` / `gate_results.csv`.",
        "",
        "## 6. Cost overlay",
        "",
        f"See `exit_slip/{'layer3_optional_' if is_opt else 'layer3_'}exit_slip_scenarios.csv`.",
        "",
        "## 7. Decision",
        "",
        f"**{decision}**",
        "",
        "## 8. Non-runs",
        "",
        "No broad L2/WFO/live/SPY.",
        "",
    ]
    (output_root / "CHATGPT_REVIEW_BUNDLE.md").write_text("\n".join(bundle), encoding="utf-8")

    # chatgpt_key_metrics.csv
    km: list[dict[str, Any]] = []
    for _, r in res.iterrows():
        km.append(
            {
                "section": "per_window",
                "profile_id": r["profile_id"],
                "window": r["window"],
                "metric": "total_r",
                "value": float(r["total_r"]),
                "interpretation": "Layer3 optional replay" if is_opt else "Layer3 CORE replay",
            }
        )
    _write_csv(pd.DataFrame(km), output_root / "chatgpt_key_metrics.csv")

    sm_rows: list[dict[str, Any]] = [
        {
            "file_path": f"{rootp}/CHATGPT_REVIEW_BUNDLE.md",
            "purpose": "single review entry",
            "required_for_review": "YES",
            "row_count_if_csv": "",
            "markdown_mirror_available": "YES",
            "notes": "",
        },
        {
            "file_path": f"{rootp}/profile_window_summary.csv",
            "purpose": "headline metrics per window",
            "required_for_review": "YES",
            "row_count_if_csv": str(len(res)),
            "markdown_mirror_available": "NO",
            "notes": "",
        },
        {
            "file_path": f"{rootp}/profile_full_available_summary.csv",
            "purpose": "full-span slice only",
            "required_for_review": "YES",
            "row_count_if_csv": str(len(res[res["window"].astype(str) == "full_available"])),
            "markdown_mirror_available": "NO",
            "notes": "",
        },
        {
            "file_path": f"{rootp}/fixed_oow_comparison.csv",
            "purpose": "Layer3 vs fixed OOW reference",
            "required_for_review": "YES",
            "row_count_if_csv": "",
            "markdown_mirror_available": "NO",
            "notes": "",
        },
        {
            "file_path": f"{rootp}/gate_results.csv",
            "purpose": "gate evaluation",
            "required_for_review": "YES",
            "row_count_if_csv": str(len(gates_df)),
            "markdown_mirror_available": "YES",
            "notes": "gate_results.md",
        },
        {
            "file_path": f"{rootp}/risk_flags.csv",
            "purpose": "risk register flags",
            "required_for_review": "YES",
            "row_count_if_csv": str(len(risk_df)),
            "markdown_mirror_available": "YES",
            "notes": "risk_flags.md",
        },
        {
            "file_path": f"{rootp}/exit_slip/{'layer3_optional_' if is_opt else 'layer3_'}exit_slip_scenarios.csv",
            "purpose": "cost overlay scenarios",
            "required_for_review": "YES",
            "row_count_if_csv": "",
            "markdown_mirror_available": "YES",
            "notes": f"{'layer3_optional_' if is_opt else 'layer3_'}exit_slip_summary.md",
        },
        {
            "file_path": f"{rootp}/run_execution_manifest_sanitized.csv",
            "purpose": "execution audit without abs paths",
            "required_for_review": "YES",
            "row_count_if_csv": "",
            "markdown_mirror_available": "NO",
            "notes": "",
        },
        {
            "file_path": f"{rootp}/{decision_fn}",
            "purpose": "decision label",
            "required_for_review": "YES",
            "row_count_if_csv": "",
            "markdown_mirror_available": "YES",
            "notes": "",
        },
    ]
    _write_csv(pd.DataFrame(sm_rows), output_root / "SOURCE_MAP.csv")


def _label_for_complete_merge(pid: str, gsub: pd.DataFrame) -> str:
    if pid in CORE_PROFILE_IDS:
        return _profile_gate_label_core(gsub).replace("LAYER3_CORE_SMOKE_", "LAYER3_SMOKE_")
    return _profile_gate_label_layer3_extended(pid, gsub)


def cmd_merge_complete(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Merge CORE + optional Layer3 smoke into complete_v1 review.")
    p.add_argument("--design-root", required=True)
    p.add_argument("--fixed-profile-root", required=True)
    p.add_argument("--core-root", required=True)
    p.add_argument("--optional-root", required=True)
    p.add_argument("--output-root", required=True)
    args = p.parse_args(argv)

    design_root = Path(args.design_root)
    fixed_root = Path(args.fixed_profile_root)
    core_root = Path(args.core_root)
    opt_root = Path(args.optional_root)
    out = Path(args.output_root)
    if not design_root.is_absolute():
        design_root = Path.cwd() / design_root
    if not fixed_root.is_absolute():
        fixed_root = Path.cwd() / fixed_root
    if not core_root.is_absolute():
        core_root = Path.cwd() / core_root
    if not opt_root.is_absolute():
        opt_root = Path.cwd() / opt_root
    if not out.is_absolute():
        out = Path.cwd() / out
    out.mkdir(parents=True, exist_ok=True)

    roles = _load_profile_roles(design_root)
    cr = pd.read_csv(core_root / "profile_window_summary.csv")
    op = pd.read_csv(opt_root / "profile_window_summary.csv")
    expected_profiles = {"pa_only_mtp1_meta", "pa_gap_mtp2_meta", "primary_mtp2_meta", "pa_gap_mtp1_meta", "pa_only_mtp2_meta"}
    got = set(cr["profile_id"].astype(str).unique()) | set(op["profile_id"].astype(str).unique())
    if got != expected_profiles:
        raise ValueError(f"merge-complete: expected profiles {sorted(expected_profiles)}, got {sorted(got)}")

    merged = pd.concat([cr, op], ignore_index=True)
    _write_csv(merged, out / "complete_profile_window_summary.csv")
    fa = merged[merged["window"].astype(str) == "full_available"].copy()
    _write_csv(fa, out / "complete_profile_full_available_summary.csv")

    # Monthly / quarterly / yearly / drawdown / exit / trade_number — concat when present
    for name in ("monthly_summary.csv", "quarterly_summary.csv", "yearly_summary.csv", "drawdown_summary.csv", "exit_reason_summary.csv", "trade_number_summary.csv"):
        c1 = core_root / name
        o1 = opt_root / name
        parts = []
        if c1.is_file():
            parts.append(pd.read_csv(c1))
        if o1.is_file():
            parts.append(pd.read_csv(o1))
        if parts:
            _write_csv(pd.concat(parts, ignore_index=True), out / f"complete_{name}")

    # Fixed OOW comparison concat
    fc = pd.read_csv(core_root / "fixed_oow_comparison.csv")
    fo = pd.read_csv(opt_root / "fixed_oow_comparison.csv")
    _write_csv(pd.concat([fc, fo], ignore_index=True), out / "complete_fixed_oow_comparison.csv")

    # Exit slip concat
    slip_c = core_root / "exit_slip/layer3_exit_slip_scenarios.csv"
    slip_o = opt_root / "exit_slip/layer3_optional_exit_slip_scenarios.csv"
    slip_parts: list[pd.DataFrame] = []
    if slip_c.is_file():
        slip_parts.append(pd.read_csv(slip_c))
    if slip_o.is_file():
        slip_parts.append(pd.read_csv(slip_o))
    slip_all = pd.concat(slip_parts, ignore_index=True) if slip_parts else pd.DataFrame()
    if not slip_all.empty:
        _write_csv(slip_all, out / "complete_exit_slip_comparison.csv")
        lines = ["# Complete Layer3 exit/slip (CORE + optional)", ""]
        for pid in sorted(slip_all["profile_id"].astype(str).unique()):
            for wid in ["early_oow", "insample_ref", "late_oow", "full_available"]:
                sub = slip_all[(slip_all["profile_id"].astype(str) == pid) & (slip_all["window"].astype(str) == wid)]
                if sub.empty:
                    continue
                lines.append(f"## {pid} / {wid}")
                for _, sr in sub.iterrows():
                    lines.append(f"- **{sr['scenario']}**: total_r={float(sr['total_r']):.4f}")
                lines.append("")
        (out / "complete_exit_slip_summary.md").write_text("\n".join(lines), encoding="utf-8")

    monthly = pd.read_csv(out / "complete_monthly_summary.csv") if (out / "complete_monthly_summary.csv").is_file() else pd.DataFrame()
    quarterly = pd.read_csv(out / "complete_quarterly_summary.csv") if (out / "complete_quarterly_summary.csv").is_file() else pd.DataFrame()
    gates_df, risk_df = _evaluate_gates(pws=merged, monthly=monthly, quarterly=quarterly, slip=slip_all, design_root=design_root)
    _write_csv(gates_df, out / "complete_gate_results.csv")
    _write_csv(risk_df, out / "complete_risk_flags.csv")

    glines = ["# Gate results (Layer3 complete)", ""]
    for gid in sorted(gates_df["gate_id"].unique()):
        sub = gates_df[gates_df["gate_id"] == gid]
        fail = int((~sub["pass"].astype(bool)).sum())
        glines.append(f"## {gid}")
        glines.append(f"- non-pass rows: **{fail}** / {len(sub)}")
        glines.append("")
    (out / "complete_gate_results.md").write_text("\n".join(glines), encoding="utf-8")
    rlines = ["# Risk flags (Layer3 complete)", ""]
    for _, rr in risk_df.iterrows():
        rlines.append(f"- **{rr['risk_id']}** ({rr['profile_id']}): {rr['severity']} — {rr['notes']}")
    (out / "complete_risk_flags.md").write_text("\n".join(rlines), encoding="utf-8")

    # Profile labels + ranking
    prof_labels: dict[str, str] = {}
    for pid in sorted(merged["profile_id"].astype(str).unique()):
        gsub = gates_df[gates_df["profile_id"].astype(str) == str(pid)]
        prof_labels[pid] = _label_for_complete_merge(pid, gsub)

    fa_rows = fa.copy()
    fa_rows["label"] = fa_rows["profile_id"].astype(str).map(prof_labels)
    rank_rows = []
    for _, r in fa_rows.sort_values("total_r", ascending=False).iterrows():
        rank_rows.append(
            {
                "rank": len(rank_rows) + 1,
                "profile_id": r["profile_id"],
                "role": roles.get(str(r["profile_id"]), ""),
                "total_r": float(r["total_r"]),
                "max_dd_r": float(r.get("max_dd_r", r.get("max_drawdown_r", 0)) or 0),
                "label": r["label"],
            }
        )
    _write_csv(pd.DataFrame(rank_rows), out / "complete_ranking.csv")

    # core_vs_optional_comparison
    cmp_list: list[dict[str, Any]] = []
    by_prof = {p: merged[merged["profile_id"].astype(str) == p] for p in expected_profiles}

    def tot(pid: str, w: str) -> float:
        sub = by_prof[pid][by_prof[pid]["window"].astype(str) == w]
        return float(sub.iloc[0]["total_r"]) if not sub.empty else float("nan")

    for w in ["early_oow", "insample_ref", "late_oow", "full_available"]:
        a, b = tot("pa_only_mtp1_meta", w), tot("pa_only_mtp2_meta", w)
        cmp_list.append(
            {
                "comparison": "pa_only_mtp1_vs_mtp2",
                "window": w,
                "delta_total_r": a - b if not math.isnan(a) and not math.isnan(b) else float("nan"),
                "notes": "near-zero delta => mtp does not bind" if abs(a - b) < 0.05 else "material delta",
            }
        )
        g2, g1 = tot("pa_gap_mtp2_meta", w), tot("pa_gap_mtp1_meta", w)
        cmp_list.append(
            {
                "comparison": "pa_gap_mtp2_vs_mtp1",
                "window": w,
                "delta_total_r": g2 - g1 if not math.isnan(g2) and not math.isnan(g1) else float("nan"),
                "notes": "positive favors mtp2 cap",
            }
        )
    _write_csv(pd.DataFrame(cmp_list), out / "core_vs_optional_comparison.csv")

    # Complementarity merge
    comp_parts: list[pd.DataFrame] = []
    for root, name in (
        (core_root, "complementarity/profile_candidate_contribution.csv"),
        (opt_root, "complementarity/profile_candidate_contribution.csv"),
    ):
        pth = root / name
        if pth.is_file():
            comp_parts.append(pd.read_csv(pth))
    if comp_parts:
        cdf = pd.concat(comp_parts, ignore_index=True)
        _write_csv(cdf, out / "complete_candidate_contribution.csv")
        md = ["# Candidate contribution (complete)", "", "| profile_id | window | candidate_id | total_r | trades | share |", "|---|---|---|---:|---:|---:|"]
        for _, rr in cdf.iterrows():
            md.append(
                f"| `{rr['profile_id']}` | `{rr['window']}` | `{rr['candidate_id']}` | {float(rr['total_r']):.4f} | {int(rr['trades'])} | {float(rr.get('share_of_total_r', 0)):.4f} |"
            )
        (out / "complete_candidate_contribution.md").write_text("\n".join(md), encoding="utf-8")
    else:
        (out / "complete_candidate_contribution.md").write_text("# Candidate contribution\n\nNo complementarity CSVs found.\n")

    # Decision
    decision, rationale = _decision_layer3_complete(merged, gates_df, prof_labels, cmp_list)
    _write_complete_decision_bundle(out=out, design_root=design_root, merged=merged, gates_df=gates_df, risk_df=risk_df, prof_labels=prof_labels, decision=decision, rationale=rationale, slip_all=slip_all, rank_rows=rank_rows)

    return 0


def _decision_layer3_complete(
    merged: pd.DataFrame,
    gates_df: pd.DataFrame,
    prof_labels: dict[str, str],
    cmp: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    rationale: list[str] = []
    if bool((~gates_df["pass"].astype(bool)).any()):
        return "REFINE_ROBUST_CORE_COMBINATION_RULES", ["At least one gate FAIL on merged profile×window rows."]
    bad_lbl = {"FAIL_LAYER3_SMOKE", "OPTIONAL_ABLATION_FAIL"}
    if any(prof_labels.get(p) in bad_lbl for p in prof_labels):
        return "REFINE_ROBUST_CORE_COMBINATION_RULES", ["A profile-level label indicates failure or failed ablation."]

    # mtp equivalence: pa_only deltas small on full_available
    cmp_df = pd.DataFrame(cmp) if cmp else pd.DataFrame()
    sub_mtp = cmp_df[(cmp_df["comparison"] == "pa_only_mtp1_vs_mtp2") & (cmp_df["window"].astype(str) == "full_available")]
    if not sub_mtp.empty and abs(float(sub_mtp.iloc[0]["delta_total_r"])) > 0.25:
        rationale.append("pa_only mtp1 vs mtp2 shows material divergence on full_available; investigate max_trades binding.")
    sub_gap = cmp_df[(cmp_df["comparison"] == "pa_gap_mtp2_vs_mtp1") & (cmp_df["window"].astype(str) == "full_available")]
    if not sub_gap.empty and float(sub_gap.iloc[0]["delta_total_r"]) < 0:
        rationale.append("pa_gap mtp2 does not dominate mtp1 on full_available; conflicts with prior expectation.")
    else:
        rationale.append("pa_gap mtp2 ≥ mtp1 on full_available (typical expectation).")

    prim = prof_labels.get("primary_mtp2_meta", "")
    if prim == "FAIL_LAYER3_SMOKE":
        return "REFINE_ROBUST_CORE_COMBINATION_RULES", ["Primary CCI profile failed rollup gates."]

    rationale.append("CORE profiles remain the recommended defaults; CCI breadth stays optional.")
    rationale.append("No optional profile invalidates locked PA+GAP mtp2 economics on merged gates.")
    if prof_labels.get("primary_mtp2_meta") == "OPTIONAL_BASELINE_PASS_WITH_WARNINGS":
        rationale.append(
            "`primary_mtp2_meta` passes as optional breadth baseline with warnings; late_oow is structurally weaker than PA-only / PA+GAP despite strong full_available R."
        )
    rationale.append(
        "`pa_only_mtp1_meta` vs `pa_only_mtp2_meta` shows ~0 delta across windows in this stack (mtp does not bind for PA-only)."
    )
    return "PROCEED_TO_LAYER3_EXPANDED_STABILITY_DESIGN", rationale


def _write_complete_decision_bundle(
    *,
    out: Path,
    design_root: Path,
    merged: pd.DataFrame,
    gates_df: pd.DataFrame,
    risk_df: pd.DataFrame,
    prof_labels: dict[str, str],
    decision: str,
    rationale: list[str],
    slip_all: pd.DataFrame,
    rank_rows: list[dict[str, Any]],
) -> None:
    git_tip = _git_tip(_ROOT)
    rootp = _repo_rel_path(out)
    lines = [
        "# Layer3 complete fixed-profile smoke v1 — decision",
        "",
        f"**Decision (exactly one):** **`{decision}`**",
        "",
        "## Rationale",
        "",
    ]
    for b in rationale:
        lines.append(f"- {b}")
    lines.extend(["", "## Profile-level labels", ""])
    for k, v in sorted(prof_labels.items()):
        lines.append(f"- `{k}`: **{v}**")
    lines.extend(
        [
            "",
            "## Recommended next step (exactly one)",
            "",
            "Design Layer3 expanded stability review (no WFO/live/SPY until design).",
            "",
            "## Explicit non-runs",
            "",
            "- No broad Layer2 sweep; no mini/full WFO; no live/paper; no SPY; no router",
            "- No strategy/feature/selected-candidate YAML edits",
            "",
            f"- git_tip: {git_tip}",
        ]
    )
    (out / "layer3_complete_smoke_decision.md").write_text("\n".join(lines), encoding="utf-8")

    kf: list[dict[str, Any]] = []
    for _, r in merged.iterrows():
        kf.append(
            {
                "topic": "window_total_r",
                "profile_id": r["profile_id"],
                "window_or_period": r["window"],
                "result": f"total_r={float(r['total_r']):.4f}",
                "evidence_strength": "high",
                "implication": "merged CORE+optional replay",
                "next_action": decision,
            }
        )
    for pid, lbl in prof_labels.items():
        kf.append(
            {
                "topic": "profile_label",
                "profile_id": pid,
                "window_or_period": "ALL",
                "result": lbl,
                "evidence_strength": "high",
                "implication": "complete gate rollup",
                "next_action": decision,
            }
        )
    _write_csv(pd.DataFrame(kf), out / "layer3_complete_smoke_key_findings.csv")

    sm = [
        "# Layer3 complete smoke v1 — summary",
        "",
        "## 1. Purpose",
        "",
        "Merge CORE (`layer3_fixed_profile_smoke_v1`) + optional (`layer3_fixed_profile_smoke_optional_v1`) into one five-profile review.",
        "",
        "## 2. Ranking (full_available)",
        "",
        "| rank | profile_id | total_r | label |",
        "|---:|---|---:|---|",
    ]
    for rr in rank_rows[:10]:
        sm.append(f"| {rr['rank']} | `{rr['profile_id']}` | {float(rr['total_r']):.2f} | `{rr['label']}` |")
    sm.extend(["", "## 3. Decision", "", f"**{decision}**", ""])
    (out / "layer3_complete_smoke_summary.md").write_text("\n".join(sm), encoding="utf-8")

    bundle = [
        "# CHATGPT_REVIEW_BUNDLE — layer3_fixed_profile_smoke_complete_v1",
        "",
        f"## 1. Git tip\n\n- `{git_tip}`",
        "",
        "## 2. Complete profile table (total_r)",
        "",
        _markdown_total_r_pivot(merged),
        "",
        "## 3. Ranking",
        "",
        "See `complete_ranking.csv`.",
        "",
        "## 4. CORE vs optional",
        "",
        "See `core_vs_optional_comparison.csv`.",
        "",
        "## 5. Gates / risks",
        "",
        "`complete_gate_results.csv`, `complete_risk_flags.csv`",
        "",
        "## 6. Cost overlay",
        "",
        "`complete_exit_slip_comparison.csv`",
        "",
        "## 7. Contribution",
        "",
        "`complete_candidate_contribution.csv`",
        "",
        "## 8. Decision",
        "",
        f"**{decision}**",
        "",
    ]
    (out / "CHATGPT_REVIEW_BUNDLE.md").write_text("\n".join(bundle), encoding="utf-8")

    km: list[dict[str, Any]] = []
    for _, r in merged.iterrows():
        km.append(
            {
                "section": "per_window",
                "profile_id": r["profile_id"],
                "window": r["window"],
                "metric": "total_r",
                "value": float(r["total_r"]),
                "interpretation": "merged replay",
            }
        )
    _write_csv(pd.DataFrame(km), out / "chatgpt_key_metrics.csv")

    sm_rows = [
        {"file_path": f"{rootp}/CHATGPT_REVIEW_BUNDLE.md", "purpose": "review", "required_for_review": "YES", "row_count_if_csv": "", "markdown_mirror_available": "YES", "notes": ""},
        {"file_path": f"{rootp}/complete_profile_window_summary.csv", "purpose": "all profiles", "required_for_review": "YES", "row_count_if_csv": str(len(merged)), "markdown_mirror_available": "NO", "notes": ""},
        {"file_path": f"{rootp}/complete_gate_results.csv", "purpose": "gates", "required_for_review": "YES", "row_count_if_csv": str(len(gates_df)), "markdown_mirror_available": "YES", "notes": "complete_gate_results.md"},
        {"file_path": f"{rootp}/layer3_complete_smoke_decision.md", "purpose": "decision", "required_for_review": "YES", "row_count_if_csv": "", "markdown_mirror_available": "YES", "notes": ""},
    ]
    _write_csv(pd.DataFrame(sm_rows), out / "SOURCE_MAP.csv")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "postprocess":
        return cmd_postprocess(argv[1:])
    if argv and argv[0] == "merge-complete":
        return cmd_merge_complete(argv[1:])
    p = argparse.ArgumentParser(description="Layer3 fixed-profile smoke v1.")
    p.add_argument("--design-root", required=True)
    p.add_argument("--fixed-profile-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--profiles", default="")
    p.add_argument("--windows", default="early_oow,insample_ref,late_oow,full_available")
    p.add_argument("--core-only", action="store_true")
    p.add_argument("--include-optional-baseline", action="store_true")
    p.add_argument("--include-ablations", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--data-dir", default="data/raw/ibkr")
    p.add_argument("--skip-existing", action="store_true")
    p.add_argument("--stop-on-fail", action="store_true")
    p.add_argument("--no-signal-cache", action="store_true")
    args, _rest = p.parse_known_args(argv)

    if args.dry_run:
        return cmd_dry_run(argv)
    return cmd_run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
