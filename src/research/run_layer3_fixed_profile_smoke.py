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

    checks = []
    n = len(plan)
    checks.append(("row_count_8", n == 8, f"rows={n}"))
    prof_set = set(plan["profile_id"].astype(str))
    checks.append(("only_core_profiles", prof_set <= CORE_PROFILE_IDS, f"profiles={sorted(prof_set)}"))
    checks.append(("no_primary", "primary_mtp2_meta" not in prof_set, ""))
    checks.append(("no_ablations", not prof_set.intersection({"pa_gap_mtp1_meta", "pa_only_mtp2_meta"}), ""))
    rp = plan["run_dir_rel"].astype(str).str.contains(r"^[a-zA-Z0-9_/.\-]+$", regex=True)
    checks.append(("run_dir_rel_safe", bool(rp.all()), "run_dir_rel pattern"))
    chk_df = pd.DataFrame([{"check": a, "passed": b, "detail": c} for a, b, c in checks])
    _write_csv(chk_df, output_root / "dry_run_validation.csv")
    all_pass = bool(chk_df["passed"].all())
    lines = [
        "# Layer3 CORE smoke — dry-run validation",
        "",
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
        risk_rows.append(
            {
                "risk_id": "R_PA_CONCENTRATION" if pid == "pa_only_mtp1_meta" else "R_GAP_DEPENDENCE",
                "profile_id": pid,
                "severity": "MEDIUM",
                "notes": "single PA candidate" if pid == "pa_only_mtp1_meta" else "combined profile; inspect GAP share",
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
        if pid == "pa_gap_mtp2_meta" and not math.isnan(late_r):
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
        if pid == "pa_gap_mtp2_meta":
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

        if pid == "pa_gap_mtp2_meta" and "candidate_id" in t.columns:
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
    if slip_parts:
        slip = pd.concat(slip_parts, ignore_index=True)
        _write_csv(slip, slip_dir / "layer3_exit_slip_scenarios.csv")
        # summary md
        lines = ["# Layer3 exit/slip overlay (CORE)", ""]
        for pid in sorted(slip["profile_id"].unique()):
            for wid in sorted(slip.loc[slip["profile_id"] == pid, "window"].unique()):
                sub = slip[(slip["profile_id"] == pid) & (slip["window"] == wid)]
                lines.append(f"## {pid} / {wid}")
                for _, sr in sub.iterrows():
                    lines.append(f"- **{sr['scenario']}**: total_r={sr['total_r']:.4f}")
                lines.append("")
        (slip_dir / "layer3_exit_slip_summary.md").write_text("\n".join(lines), encoding="utf-8")
    if erc_parts:
        _write_csv(pd.concat(erc_parts, ignore_index=True), slip_dir / "layer3_exit_reason_cost_table.csv")

    comp_dir = output_root / "complementarity"
    comp_dir.mkdir(parents=True, exist_ok=True)
    if comp_parts:
        cdf = pd.concat(comp_parts, ignore_index=True)
        _write_csv(cdf, comp_dir / "profile_candidate_contribution.csv")
        md_lines = [
            "# PA+GAP candidate contribution (CORE)",
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
    glines = ["# Gate results (Layer3 CORE)", ""]
    for gid in sorted(gates_df["gate_id"].unique()):
        sub = gates_df[gates_df["gate_id"] == gid]
        fail = int((~sub["pass"].astype(bool)).sum())
        glines.append(f"## {gid}")
        glines.append(f"- non-pass rows: **{fail}** / {len(sub)}")
        glines.append("")
    (output_root / "gate_results.md").write_text("\n".join(glines), encoding="utf-8")

    rlines = ["# Risk flags (Layer3 CORE)", ""]
    for _, rr in risk_df.iterrows():
        rlines.append(f"- **{rr['risk_id']}** ({rr['profile_id']}): {rr['severity']} — {rr['notes']}")
    (output_root / "risk_flags.md").write_text("\n".join(rlines), encoding="utf-8")

    # Profile-level smoke label
    prof_labels: dict[str, str] = {}
    for pid in sorted(res["profile_id"].unique()):
        gsub = gates_df[gates_df["profile_id"].astype(str) == str(pid)]
        if gsub.empty:
            prof_labels[str(pid)] = "NOT_EVALUATED"
            continue
        if any(~gsub["pass"].astype(bool)):
            prof_labels[str(pid)] = "FAIL_LAYER3_CORE_SMOKE"
        elif any(gsub["level"].astype(str) == "WARNING"):
            prof_labels[str(pid)] = "LAYER3_CORE_SMOKE_PASS_WITH_WARNINGS"
        else:
            prof_labels[str(pid)] = "LAYER3_CORE_SMOKE_PASS"

    # Decision between RUN_OPTIONAL..., REFINE..., etc.
    pa_lbl = prof_labels.get("pa_only_mtp1_meta", "NOT_EVALUATED")
    gap_lbl = prof_labels.get("pa_gap_mtp2_meta", "NOT_EVALUATED")
    decision = "NEED_MORE_LAYER3_CORE_SMOKE"
    rationale: list[str] = []
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

    # layer3_smoke_summary.md (short; full narrative in layer3_fixed_profile_smoke_summary.md)
    (output_root / "layer3_smoke_summary.md").write_text(
        "\n".join(
            [
                "# Layer3 CORE smoke — summary",
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
    )

    design_decision_path = design_root / "layer3_fixed_profile_smoke_design_decision.md"
    design_decision_note = "RUN_LAYER3_FIXED_PROFILE_SMOKE"
    if design_decision_path.is_file():
        txt = design_decision_path.read_text(encoding="utf-8", errors="replace")
        if "RUN_LAYER3_FIXED_PROFILE_SMOKE" not in txt:
            design_decision_note = "(design decision file present; label not found)"

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
) -> None:
    git_tip = _git_tip(_ROOT)
    lines = [
        "# Layer3 fixed-profile smoke v1 — decision (CORE only)",
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
    if decision == "RUN_OPTIONAL_LAYER3_BASELINE_ABLATION":
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
            "- No optional profiles in this CORE task",
            "- No broad Layer2, WFO, live/paper, SPY, router",
            "- No strategy/feature/YAML edits",
            "",
            f"- git_tip: {git_tip}",
        ]
    )
    (output_root / "layer3_fixed_profile_smoke_decision.md").write_text("\n".join(lines), encoding="utf-8")

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
                "implication": "headline economics for CORE window",
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
    _write_csv(pd.DataFrame(kf), output_root / "layer3_fixed_profile_smoke_key_findings.csv")

    # layer3_fixed_profile_smoke_summary.md
    sm = [
        "# Layer3 fixed-profile smoke v1 — summary (CORE)",
        "",
        "## 1. Purpose",
        "",
        "Execute CORE Layer3 smoke (2 profiles × 4 windows) against fixed design gates.",
        "",
        "## 2. Input design",
        "",
        f"- Design root: `{design_root.as_posix()}`",
        "",
        "## 3. CORE profiles",
        "",
        "- `pa_only_mtp1_meta`",
        "- `pa_gap_mtp2_meta`",
        "",
        "## 4. Results",
        "",
        "See `profile_window_summary.csv` and `fixed_oow_comparison.csv`.",
        "",
        "## 5. Gates / risks / cost overlay",
        "",
        "- `gate_results.csv`, `risk_flags.csv`",
        "- `exit_slip/layer3_exit_slip_scenarios.csv`",
        "",
        "## 6. Decision",
        "",
        f"**{decision}**",
        "",
        "## 7. Explicit non-runs",
        "",
        "Optional profiles not run; no WFO/live/SPY/router/YAML edits.",
        "",
    ]
    (output_root / "layer3_fixed_profile_smoke_summary.md").write_text("\n".join(sm), encoding="utf-8")

    # CHATGPT_REVIEW_BUNDLE.md
    bundle = [
        "# CHATGPT_REVIEW_BUNDLE — layer3_fixed_profile_smoke_v1 (CORE)",
        "",
        f"## 1. Git tip\n\n- `{git_tip}`",
        "",
        "## 2. CORE execution",
        "",
        "- Profiles: `pa_only_mtp1_meta`, `pa_gap_mtp2_meta`",
        "- Windows: `early_oow`, `insample_ref`, `late_oow`, `full_available`",
        f"- Runs discovered: **{len(res)}**",
        "",
        "## 3. Per-window total_r (Layer3)",
        "",
        _markdown_total_r_pivot(res),
        "",
        "## 4. Fixed OOW comparison",
        "",
        "See `fixed_oow_comparison.csv` (should match within float noise if same data/code).",
        "",
        "## 5. Gates",
        "",
        "See `gate_results.md` / `gate_results.csv`.",
        "",
        "## 6. Cost overlay",
        "",
        "See `exit_slip/layer3_exit_slip_scenarios.csv` — target_limit_stress must stay positive for full_available (gate).",
        "",
        "## 7. Complementarity",
        "",
        "See `complementarity/profile_candidate_contribution.csv` for PA+GAP.",
        "",
        "## 8. Decision",
        "",
        f"**{decision}**",
        "",
        "## 9. Non-runs",
        "",
        "No optional profiles; no broad L2/WFO/live/SPY.",
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
                "interpretation": "Layer3 CORE replay",
            }
        )
    _write_csv(pd.DataFrame(km), output_root / "chatgpt_key_metrics.csv")

    sm_rows: list[dict[str, Any]] = [
        {
            "file_path": "src/research/results/layer3_fixed_profile_smoke_v1/CHATGPT_REVIEW_BUNDLE.md",
            "purpose": "single review entry",
            "required_for_review": "YES",
            "row_count_if_csv": "",
            "markdown_mirror_available": "YES",
            "notes": "",
        },
        {
            "file_path": "src/research/results/layer3_fixed_profile_smoke_v1/profile_window_summary.csv",
            "purpose": "headline metrics per window",
            "required_for_review": "YES",
            "row_count_if_csv": str(len(res)),
            "markdown_mirror_available": "NO",
            "notes": "",
        },
        {
            "file_path": "src/research/results/layer3_fixed_profile_smoke_v1/profile_full_available_summary.csv",
            "purpose": "full-span slice only",
            "required_for_review": "YES",
            "row_count_if_csv": str(len(res[res["window"].astype(str) == "full_available"])),
            "markdown_mirror_available": "NO",
            "notes": "",
        },
        {
            "file_path": "src/research/results/layer3_fixed_profile_smoke_v1/fixed_oow_comparison.csv",
            "purpose": "Layer3 vs fixed OOW reference",
            "required_for_review": "YES",
            "row_count_if_csv": "",
            "markdown_mirror_available": "NO",
            "notes": "",
        },
        {
            "file_path": "src/research/results/layer3_fixed_profile_smoke_v1/gate_results.csv",
            "purpose": "gate evaluation",
            "required_for_review": "YES",
            "row_count_if_csv": str(len(gates_df)),
            "markdown_mirror_available": "YES",
            "notes": "gate_results.md",
        },
        {
            "file_path": "src/research/results/layer3_fixed_profile_smoke_v1/risk_flags.csv",
            "purpose": "risk register flags",
            "required_for_review": "YES",
            "row_count_if_csv": str(len(risk_df)),
            "markdown_mirror_available": "YES",
            "notes": "risk_flags.md",
        },
        {
            "file_path": "src/research/results/layer3_fixed_profile_smoke_v1/exit_slip/layer3_exit_slip_scenarios.csv",
            "purpose": "cost overlay scenarios",
            "required_for_review": "YES",
            "row_count_if_csv": "",
            "markdown_mirror_available": "YES",
            "notes": "layer3_exit_slip_summary.md",
        },
        {
            "file_path": "src/research/results/layer3_fixed_profile_smoke_v1/run_execution_manifest_sanitized.csv",
            "purpose": "execution audit without abs paths",
            "required_for_review": "YES",
            "row_count_if_csv": "",
            "markdown_mirror_available": "NO",
            "notes": "",
        },
        {
            "file_path": "src/research/results/layer3_fixed_profile_smoke_v1/layer3_fixed_profile_smoke_decision.md",
            "purpose": "final decision label",
            "required_for_review": "YES",
            "row_count_if_csv": "",
            "markdown_mirror_available": "YES",
            "notes": "",
        },
    ]
    _write_csv(pd.DataFrame(sm_rows), output_root / "SOURCE_MAP.csv")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "postprocess":
        return cmd_postprocess(argv[1:])
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
