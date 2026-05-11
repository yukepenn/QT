"""
Local detailed Champion v0 trade-context replay (v1) — research-only.

Goal:
- Regenerate detailed row-level trades for Champion v0 profiles (local-only).
- Build a local-only row-level trade-context panel with **decision-time** (signal bar) context,
  using backward merge_asof joins (no lookahead).
- Commit only small aggregated diagnostics + reports.

Hard constraints:
- Do NOT edit strategy YAMLs, signal semantics, or combiner production code.
- Do NOT commit raw trades or row-level panels.
"""

from __future__ import annotations

import argparse
import json
import re
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

from src.data.read_bars import read_bars  # noqa: E402
from src.features.build_features import build_basic_features  # noqa: E402
from src.research.trade_quality_helpers import (  # noqa: E402
    REGIME_LABEL_MAP,
    TRADE_MODE_MAP,
    ALWAYS_IN_MAP,
    add_prior_trade_columns,
    enum_label,
    merge_features_asof_backward,
    profit_factor_r,
)


WINDOW_BOUNDS = {
    "early_oow": ("2020-01-01", "2022-12-31"),
    "insample_ref": ("2023-01-01", "2024-12-31"),
    "late_oow": ("2025-01-01", "2026-04-30"),
    "full_available": ("2020-01-01", "2026-04-30"),
}


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, lineterminator="\n")


def _safe_dir(s: str) -> str:
    s2 = str(s).strip().replace(" ", "_").replace("/", "_").replace("\\", "_")
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", s2)


def _parse_list(s: str) -> list[str]:
    return [x.strip() for x in str(s).split(",") if x.strip()]


def _git_tip() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(_ROOT), text=True).strip()
    except Exception:
        return "UNKNOWN"


def _load_fixed_profiles_defs(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"profile_id", "candidate_ids", "max_trades_per_day", "daily_max_loss_r", "priority_policy"}
    miss = sorted(required - set(df.columns))
    if miss:
        raise ValueError(f"fixed_profile_definitions missing columns: {miss}")
    return df


def _materialize_combiner_cfg(*, max_trades_per_day: int, daily_max_loss_r: float, priority_policy: str) -> dict[str, Any]:
    # Keep consistent with Layer3 smoke / fixed OOW v1 runner defaults.
    candidate_root_rel = "src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates"
    return {
        "name": "local_trade_context_replay_v1",
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


def _run_combiner_cli(
    *,
    cfg_path: Path,
    output_root: Path,
    start: str,
    end: str,
    candidate_ids: list[str],
    data_dir: str,
    no_signal_cache: bool,
    detailed: bool = False,
) -> None:
    # Use combiner CLI so we get full `trades.csv` including `signal_ts_utc` / `signal_idx`.
    output_root.mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    cand_root = cfg.get("candidate_root")
    if not cand_root:
        raise ValueError("config missing candidate_root")
    cmd = [
        sys.executable,
        "-m",
        "src.combiner.run",
        "--candidate-root",
        str(cand_root),
        "--config",
        str(cfg_path),
        "--asset",
        "equity",
        "--symbol",
        "QQQ",
        "--start",
        start,
        "--end",
        end,
        "--candidate-ids",
        *candidate_ids,
        "--top-per-strategy",
        "999",
        "--output-root",
        str(output_root),
        "--tag",
        "local_trade_context_replay_v1",
    ]
    # Combiner CLI enables disk cache only with --use-signal-cache; absence means "no cache".
    # Keep the --no-signal-cache flag in this replay runner for explicitness.
    if not detailed:
        cmd.append("--no-detailed")
    cmd += ["--data-dir", data_dir]
    subprocess.check_call(cmd, cwd=str(_ROOT))


def _decision_ts(trades: pd.DataFrame, *, source: str) -> tuple[pd.Series, pd.Series]:
    """
    Returns (decision_context_ts_utc, decision_context_source).
    """
    if source == "signal_or_previous_bar":
        if "signal_ts_utc" in trades.columns:
            ts = pd.to_datetime(trades["signal_ts_utc"], utc=True, errors="coerce")
            ok = ts.notna()
            out = ts.copy()
            if "entry_ts_utc" in trades.columns and "entry_idx" in trades.columns and "signal_idx" in trades.columns:
                # Invariant (expected): entry_idx = signal_idx + 1 for most trades; still allow.
                pass
            src = pd.Series(np.where(ok, "signal_ts_utc", "previous_bar_before_entry"), index=trades.index, dtype="string")
            # fallback handled later if needed
            return out, src
        # fallthrough: previous bar
        source = "previous_bar_before_entry"

    if source == "previous_bar_before_entry":
        if "entry_ts_utc" not in trades.columns:
            return pd.Series(pd.NaT, index=trades.index), pd.Series(["missing_entry_ts"] * len(trades), dtype="string")
        # Approx: decision timestamp is 1 minute before entry_ts (RTH bars are 1-min).
        ent = pd.to_datetime(trades["entry_ts_utc"], utc=True, errors="coerce")
        return ent - pd.Timedelta(minutes=1), pd.Series(["previous_bar_before_entry"] * len(trades), dtype="string")

    raise ValueError(f"unknown decision context source: {source}")


def _pick_feature_cols(feats: pd.DataFrame, w: int) -> list[str]:
    base = [
        "minute_from_open",
        f"pa_regime_label_{w}",
        f"pa_trade_mode_{w}",
        f"pa_always_in_side_{w}",
        f"trend_score_{w}",
        f"range_efficiency_{w}",
        f"vwap_cross_count_{w}",
        f"pa_trading_range_score_{w}",
        f"pa_climax_score_{w}",
        f"pa_late_trend_score_{w}",
        "pa_distance_from_vwap_atr",
        f"vwap_slope_{w}",
        "close_above_vwap",
        "close_below_vwap",
        "above_orb_high",
        "below_orb_low",
        "near_prior_close_atr",
    ]
    # include any near_*_atr magnet features when present
    near = [c for c in feats.columns if str(c).startswith("near_") and str(c).endswith("_atr")]
    cols = [c for c in base if c in feats.columns]
    for c in near:
        if c not in cols:
            cols.append(c)
    return ["ts_utc"] + cols


def _enrich_with_decision_context(
    trades: pd.DataFrame,
    feats: pd.DataFrame,
    *,
    windows: list[int],
    decision_ts_col: str = "decision_context_ts_utc",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    out = trades.copy()
    meta: dict[str, Any] = {"rows_in": int(len(trades)), "rows_out": int(len(trades)), "context_windows": windows}

    out[decision_ts_col] = pd.to_datetime(out[decision_ts_col], utc=True, errors="coerce")
    fts = feats.copy()
    fts["ts_utc"] = pd.to_datetime(fts["ts_utc"], utc=True, errors="coerce")

    merged_any = []
    missing_by_window: dict[int, list[str]] = {}
    for w in windows:
        cols = _pick_feature_cols(fts, w)
        missing = [c for c in cols if c != "ts_utc" and c not in fts.columns]
        missing_by_window[w] = missing
        fsub = fts[cols].copy()
        m = merge_features_asof_backward(out[[decision_ts_col]].join(out.drop(columns=[decision_ts_col])), fsub, trade_ts_col=decision_ts_col, feature_ts_col="ts_utc")
        # rename merged feature cols with decision_ prefix per window semantics
        for c in cols:
            if c == "ts_utc":
                continue
            new = f"decision_{c}"
            if new not in m.columns and c in m.columns:
                m[new] = m[c]
        merged_any.append(m)
        out = m

    meta["missing_feature_columns_by_window"] = missing_by_window
    # Join success proxy: any regime label present for smallest window, else minute_from_open
    w0 = int(windows[0]) if windows else 20
    key = f"decision_pa_regime_label_{w0}"
    if key in out.columns:
        meta["context_join_success_rows"] = int(out[key].notna().sum())
    elif "decision_minute_from_open" in out.columns:
        meta["context_join_success_rows"] = int(out["decision_minute_from_open"].notna().sum())
    else:
        meta["context_join_success_rows"] = 0
    return out, meta


def _map_context_bucket(row: pd.Series) -> str:
    # Conservative: derive from trade mode if present; else unknown_mixed.
    for w in (20, 30, 60):
        c = f"decision_pa_trade_mode_{w}"
        if c in row.index and pd.notna(row[c]):
            lab = enum_label(TRADE_MODE_MAP, row[c])
            if lab == "trend_long":
                return "trend_long"
            if lab == "trend_short":
                return "trend_short_diagnostic"
            if lab == "range_mode":
                return "trading_range"
            if lab == "climax_mode":
                return "late_climax"
            return "unknown_mixed"
    return "unknown_mixed"


def _add_derived_fields(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # decision labels
    for w in (20, 30, 60):
        if f"decision_pa_regime_label_{w}" in out.columns:
            out[f"decision_pa_regime_label_{w}_label"] = out[f"decision_pa_regime_label_{w}"].map(
                lambda x: enum_label(REGIME_LABEL_MAP, x)
            )
        if f"decision_pa_trade_mode_{w}" in out.columns:
            out[f"decision_pa_trade_mode_{w}_label"] = out[f"decision_pa_trade_mode_{w}"].map(
                lambda x: enum_label(TRADE_MODE_MAP, x)
            )
        if f"decision_pa_always_in_side_{w}" in out.columns:
            out[f"decision_pa_always_in_side_{w}_label"] = out[f"decision_pa_always_in_side_{w}"].map(
                lambda x: enum_label(ALWAYS_IN_MAP, x)
            )

    out["context_bucket"] = out.apply(_map_context_bucket, axis=1).astype("string")
    # minimal weak-period flag from expanded stability weak periods
    if "period_quarter" in out.columns:
        out["weak_period_flag"] = out["period_quarter"].isin(["2025Q1", "2022Q4", "2023Q3"])
    else:
        out["weak_period_flag"] = False
    return out


def _add_market_context_label(df: pd.DataFrame, expanded_root: Path) -> pd.DataFrame:
    out = df.copy()
    # Use the labeled table (contains `context_label`) produced by expanded stability.
    mpath = expanded_root / "market_context_labels.csv"
    if not mpath.is_file():
        out["market_context_label"] = "unknown_mixed"
        return out
    m = pd.read_csv(mpath)
    if "period" not in m.columns or "context_label" not in m.columns:
        out["market_context_label"] = "unknown_mixed"
        return out
    # period is YYYY-MM in monthly file
    out["period_month"] = pd.to_datetime(out["session_date"].astype(str), errors="coerce").dt.strftime("%Y-%m")
    if "period_kind" in m.columns:
        m = m[m["period_kind"].astype(str) == "month"].copy()
    mm = m[["period", "context_label"]].drop_duplicates()
    out = out.merge(mm, left_on="period_month", right_on="period", how="left")
    out = out.drop(columns=["period"], errors="ignore")
    out["market_context_label"] = out["context_label"].fillna("unknown_mixed").astype("string")
    out = out.drop(columns=["context_label"], errors="ignore")
    return out


def _compute_period_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    sd = pd.to_datetime(out["session_date"].astype(str), errors="coerce")
    out["period_month"] = sd.dt.strftime("%Y-%m")
    out["period_quarter"] = sd.dt.to_period("Q").astype(str)
    return out


def _aggregate_basic(df: pd.DataFrame, *, group_cols: list[str]) -> pd.DataFrame:
    g = df.groupby(group_cols, dropna=False)
    rows = g["r_multiple"].agg(trades="count", total_r="sum", avg_r="mean", median_r="median").reset_index()
    rows["win_rate"] = g["r_multiple"].apply(lambda s: float((s > 0).mean()) if len(s) else 0.0).values
    rows["pf_r"] = g["r_multiple"].apply(lambda s: float(profit_factor_r(s)) if len(s) else 0.0).values
    return rows


@dataclass(frozen=True)
class PlanRow:
    profile_id: str
    window: str
    start: str
    end: str
    candidate_ids: list[str]
    max_trades_per_day: int
    daily_max_loss_r: float
    priority_policy: str
    cfg_path_rel: str
    run_dir_rel: str


def _build_plan(
    *,
    output_root: Path,
    fixed_defs: pd.DataFrame,
    profiles: list[str],
    windows: list[str],
) -> tuple[pd.DataFrame, dict[str, Path]]:
    df = fixed_defs.copy()
    if profiles:
        df = df[df["profile_id"].astype(str).isin(set(profiles))].copy()
    if df.empty:
        raise ValueError("no profiles selected")

    cfg_dir = output_root / "local_configs"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_paths: dict[str, Path] = {}
    for _, r in df.iterrows():
        pid = str(r["profile_id"])
        cfg = _materialize_combiner_cfg(
            max_trades_per_day=int(r["max_trades_per_day"]),
            daily_max_loss_r=float(r["daily_max_loss_r"]),
            priority_policy=str(r["priority_policy"]),
        )
        p = cfg_dir / f"{_safe_dir(pid)}.yaml"
        p.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        cfg_paths[pid] = p

    rows: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        pid = str(r["profile_id"])
        ids = [x.strip() for x in str(r["candidate_ids"]).split(",") if x.strip()]
        for w in windows:
            if w not in WINDOW_BOUNDS:
                raise KeyError(f"unknown window {w}")
            st, en = WINDOW_BOUNDS[w]
            run_parent = output_root / "local_runs" / _safe_dir(pid) / _safe_dir(w)
            rows.append(
                PlanRow(
                    profile_id=pid,
                    window=w,
                    start=st,
                    end=en,
                    candidate_ids=ids,
                    max_trades_per_day=int(r["max_trades_per_day"]),
                    daily_max_loss_r=float(r["daily_max_loss_r"]),
                    priority_policy=str(r["priority_policy"]),
                    cfg_path_rel=str(cfg_paths[pid].relative_to(output_root)).replace("\\", "/"),
                    run_dir_rel=str(run_parent.relative_to(output_root)).replace("\\", "/"),
                ).__dict__
            )
    return pd.DataFrame(rows), cfg_paths


def cmd_dry_run(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Dry-run local detailed trade context replay plan (v1).")
    p.add_argument("--playbook-root", required=True)
    p.add_argument("--complete-smoke-root", required=True)
    p.add_argument("--expanded-stability-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--profiles", default="pa_only_mtp1_meta,pa_gap_mtp2_meta,primary_mtp2_meta")
    p.add_argument("--windows", default="early_oow,insample_ref,late_oow,full_available")
    p.add_argument("--context-windows", default="20,30,60")
    p.add_argument("--decision-context-source", default="signal_or_previous_bar")
    args = p.parse_args(argv)

    out = Path(args.output_root)
    if not out.is_absolute():
        out = Path.cwd() / out
    out.mkdir(parents=True, exist_ok=True)

    fixed_defs = _load_fixed_profiles_defs(Path("src/research/results/fixed_robust_profile_oow_v1/fixed_profile_definitions.csv"))
    plan, _ = _build_plan(
        output_root=out,
        fixed_defs=fixed_defs,
        profiles=_parse_list(args.profiles),
        windows=_parse_list(args.windows),
    )
    _write_csv(plan, out / "dry_run_plan.csv")

    lines = [
        "# Dry-run validation — local_detailed_trade_context_replay_v1",
        "",
        f"- git_tip: `{_git_tip()}`",
        f"- planned_rows: **{len(plan)}**",
        f"- profiles: **{plan['profile_id'].nunique()}**",
        f"- windows: **{plan['window'].nunique()}**",
        f"- context_windows: `{args.context_windows}`",
        f"- decision_context_source: `{args.decision_context_source}`",
        "",
        "## Policy",
        "- Row-level outputs under `local_rows/**` are **local-only** (gitignored).",
        "- Aggregates under `aggregates/**` are intended for commit.",
        "",
    ]
    (out / "dry_run_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    _write_csv(
        pd.DataFrame(
            [
                {
                    "ok": True,
                    "planned_rows": int(len(plan)),
                    "planned_profiles": int(plan["profile_id"].nunique()),
                    "planned_windows": int(plan["window"].nunique()),
                    "decision_context_source": str(args.decision_context_source),
                }
            ]
        ),
        out / "dry_run_validation.csv",
    )
    return 0


def cmd_run(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Execute local detailed trade context replay (v1).")
    p.add_argument("--playbook-root", required=True)
    p.add_argument("--complete-smoke-root", required=True)
    p.add_argument("--expanded-stability-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--profiles", default="pa_only_mtp1_meta,pa_gap_mtp2_meta,primary_mtp2_meta")
    p.add_argument("--windows", default="early_oow,insample_ref,late_oow,full_available")
    p.add_argument("--context-windows", default="20,30,60")
    p.add_argument("--decision-context-source", default="signal_or_previous_bar")
    p.add_argument("--data-dir", default="data/raw/ibkr")
    p.add_argument("--no-signal-cache", action="store_true", default=False)
    p.add_argument("--skip-existing", action="store_true", default=False)
    p.add_argument("--stop-on-fail", action="store_true", default=False)
    p.add_argument("--local-only-row-output", action="store_true", default=False)
    p.add_argument("--aggregate-commit-output", action="store_true", default=False)
    args = p.parse_args(argv)

    out = Path(args.output_root)
    if not out.is_absolute():
        out = Path.cwd() / out
    out.mkdir(parents=True, exist_ok=True)

    playbook_root = Path(args.playbook_root)
    expanded_root = Path(args.expanded_stability_root)
    complete_smoke_root = Path(args.complete_smoke_root)

    fixed_defs = _load_fixed_profiles_defs(Path("src/research/results/fixed_robust_profile_oow_v1/fixed_profile_definitions.csv"))
    profs = _parse_list(args.profiles)
    wins = _parse_list(args.windows)
    ctx_ws = [int(x) for x in _parse_list(args.context_windows)]

    plan, _ = _build_plan(output_root=out, fixed_defs=fixed_defs, profiles=profs, windows=wins)
    _write_csv(plan, out / "run_plan.csv")

    exec_rows: list[dict[str, Any]] = []
    local_trades_parts: list[pd.DataFrame] = []

    # Pre-load market context monthly (small) if available
    for _, r in plan.iterrows():
        pid = str(r["profile_id"])
        wid = str(r["window"])
        st = str(r["start"])
        en = str(r["end"])
        ids = list(r["candidate_ids"])
        cfg_path = out / str(r["cfg_path_rel"])
        run_parent = out / str(r["run_dir_rel"])

        latest = sorted(run_parent.glob("run_*/metrics.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if args.skip_existing and latest:
            exec_rows.append(
                {
                    **dict(r),
                    "status": "REUSED_EXISTING",
                    "run_dir_rel_effective": str(latest[0].parent.relative_to(out)).replace("\\", "/"),
                }
            )
            continue

        try:
            # execute combiner replay (writes trades.csv)
            _run_combiner_cli(
                cfg_path=cfg_path,
                output_root=run_parent,
                start=st,
                end=en,
                candidate_ids=ids,
                data_dir=args.data_dir,
                no_signal_cache=bool(args.no_signal_cache),
                detailed=False,
            )
            latest = sorted(run_parent.glob("run_*/metrics.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            rd = latest[0].parent if latest else run_parent
            exec_rows.append(
                {
                    **dict(r),
                    "status": "OK",
                    "run_dir_rel_effective": str(rd.relative_to(out)).replace("\\", "/"),
                }
            )
        except Exception as e:  # noqa: BLE001
            exec_rows.append(
                {
                    **dict(r),
                    "status": "FAILED",
                    "error": repr(e),
                    "run_dir_rel_effective": str(run_parent.relative_to(out)).replace("\\", "/"),
                }
            )
            if args.stop_on_fail:
                break
            continue

    ex = pd.DataFrame(exec_rows)
    _write_csv(ex, out / "run_execution_manifest.csv")

    # sanitized manifest: remove local absolute paths by only storing rel paths (already rel)
    san = ex.copy()
    _write_csv(san, out / "run_execution_manifest_sanitized.csv")

    failed = ex[ex["status"] == "FAILED"]
    if not failed.empty:
        _write_csv(failed, out / "failed_detailed_replay.csv")
        return 1

    # Build local row panel (local-only)
    if args.local_only_row_output:
        local_root = out / "local_rows"
        local_root.mkdir(parents=True, exist_ok=True)

        # Load features per window once, and join by decision timestamp.
        features_cache: dict[str, pd.DataFrame] = {}

        for _, r in ex.iterrows():
            if str(r["status"]) not in ("OK", "REUSED_EXISTING"):
                continue
            pid = str(r["profile_id"])
            wid = str(r["window"])
            st = str(r["start"])
            en = str(r["end"])
            run_dir = out / str(r["run_dir_rel_effective"])
            trades_path = run_dir / "trades.csv"
            if not trades_path.is_file():
                continue
            trades = pd.read_csv(trades_path)
            if trades.empty:
                continue
            trades["profile_id"] = pid
            trades["window"] = wid

            # Ensure UTC timestamps and session_date
            if "session_date" not in trades.columns and "signal_ts_utc" in trades.columns:
                trades["session_date"] = pd.to_datetime(trades["signal_ts_utc"], utc=True, errors="coerce").dt.tz_convert("America/New_York").dt.date.astype(str)

            # decision timestamp
            dts, dsrc = _decision_ts(trades, source=str(args.decision_context_source))
            trades["decision_context_ts_utc"] = dts
            trades["decision_context_source"] = dsrc

            # features
            if wid not in features_cache:
                bars = read_bars(asset="equity", symbol="QQQ", start=st, end=en, data_dir=args.data_dir)
                if bars.empty:
                    raise RuntimeError(f"bars empty for window {wid} {st}..{en}")
                feats = build_basic_features(bars, copy=True, allow_overwrite=False)
                features_cache[wid] = feats
            feats = features_cache[wid]

            enriched, meta = _enrich_with_decision_context(trades, feats, windows=ctx_ws, decision_ts_col="decision_context_ts_utc")
            enriched = _compute_period_cols(enriched)
            enriched = _add_market_context_label(enriched, expanded_root=expanded_root)
            enriched = _add_derived_fields(enriched)

            # prior trade columns (session_date + decision ordering)
            if "session_date" in enriched.columns and "entry_ts_utc" in enriched.columns:
                enriched = add_prior_trade_columns(
                    enriched,
                    session_col="session_date",
                    entry_ts_col="entry_ts_utc",
                    strategy_col="strategy",
                    family_col="strategy_family",
                    r_col="r_multiple",
                )
            # save per-run local copy (optional)
            per_run_out = local_root / "trades" / _safe_dir(pid) / _safe_dir(wid)
            per_run_out.mkdir(parents=True, exist_ok=True)
            enriched.to_csv(per_run_out / "trades_enriched_local.csv", index=False)
            (per_run_out / "enrich_meta.json").write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")

            local_trades_parts.append(enriched)

        if local_trades_parts:
            panel = pd.concat(local_trades_parts, ignore_index=True)
        else:
            panel = pd.DataFrame()

        panel_path = local_root / "trade_context_panel.csv"
        panel.to_csv(panel_path, index=False)

        inv = pd.DataFrame(
            [
                {
                    "git_tip": _git_tip(),
                    "panel_rows": int(len(panel)),
                    "panel_path_local_only": str(panel_path.relative_to(out)).replace("\\", "/"),
                    "policy": "LOCAL_ONLY_NOT_COMMITTED",
                }
            ]
        )
        _write_csv(inv, out / "local_row_artifact_inventory.csv")
        (out / "row_level_commit_blocklist.md").write_text(
            "\n".join(
                [
                    "# Row-level commit blocklist",
                    "",
                    "Do NOT commit:",
                    "- `local_rows/**`",
                    "- `trades.csv` / `trades_enriched_local.csv`",
                    "",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    # Produce aggregates (committable)
    if args.aggregate_commit_output:
        agg_root = out / "aggregates"
        agg_root.mkdir(parents=True, exist_ok=True)

        panel_path = out / "local_rows" / "trade_context_panel.csv"
        if not panel_path.is_file():
            # still write an empty coverage file so the run is explainable
            _write_csv(pd.DataFrame([{"note": "local panel missing; run with --local-only-row-output"}]), agg_root / "trade_context_coverage.csv")
            return 0
        try:
            panel = pd.read_csv(panel_path)
        except pd.errors.EmptyDataError:
            panel = pd.DataFrame()
        if panel.empty:
            _write_csv(pd.DataFrame([{"note": "local panel empty"}]), agg_root / "trade_context_coverage.csv")
            return 0

        # Coverage
        cov = {
            "total_trades": int(len(panel)),
            "rows_with_signal_ts": int(pd.to_datetime(panel.get("signal_ts_utc", pd.Series(dtype=str)), errors="coerce").notna().sum()) if "signal_ts_utc" in panel.columns else 0,
        }
        key = "decision_pa_regime_label_20"
        cov["rows_with_decision_regime_20"] = int(panel[key].notna().sum()) if key in panel.columns else 0
        cov["rows_with_market_context_label"] = int(panel["market_context_label"].notna().sum()) if "market_context_label" in panel.columns else 0
        _write_csv(pd.DataFrame([cov]), agg_root / "trade_context_coverage.csv")

        # Basic summaries
        _write_csv(_aggregate_basic(panel, group_cols=["profile_id"]), agg_root / "panel_profile_summary.csv")
        _write_csv(_aggregate_basic(panel, group_cols=["profile_id", "window"]), agg_root / "panel_window_summary.csv")
        if "candidate_id" in panel.columns:
            _write_csv(_aggregate_basic(panel, group_cols=["profile_id", "window", "candidate_id"]), agg_root / "panel_candidate_summary.csv")
        if "context_bucket" in panel.columns:
            _write_csv(_aggregate_basic(panel, group_cols=["profile_id", "window", "context_bucket"]), agg_root / "panel_context_bucket_summary.csv")
        if "market_context_label" in panel.columns:
            _write_csv(_aggregate_basic(panel, group_cols=["profile_id", "window", "market_context_label"]), agg_root / "panel_market_context_summary.csv")
        if "exit_reason" in panel.columns:
            _write_csv(_aggregate_basic(panel, group_cols=["profile_id", "window", "exit_reason"]), agg_root / "panel_exit_reason_summary.csv")
        if "daily_trade_number" in panel.columns:
            _write_csv(_aggregate_basic(panel, group_cols=["profile_id", "window", "daily_trade_number"]), agg_root / "panel_trade_number_summary.csv")
        if "entry_prior_trade_pnl_r" in panel.columns:
            tmp = panel.copy()
            tmp["prior_trade_was_loss"] = pd.to_numeric(tmp["entry_prior_trade_pnl_r"], errors="coerce") < 0
            _write_csv(_aggregate_basic(tmp, group_cols=["profile_id", "window", "prior_trade_was_loss"]), agg_root / "panel_prior_trade_summary.csv")
        if "weak_period_flag" in panel.columns:
            _write_csv(_aggregate_basic(panel, group_cols=["profile_id", "window", "weak_period_flag"]), agg_root / "panel_weak_period_summary.csv")

        # Regime summary (label form when available)
        lab = "decision_pa_regime_label_20_label"
        if lab in panel.columns:
            _write_csv(_aggregate_basic(panel, group_cols=["profile_id", "window", lab]), agg_root / "panel_regime_summary.csv")
        else:
            _write_csv(pd.DataFrame([{"note": "decision_pa_regime_label_20_label missing"}]), agg_root / "panel_regime_summary.csv")

        (agg_root / "panel_context_summary.md").write_text(
            "\n".join(
                [
                    "# panel_context_summary",
                    "",
                    "All aggregates are derived from a **local-only** row-level panel. Do not commit row-level files.",
                    "",
                    f"- local panel: `{(out / 'local_rows' / 'trade_context_panel.csv').as_posix()}` (gitignored)",
                    f"- aggregates: `{agg_root.as_posix()}`",
                    "",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Local detailed trade context replay v1 (research-only).")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("dry-run")
    sub.add_parser("run")
    ns, rest = p.parse_known_args(argv)
    if ns.cmd == "dry-run":
        return cmd_dry_run(rest)
    if ns.cmd == "run":
        return cmd_run(rest)
    raise AssertionError(ns.cmd)


if __name__ == "__main__":
    raise SystemExit(main())

