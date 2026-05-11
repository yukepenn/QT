"""
Fixed robust-profile OOW validation (v1) — research-only.

Runs a *small* number of locked profiles (candidate IDs + fixed risk knobs) across fixed windows.

Constraints:
- no broad Layer2 sweep
- no WFO/live/SPY/router
- no candidate YAML edits
- no --use-signal-cache
- raw runs remain local-only under output_root/local_runs/**
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

import numpy as np
import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.combiner.run import run_combiner_fixed_config  # noqa: E402
from src.research.fixed_profile_oow_lib import (  # noqa: E402
    exit_slip_scenarios_table,
    max_drawdown_r,
    metrics_from_trades,
    trades_path_for_postprocess,
)
from src.research.trade_quality_helpers import add_prior_trade_columns  # noqa: E402


WINDOW_BOUNDS = {
    "early_oow": ("2020-01-01", "2022-12-31"),
    "insample_ref": ("2023-01-01", "2024-12-31"),
    "late_oow": ("2025-01-01", "2026-04-30"),
    "full_available": ("2020-01-01", "2026-04-30"),
}


def _git_tip(repo_root: Path) -> str:
    try:
        return subprocess.check_output(["git", "log", "-1", "--oneline"], cwd=str(repo_root), text=True).strip()
    except Exception:
        return "(unavailable)"


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, lineterminator="\n")


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


def _load_profiles(profile_root: Path) -> pd.DataFrame:
    p = profile_root / "fixed_profile_definitions.csv"
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


def _materialize_config(*, max_trades_per_day: int, daily_max_loss_r: float, priority_policy: str) -> dict[str, Any]:
    candidate_root_rel = "src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates"
    return {
        "name": "fixed_robust_profile_oow_v1",
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


@dataclass(frozen=True)
class PlanRow:
    profile_id: str
    window: str
    start_date: str
    end_date: str
    candidate_set: str
    candidate_ids: str
    max_trades_per_day: int
    daily_max_loss_r: float
    priority_policy: str
    config_path_rel: str
    run_dir_rel: str
    status: str


def _build_run_plan(profile_root: Path, *, profiles: list[str], windows: list[str]) -> pd.DataFrame:
    df = _load_profiles(profile_root)
    if profiles:
        df = df[df["profile_id"].astype(str).isin(set(profiles))].copy()
    if df.empty:
        raise ValueError("no profiles selected")

    # materialize one config per profile (locked knobs)
    cfg_dir = profile_root / "local_configs"
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

    rows: list[PlanRow] = []
    for _, r in df.iterrows():
        pid = str(r["profile_id"])
        for wid in windows:
            if wid not in WINDOW_BOUNDS:
                raise KeyError(f"unknown window {wid}")
            st, en = WINDOW_BOUNDS[wid]
            run_dir = profile_root / "local_runs" / _safe_dir(pid) / _safe_dir(wid)
            rows.append(
                PlanRow(
                    profile_id=pid,
                    window=wid,
                    start_date=st,
                    end_date=en,
                    candidate_set=str(r["candidate_set"]),
                    candidate_ids=str(r["candidate_ids"]),
                    max_trades_per_day=int(r["max_trades_per_day"]),
                    daily_max_loss_r=float(r["daily_max_loss_r"]),
                    priority_policy=str(r["priority_policy"]),
                    config_path_rel=str(cfg_paths[pid].relative_to(profile_root)).replace("\\", "/"),
                    run_dir_rel=str(run_dir.relative_to(profile_root)).replace("\\", "/"),
                    status="PLANNED",
                )
            )
    out = pd.DataFrame([x.__dict__ for x in rows])
    return out


def cmd_dry_run(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Dry-run fixed robust-profile OOW plan expansion.")
    p.add_argument("--profile-root", required=True)
    p.add_argument("--profiles", default="")
    p.add_argument("--windows", default="insample_ref,early_oow,late_oow,full_available")
    args = p.parse_args(argv)

    root = Path(args.profile_root)
    if not root.is_absolute():
        root = Path.cwd() / root

    profs = _parse_csv_list(args.profiles, [])
    wins = _parse_csv_list(args.windows, ["insample_ref", "early_oow", "late_oow", "full_available"])
    plan = _build_run_plan(root, profiles=profs, windows=wins)
    _write_csv(plan, root / "run_plan.csv")
    (root / "dry_run_validation.md").write_text(
        "\n".join(
            [
                "# Dry-run validation (fixed robust-profile OOW v1)",
                "",
                f"- rows: **{len(plan)}**",
                f"- profiles: **{len(set(plan['profile_id']))}**",
                f"- windows: **{len(set(plan['window']))}**",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return 0


def cmd_run(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Run fixed robust-profile OOW v1.")
    p.add_argument("--profile-root", required=True)
    p.add_argument("--profiles", default="")
    p.add_argument("--windows", default="insample_ref,early_oow,late_oow,full_available")
    p.add_argument("--data-dir", default="data/raw/ibkr")
    p.add_argument("--skip-existing", action="store_true")
    p.add_argument("--stop-on-fail", action="store_true")
    args = p.parse_args(argv)

    root = Path(args.profile_root)
    if not root.is_absolute():
        root = Path.cwd() / root

    profs = _parse_csv_list(args.profiles, [])
    wins = _parse_csv_list(args.windows, ["insample_ref", "early_oow", "late_oow", "full_available"])
    plan = _build_run_plan(root, profiles=profs, windows=wins)
    _write_csv(plan, root / "run_plan.csv")

    exec_rows: list[dict[str, Any]] = []
    for _, r in plan.iterrows():
        run_dir = root / str(r["run_dir_rel"])
        cfg_path = root / str(r["config_path_rel"])
        pid = str(r["profile_id"])
        wid = str(r["window"])
        st = str(r["start_date"])
        en = str(r["end_date"])
        ids = [x.strip() for x in str(r["candidate_ids"]).split(",") if x.strip()]

        # Skip if latest run already has metrics.json
        latest = sorted((run_dir).glob("run_*/metrics.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if args.skip_existing and latest:
            row = dict(r)
            row.update(
                {
                    "status": "SKIPPED_EXISTING",
                    "exit_code": 0,
                    "error_summary": "",
                    "run_dir_rel": str(run_dir.relative_to(root)).replace("\\", "/"),
                }
            )
            exec_rows.append(row)
            continue

        try:
            combiner_yaml = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            out_dir = run_dir / f"run_{ts}_fixed_robust"
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
                tag="fixed_robust_profile_oow_v1",
            )
            row = dict(r)
            row.update(
                {
                    "status": "OK",
                    "exit_code": 0,
                    "error_summary": "",
                    "run_dir_rel": str(out_dir.relative_to(root)).replace("\\", "/"),
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
                    "run_dir_rel": str(run_dir.relative_to(root)).replace("\\", "/"),
                }
            )
            exec_rows.append(row)
            if args.stop_on_fail:
                break

    ex = pd.DataFrame(exec_rows)
    _write_csv(ex, root / "run_execution_manifest.csv")
    # Sanitized: same as execution manifest but no absolute paths or commands (already none).
    _write_csv(ex, root / "run_execution_manifest_sanitized.csv")
    # If any failures, keep a failed_runs.csv
    failed = ex[ex["status"] == "FAILED"]
    if not failed.empty:
        _write_csv(failed, root / "failed_runs.csv")
        return 1
    # Remove stale failed_runs from prior attempts if any
    fr = root / "failed_runs.csv"
    if fr.is_file():
        try:
            fr.unlink()
        except Exception:
            pass
    return 0


def _discover_latest_runs(root: Path) -> list[tuple[str, str, Path]]:
    runs_root = root / "local_runs"
    best: dict[tuple[str, str], Path] = {}
    for mpath in runs_root.glob("*/*/run_*/metrics.json"):
        run_dir = mpath.parent
        parts = run_dir.relative_to(runs_root).parts
        if len(parts) < 3:
            continue
        pid, wid = parts[0], parts[1]
        key = (pid, wid)
        prev = best.get(key)
        if prev is None or run_dir.stat().st_mtime > prev.stat().st_mtime:
            best[key] = run_dir
    return [(k[0], k[1], v) for k, v in sorted(best.items())]


def _period_cols(t: pd.DataFrame) -> pd.DataFrame:
    tt = t.copy()
    dt = pd.to_datetime(tt["session_date"].astype(str), errors="coerce")
    tt["_year"] = dt.dt.year
    tt["_quarter"] = dt.dt.to_period("Q").astype(str)
    tt["_month"] = dt.dt.to_period("M").astype(str)
    return tt


def cmd_postprocess(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Postprocess fixed robust-profile OOW v1 runs.")
    p.add_argument("--profile-root", required=True)
    p.add_argument("--write-exit-slip", action="store_true")
    args = p.parse_args(argv)

    root = Path(args.profile_root)
    if not root.is_absolute():
        root = Path.cwd() / root

    discovered = _discover_latest_runs(root)
    if not discovered:
        raise RuntimeError("no runs discovered under local_runs/**")

    disc_rows: list[dict[str, Any]] = []
    result_rows: list[dict[str, Any]] = []
    month_parts: list[pd.DataFrame] = []
    quarter_parts: list[pd.DataFrame] = []
    year_parts: list[pd.DataFrame] = []
    exit_rows: list[dict[str, Any]] = []
    tn_rows: list[dict[str, Any]] = []
    dd_rows: list[dict[str, Any]] = []
    slip_parts: list[pd.DataFrame] = []

    for pid, wid, run_dir in discovered:
        mjson = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8")) if (run_dir / "metrics.json").is_file() else {}
        tpath = trades_path_for_postprocess(run_dir)
        if tpath is None or not tpath.is_file():
            # This runner uses run_combiner_fixed_config which writes compact_trades.csv by default.
            ct = run_dir / "compact_trades.csv"
            tpath = ct if ct.is_file() else tpath
        trades = pd.read_csv(tpath) if tpath is not None and tpath.is_file() else pd.DataFrame()
        status = "OK" if not trades.empty else "NOT_RUN"
        met = metrics_from_trades(trades, metrics_json=mjson)

        disc_rows.append(
            {
                "profile_id": pid,
                "window": wid,
                "run_dir_rel": str(run_dir.relative_to(root)).replace("\\", "/"),
                "status": status,
            }
        )

        row = {
            "profile_id": pid,
            "window": wid,
            "run_dir_rel": str(run_dir.relative_to(root)).replace("\\", "/"),
            "status": status,
            **met,
            "start": mjson.get("start", ""),
            "end": mjson.get("end", ""),
            "profit_factor": mjson.get("profit_factor"),
            "max_drawdown_r": mjson.get("max_drawdown_r"),
            "combiner_score": mjson.get("combiner_score"),
        }
        result_rows.append(row)

        if trades.empty:
            continue

        t = _period_cols(trades)
        t["r_multiple"] = pd.to_numeric(t["r_multiple"], errors="coerce").fillna(0.0)

        # Monthly/quarterly/yearly totals
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

        # Drawdown by month (max DD in R units on cumulative sequence within the month)
        for mo, part in t.groupby("month", dropna=False) if "month" in t.columns else t.groupby("_month", dropna=False):
            rs = part["r_multiple"].to_numpy(dtype=float)
            dd = max_drawdown_r(rs)
            dd_rows.append({"profile_id": pid, "window": wid, "month": str(mo), "max_dd_r": float(dd), "trades": int(len(part))})

        # Exit reason counts
        if "exit_reason" in trades.columns:
            ex = trades["exit_reason"].astype(str).value_counts().reset_index()
            ex.columns = ["exit_reason", "count"]
            for _, rr in ex.iterrows():
                exit_rows.append({"profile_id": pid, "window": wid, "exit_reason": str(rr["exit_reason"]), "count": int(rr["count"])})

        # Trade number summary (trade #1/#2 totals)
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

        # Exit/slip overlay scenarios (curated only)
        if args.write_exit_slip:
            label = f"{pid}__{wid}"
            slip_parts.append(exit_slip_scenarios_table(trades, label))

    disc = pd.DataFrame(disc_rows)
    _write_csv(disc, root / "run_discovery_manifest.csv")

    res = pd.DataFrame(result_rows)
    _write_csv(res, root / "fixed_profile_results.csv")

    # Profile-window summary (same as results but sorted)
    pws = res.sort_values(["profile_id", "window"])
    _write_csv(pws, root / "profile_window_summary.csv")

    # Overall profile summary (sum over windows)
    overall = res.groupby("profile_id", dropna=False)[["total_r", "trades", "max_dd_r"]].agg(
        {"total_r": "sum", "trades": "sum", "max_dd_r": "min"}
    ).reset_index()
    _write_csv(overall, root / "profile_overall_summary.csv")

    if month_parts:
        monthly = pd.concat(month_parts, ignore_index=True)
        _write_csv(monthly, root / "monthly_summary.csv")
    else:
        _write_csv(pd.DataFrame(columns=["profile_id", "window", "month", "total_r"]), root / "monthly_summary.csv")

    if quarter_parts:
        quarterly = pd.concat(quarter_parts, ignore_index=True)
        _write_csv(quarterly, root / "quarterly_summary.csv")
    else:
        _write_csv(pd.DataFrame(columns=["profile_id", "window", "quarter", "total_r"]), root / "quarterly_summary.csv")

    if year_parts:
        yearly = pd.concat(year_parts, ignore_index=True)
        _write_csv(yearly, root / "yearly_summary.csv")
    else:
        _write_csv(pd.DataFrame(columns=["profile_id", "window", "year", "total_r"]), root / "yearly_summary.csv")

    if dd_rows:
        _write_csv(pd.DataFrame(dd_rows), root / "drawdown_summary.csv")
    else:
        _write_csv(pd.DataFrame(columns=["profile_id", "window", "month", "max_dd_r", "trades"]), root / "drawdown_summary.csv")

    if tn_rows:
        _write_csv(pd.DataFrame(tn_rows), root / "trade_number_summary.csv")
    else:
        _write_csv(pd.DataFrame(columns=["profile_id", "window", "trade_number_of_day", "total_r"]), root / "trade_number_summary.csv")

    if exit_rows:
        _write_csv(pd.DataFrame(exit_rows), root / "exit_reason_summary.csv")
    else:
        _write_csv(pd.DataFrame(columns=["profile_id", "window", "exit_reason", "count"]), root / "exit_reason_summary.csv")

    if args.write_exit_slip and slip_parts:
        slip = pd.concat(slip_parts, ignore_index=True)
        slip_dir = root / "exit_slip"
        slip_dir.mkdir(parents=True, exist_ok=True)
        _write_csv(slip, slip_dir / "fixed_profile_exit_slip_scenarios.csv")

    # Minimal markdown summary
    lines = [
        "# Fixed robust-profile OOW v1 — summary (curated)",
        "",
        f"- discovered runs: **{len(disc)}**",
        f"- OK runs: **{int((disc['status']=='OK').sum())}**",
        "",
        "See `profile_window_summary.csv` and `monthly_summary.csv` for detailed tables.",
        "",
    ]
    (root / "fixed_profile_summary.md").write_text("\n".join(lines), encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Fixed robust-profile OOW validation v1.")
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

