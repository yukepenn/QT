"""Execution-path exit overlay diagnostic — TradeIntent + ExitPlan + simulate_trade_path only.

No independent PnL engine. Baseline uses ``simulate_combiner_canonical``; overlays replay each
baseline trade with modified :class:`ExitPlan` / :class:`TradeIntent` via
:func:`src.execution.path.simulate_trade_path` (per-trade sensitivity, not full combiner re-cursor).
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.combiner.adapter import _bars_dataframe, simulate_combiner_canonical
from src.combiner.candidate import encode_candidate_metadata
from src.combiner.precompute import precompute_candidate_signal_matrices
from src.combiner.run import (
    _build_execution_arrays,
    _combiner_cfg_from_yaml,
    apply_combiner_rules,
    filter_candidates,
    load_candidates,
    resolve_precompute_signal_cache_settings,
    validate_common_combiner_config,
)
from src.combiner.trade_intent_adapter import (
    build_trade_intent_from_candidate,
    execution_policy_from_combiner_cfg,
)
from src.execution.path import simulate_trade_path
from src.execution.types import ExitPlan, TradeIntent

from src.research.run_combiner_adapter_parity import discover_candidate_root, discover_combiner_config, resolve_ibkr_data_dir

PROFILE_IDS: dict[str, list[str]] = {
    "pa_only_mtp1_meta": ["PA_BUY_SELL_CLOSE_TREND_003"],
    "pa_gap_mtp2_meta": ["PA_BUY_SELL_CLOSE_TREND_003", "GAP_ACCEPTANCE_FAILURE_001"],
    "primary_mtp2_meta": [
        "PA_BUY_SELL_CLOSE_TREND_003",
        "GAP_ACCEPTANCE_FAILURE_001",
        "CCI_EXTREME_SNAPBACK_003",
    ],
}

OVERLAY_REGISTRY = frozenset(
    {
        "baseline_execution_backed",
        "max_hold_tighten_60",
        "no_followthrough_exit_5bars",
        "trend_swing_2r",
        "trail_after_1r_simple",
        "runner_after_1r_reference",
    }
)


def normalize_overlay_names(raw: str) -> list[str]:
    out: list[str] = []
    for part in raw.split(","):
        p = part.strip().lower().replace("-", "_")
        if p:
            out.append(p)
    return out


def discover_qqq_repo_bounds(data_dir: Path) -> tuple[str, str]:
    sym = data_dir / "equity" / "bars_1min" / "symbol=QQQ"
    if not sym.is_dir():
        return "2024-01-01", "2024-01-31"
    years: list[int] = []
    for yd in sym.glob("year=*"):
        try:
            years.append(int(yd.name.split("=")[1]))
        except (IndexError, ValueError):
            continue
    if not years:
        return "2024-01-01", "2024-01-31"
    y0, y1 = min(years), max(years)
    m0 = min(int(p.name.split("=")[1]) for p in (sym / f"year={y0}").glob("month=*"))
    m1 = max(int(p.name.split("=")[1]) for p in (sym / f"year={y1}").glob("month=*"))
    import calendar

    start = f"{y0}-{m0:02d}-01"
    last = calendar.monthrange(y1, m1)[1]
    end = f"{y1}-{m1:02d}-{last:02d}"
    return start, end


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def apply_overlay(
    overlay: str,
    intent: TradeIntent,
    *,
    max_hold_bars: int | None,
    combiner_cfg: Any,
) -> tuple[TradeIntent | None, ExitPlan | None, str, str]:
    del combiner_cfg  # reserved for future policy-aware overlays
    if overlay == "baseline_execution_backed":
        plan = ExitPlan()
        if max_hold_bars is not None and max_hold_bars > 0:
            plan = ExitPlan(max_hold_bars_cap=int(max_hold_bars))
        return intent, plan, "supported", "adapter-equivalent max_hold cap"

    if overlay == "max_hold_tighten_60":
        cap = 60
        if max_hold_bars is not None and max_hold_bars > 0:
            cap = min(60, int(max_hold_bars))
        return intent, ExitPlan(max_hold_bars_cap=cap), "supported", "ExitPlan.max_hold_bars_cap"

    if overlay == "no_followthrough_exit_5bars":
        return (
            intent,
            ExitPlan(no_followthrough_bars=5, no_followthrough_min_r=0.05),
            "supported",
            "NO_FOLLOWTHROUGH if unrealized R < 0.05 after 5 bars",
        )

    if overlay == "trend_swing_2r":
        if str(intent.target_mode) != "fixed_r":
            return None, None, "unsupported", "requires fixed_r"
        new_i = dataclasses.replace(intent, target_r=2.0)
        plan = ExitPlan()
        if max_hold_bars is not None and max_hold_bars > 0:
            plan = ExitPlan(max_hold_bars_cap=int(max_hold_bars))
        return new_i, plan, "supported", "target_r=2.0"

    if overlay == "trail_after_1r_simple":
        return None, None, "unsupported", "no arm-after-R threshold on TrailingRule in ExitPlan"

    if overlay == "runner_after_1r_reference":
        return None, None, "unsupported", "runner/scale ladder not in current fixed-R diagnostic contract"

    return None, None, "unsupported", f"unknown overlay {overlay!r}"


def _candidate_index(candidates: list[Any], cid: str) -> int:
    for i, c in enumerate(candidates):
        if c.candidate_id == cid:
            return i
    raise KeyError(cid)


def run_baseline_combiner(
    *,
    combiner_yaml: dict[str, Any],
    candidate_root: Path,
    candidate_ids: list[str],
    symbol: str,
    start: str,
    end: str,
    data_dir: Path,
    profile_csv: Path,
) -> tuple[pd.DataFrame, dict[str, Any], dict[str, np.ndarray], list[Any], Any, np.ndarray]:
    validate_common_combiner_config(combiner_yaml)
    strategy_rules = combiner_yaml.get("strategy_rules") or {}
    use_sc, sc_root, refresh_sc = resolve_precompute_signal_cache_settings(
        combiner_yaml,
        cli_use_signal_cache=False,
        cli_signal_cache_root=None,
        cli_refresh_signal_cache=False,
    )
    raw_specs = load_candidates(candidate_root)
    raw_eligible = [sp for sp in raw_specs if (strategy_rules.get(sp.strategy) or {}).get("enabled", True) is not False]
    merged_specs = filter_candidates(raw_eligible, candidate_ids=candidate_ids, top_per_strategy=None)
    merged: list[Any] = []
    for sp in merged_specs:
        rules = strategy_rules.get(sp.strategy) or {}
        if rules.get("enabled", True) is False:
            continue
        merged.append(apply_combiner_rules(sp, strategy_rules))
    if not merged:
        raise RuntimeError("no candidates after filters")
    profile_csv.parent.mkdir(parents=True, exist_ok=True)
    csm = precompute_candidate_signal_matrices(
        candidates=merged,
        asset="equity",
        symbol=symbol,
        start=start,
        end=end,
        data_dir=str(data_dir),
        profile_csv_path=profile_csv,
        use_signal_cache=use_sc,
        signal_cache_root=sc_root,
        refresh_signal_cache=refresh_sc,
    )
    comb_cfg = _combiner_cfg_from_yaml(combiner_yaml)
    max_hold, recomp, qty, min_risk = _build_execution_arrays(merged, combiner_yaml, comb_cfg)
    _, _, pri, score, rank, ast, aen, _, _, _ = encode_candidate_metadata(merged)
    enabled = np.ones(len(merged), dtype=np.int8)
    bt_arr = csm.backtest_arrays
    mats = {
        "side": csm.side,
        "valid": csm.valid,
        "stop": csm.stop,
        "target_preview": csm.target_preview,
        "target_mode_code": csm.target_mode_code,
        "target_r": csm.target_r,
        "risk_preview": csm.risk_preview,
    }
    meta = csm.meta_arrays
    sim_out = simulate_combiner_canonical(
        backtest_arrays=bt_arr,
        candidate_arrays=mats,
        candidates=merged,
        meta_arrays=meta,
        combiner_cfg=comb_cfg,
        enabled_mask=enabled,
        max_hold_per_candidate=max_hold,
        recompute_target=recomp,
        quantity_per_candidate=qty,
        min_risk_per_candidate=min_risk,
        priority_float=pri,
        score_float=score,
        rank_int=rank,
        active_start=ast,
        active_end=aen,
    )
    trades_df = sim_out["trades_df"]
    return trades_df, bt_arr, meta, merged, comb_cfg, max_hold


def replay_overlay_on_baseline_trades(
    *,
    trades_df: pd.DataFrame,
    bars_df: pd.DataFrame,
    candidates: list[Any],
    max_hold_arr: np.ndarray,
    combiner_cfg: Any,
    overlay: str,
    profile: str,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    unsupported: list[dict[str, Any]] = []
    rows_out: list[dict[str, Any]] = []
    if not len(trades_df):
        return pd.DataFrame(), unsupported

    pol = execution_policy_from_combiner_cfg(combiner_cfg)

    for _, row in trades_df.iterrows():
        cid = str(row["candidate_id"])
        ci = _candidate_index(candidates, cid)
        mh = int(max_hold_arr[ci])
        max_hold = None if mh < 0 else mh
        tmc = int(row["target_mode_code"])
        tpv = float(row.get("target_price", float("nan")))
        try:
            intent = build_trade_intent_from_candidate(
                candidate=candidates[ci],
                ci=ci,
                signal_bar=int(row["signal_idx"]),
                entry_bar=int(row["entry_idx"]),
                side=int(row["side"]),
                stop_price=float(row["stop_price"]),
                target_preview=tpv,
                target_mode_code=tmc,
                target_r=float(row["target_r"]),
                risk_preview=float(row["risk_per_share"]),
                max_hold_bars=max_hold,
                qty=1.0,
            )
        except (ValueError, KeyError) as ex:
            unsupported.append({"overlay": overlay, "candidate_id": cid, "reason": f"intent_build:{ex}"})
            continue

        new_intent, plan, st, note = apply_overlay(overlay, intent, max_hold_bars=max_hold, combiner_cfg=combiner_cfg)
        if st == "unsupported" or new_intent is None or plan is None:
            unsupported.append({"overlay": overlay, "candidate_id": cid, "reason": note})
            continue

        res = simulate_trade_path(bars_df, new_intent, pol, plan)
        er = ""
        if res.ok and res.exit_reason is not None:
            er = str(res.exit_reason.name).lower()
        else:
            er = str(res.reject_reason)
        rows_out.append(
            {
                "profile": profile,
                "overlay": overlay,
                "candidate_id": cid,
                "session_date": row.get("session_date", ""),
                "signal_idx": int(row["signal_idx"]),
                "r_multiple": float(res.r_multiple) if res.ok else 0.0,
                "bars_held": int(res.bars_held) if res.ok else 0,
                "exit_reason": er,
                "ok": bool(res.ok),
            }
        )

    return pd.DataFrame(rows_out), unsupported


def aggregate_replay(df: pd.DataFrame) -> dict[str, Any]:
    if df is None or not len(df):
        return {"trades": 0, "total_r": 0.0, "avg_r": 0.0, "profit_factor_r": "", "exit_reason_counts": ""}
    r = df["r_multiple"].astype(float)
    pos = r[r > 0].sum()
    neg = -r[r < 0].sum()
    pf_s = str(float(pos / neg)) if neg > 0 else ""
    vc = df["exit_reason"].value_counts().to_dict() if "exit_reason" in df.columns else {}
    parts = [f"{k}={v}" for k, v in sorted(vc.items())]
    return {
        "trades": int(len(df)),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "profit_factor_r": pf_s,
        "exit_reason_counts": ";".join(parts),
    }


def aggregate_baseline_trades(trades_df: pd.DataFrame) -> dict[str, Any]:
    if not len(trades_df):
        return {"trades": 0, "total_r": 0.0, "avg_r": 0.0, "profit_factor_r": "", "exit_reason_counts": ""}
    r = trades_df["r_multiple"].astype(float)
    pos = r[r > 0].sum()
    neg = -r[r < 0].sum()
    pf_s = str(float(pos / neg)) if neg > 0 else ""
    vc = trades_df["exit_reason"].value_counts().to_dict() if "exit_reason" in trades_df.columns else {}
    parts = [f"{k}={v}" for k, v in sorted(vc.items())]
    return {
        "trades": int(len(trades_df)),
        "total_r": float(r.sum()),
        "avg_r": float(r.mean()),
        "profit_factor_r": pf_s,
        "exit_reason_counts": ";".join(parts),
    }


def _run_window(
    *,
    out: Path,
    comb_yaml: dict[str, Any],
    cr: Path,
    ids: list[str],
    symbol: str,
    start: str,
    end: str,
    data_dir: Path,
    profile: str,
    overlays: list[str],
    aggregate_only: bool,
    local_row_output: Path | None,
    label_prefix: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], pd.DataFrame, pd.DataFrame]:
    profile_csv = out / "_local_only" / f"candidate_precompute_profile_{label_prefix}_{profile}.csv"
    trades_df, bt_arr, meta, merged, comb_cfg, max_hold = run_baseline_combiner(
        combiner_yaml=comb_yaml,
        candidate_root=cr,
        candidate_ids=ids,
        symbol=symbol,
        start=start,
        end=end,
        data_dir=data_dir,
        profile_csv=profile_csv,
    )
    bars_df = _bars_dataframe(bt_arr, meta)

    all_unsup: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []

    base_agg = aggregate_baseline_trades(trades_df)
    summary_rows.append(
        {
            "window_label": label_prefix,
            "profile": profile,
            "overlay": "baseline_execution_backed",
            "source": "combiner_canonical",
            "trades": base_agg["trades"],
            "total_r": base_agg["total_r"],
            "avg_r": base_agg["avg_r"],
            "profit_factor_r": base_agg["profit_factor_r"],
            "exit_reason_counts": base_agg["exit_reason_counts"],
            "start": start,
            "end": end,
        }
    )

    combined_replay = pd.DataFrame()
    for ov in overlays:
        ov_n = ov.lower().replace("-", "_")
        if ov_n == "baseline_execution_backed":
            continue
        rdf, unsup = replay_overlay_on_baseline_trades(
            trades_df=trades_df,
            bars_df=bars_df,
            candidates=merged,
            max_hold_arr=max_hold,
            combiner_cfg=comb_cfg,
            overlay=ov_n,
            profile=profile,
        )
        all_unsup.extend(unsup)
        agg = aggregate_replay(rdf)
        summary_rows.append(
            {
                "window_label": label_prefix,
                "profile": profile,
                "overlay": ov_n,
                "source": "per_trade_replay",
                "trades": agg["trades"],
                "total_r": agg["total_r"],
                "avg_r": agg["avg_r"],
                "profit_factor_r": agg["profit_factor_r"],
                "exit_reason_counts": agg["exit_reason_counts"],
                "start": start,
                "end": end,
            }
        )
        if len(rdf):
            rdf = rdf.assign(window_label=label_prefix)
            combined_replay = pd.concat([combined_replay, rdf], ignore_index=True) if len(combined_replay) else rdf

    if local_row_output and len(combined_replay):
        lp = local_row_output if local_row_output.is_absolute() else Path.cwd() / local_row_output
        lp.parent.mkdir(parents=True, exist_ok=True)
        combined_replay.to_csv(lp, index=False)

    return summary_rows, all_unsup, combined_replay, trades_df


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Exit overlay diagnostic on execution-backed path")
    p.add_argument("--output-root", type=Path, default=_ROOT / "src/research/results/exit_overlay_execution_path")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--bar-root", type=str, default="data")
    p.add_argument("--data-dir", type=str, default="")
    p.add_argument("--candidate-root", type=Path, default=None)
    p.add_argument("--config", type=Path, default=None)
    p.add_argument("--profile", type=str, required=True, help="Diagnostic profile key (comma-separated for multiple)")
    p.add_argument("--candidate-ids", type=str, default="")
    p.add_argument("--symbol", type=str, default="QQQ")
    p.add_argument("--start", type=str, default="2024-01-01")
    p.add_argument("--end", type=str, default="2024-01-31")
    p.add_argument("--overlays", type=str, required=True)
    p.add_argument("--aggregate-only", action="store_true")
    p.add_argument(
        "--local-row-output",
        action="store_true",
        help="Write per-trade replay rows to output-root/_local_only/ (not for commit)",
    )
    p.add_argument("--skip-existing", action="store_true")
    p.add_argument("--repo-coverage", action="store_true")
    args = p.parse_args(argv)

    out = args.output_root
    if not out.is_absolute():
        out = Path.cwd() / out
    out.mkdir(parents=True, exist_ok=True)

    overlays = normalize_overlay_names(args.overlays)
    for o in overlays:
        on = o.lower().replace("-", "_")
        if on not in OVERLAY_REGISTRY:
            print(f"ERROR unknown overlay {o!r}", file=sys.stderr)
            return 2

    data_dir = resolve_ibkr_data_dir(_ROOT, bar_root=(args.bar_root or "").strip() or None, data_dir=(args.data_dir or "").strip() or None)
    cr = discover_candidate_root(_ROOT, args.candidate_root)
    cfgp = discover_combiner_config(_ROOT, args.config)
    if not cr or not cfgp:
        print(f"ERROR missing candidate_root={cr} config={cfgp}", file=sys.stderr)
        return 2

    profiles = [x.strip() for x in str(args.profile).split(",") if x.strip()]
    if not profiles:
        print("ERROR empty --profile", file=sys.stderr)
        return 2

    cli_ids = [x.strip() for x in (args.candidate_ids or "").split(",") if x.strip()]

    def ids_for_profile(prof: str) -> list[str]:
        if len(profiles) > 1:
            return PROFILE_IDS.get(prof) or []
        if cli_ids:
            return cli_ids
        return PROFILE_IDS.get(prof) or []

    if len(profiles) > 1 and cli_ids:
        print("NOTE: --candidate-ids ignored when multiple --profile values are given", flush=True)

    for prof in profiles:
        ids_chk = ids_for_profile(prof)
        if not ids_chk:
            print(f"ERROR no candidate ids for profile={prof!r}", file=sys.stderr)
            return 2

    if args.dry_run:
        rows = []
        for prof in profiles:
            ids = ids_for_profile(prof)
            rows.append(
                {
                    "profile": prof,
                    "candidate_ids": ",".join(ids),
                    "symbol": args.symbol,
                    "start": args.start,
                    "end": args.end,
                    "data_dir": str(data_dir),
                    "candidate_root": str(cr),
                    "config": str(cfgp),
                    "overlays": ",".join(overlays),
                    "status": "PLANNED",
                }
            )
        keys = list(rows[0].keys())
        _write_csv(out / "dry_run_plan.csv", rows, keys)
        (out / "dry_run_plan.md").write_text(
            f"# Dry run plan\n\n- Profile: `{args.profile}`\n- IDs: {ids}\n"
            f"- Window: {args.start} … {args.end}\n- Data: `{data_dir}`\n- Overlays: {overlays}\n",
            encoding="utf-8",
        )
        _write_csv(
            out / "input_inventory.csv",
            [
                {"key": "data_dir", "value": str(data_dir), "exists": str(data_dir.is_dir())},
                {"key": "candidate_root", "value": str(cr), "exists": str(cr.is_dir())},
                {"key": "config", "value": str(cfgp), "exists": str(cfgp.is_file())},
            ],
            ["key", "value", "exists"],
        )
        (out / "input_inventory.md").write_text("# Inputs\n\nSee `input_inventory.csv`.\n", encoding="utf-8")
        unsup: list[dict[str, Any]] = []
        probe = TradeIntent(
            candidate_id="X",
            strategy="s",
            side=1,
            signal_idx=0,
            entry_idx=1,
            stop_price=99.0,
            max_hold_bars=120,
            management_mode="none",
            target_mode="fixed_r",
            target_r=1.5,
            qty=1.0,
        )
        cfg_probe = _combiner_cfg_from_yaml({"execution": {"slippage_per_share": 0.01, "commission_per_trade": 0.0}})
        for o in overlays:
            on = o.lower().replace("-", "_")
            _, _, st, note = apply_overlay(on, probe, max_hold_bars=120, combiner_cfg=cfg_probe)
            if st == "unsupported":
                unsup.append({"overlay": on, "reason": note})
        if not unsup:
            unsup.append({"overlay": "(structure)", "reason": "see per-run unsupported rows after smoke"})
        _write_csv(out / "unsupported_overlay_capabilities.csv", unsup, ["overlay", "reason"])
        return 0

    summary_path = out / "overlay_smoke_summary.csv"
    if args.skip_existing and summary_path.is_file():
        print("skip-existing: overlay_smoke_summary.csv present", flush=True)
        return 0

    with cfgp.open(encoding="utf-8") as f:
        comb_yaml = yaml.safe_load(f)

    all_summary: list[dict[str, Any]] = []
    all_unsup: list[dict[str, Any]] = []
    smoke_combined = pd.DataFrame()
    smoke_trades = pd.DataFrame()

    for prof in profiles:
        ids_loop = ids_for_profile(prof)
        local_row_path: Path | None = None
        if args.local_row_output:
            local_row_path = out / "_local_only" / f"replay_rows_{prof}_{args.start}_{args.end}.csv"

        rows_u, uns_u, comb_u, tr_u = _run_window(
            out=out,
            comb_yaml=comb_yaml,
            cr=cr,
            ids=ids_loop,
            symbol=args.symbol,
            start=args.start,
            end=args.end,
            data_dir=data_dir,
            profile=prof,
            overlays=overlays,
            aggregate_only=args.aggregate_only,
            local_row_output=local_row_path,
            label_prefix="smoke",
        )
        all_summary.extend(rows_u)
        all_unsup.extend(uns_u)
        if len(comb_u):
            comb_u = comb_u.assign(profile=prof)
            smoke_combined = (
                pd.concat([smoke_combined, comb_u], ignore_index=True) if len(smoke_combined) else comb_u
            )
        if len(tr_u):
            tr_u = tr_u.copy()
            tr_u["diagnostic_profile"] = prof
            smoke_trades = pd.concat([smoke_trades, tr_u], ignore_index=True) if len(smoke_trades) else tr_u

    cov_combined = pd.DataFrame()
    if args.repo_coverage:
        (out / "repo_coverage_not_run_reason.md").unlink(missing_ok=True)
        rs, re_ = discover_qqq_repo_bounds(data_dir)
        cov_rows = [{"period_start": rs, "period_end": re_, "note": "full QQQ partition span in repo data/"}]
        _write_csv(out / "overlay_repo_coverage_by_period.csv", cov_rows, list(cov_rows[0].keys()))
        cov_summary_parts: list[dict[str, Any]] = []
        for prof in profiles:
            ids_loop = ids_for_profile(prof)
            rows_c, uns_c, comb_c, _tr_c = _run_window(
                out=out,
                comb_yaml=comb_yaml,
                cr=cr,
                ids=ids_loop,
                symbol=args.symbol,
                start=rs,
                end=re_,
                data_dir=data_dir,
                profile=prof,
                overlays=overlays,
                aggregate_only=args.aggregate_only,
                local_row_output=None,
                label_prefix="repo_coverage",
            )
            all_summary.extend(rows_c)
            all_unsup.extend(uns_c)
            if len(comb_c):
                comb_c = comb_c.assign(profile=prof)
                cov_combined = (
                    pd.concat([cov_combined, comb_c], ignore_index=True) if len(cov_combined) else comb_c
                )
            cov_summary_parts.extend([r for r in rows_c if r.get("window_label") == "repo_coverage"])
        _write_csv(
            out / "overlay_repo_coverage_summary.csv",
            cov_summary_parts,
            list(cov_summary_parts[0].keys()) if cov_summary_parts else ["window_label", "profile", "overlay", "total_r", "trades"],
        )
        (out / "overlay_repo_coverage_summary.md").write_text(
            f"# Repo coverage\n\nRange **{rs}** … **{re_}**.\n\nSee `overlay_repo_coverage_summary.csv`.\n",
            encoding="utf-8",
        )
        if len(cov_combined):
            g = cov_combined.groupby(["profile", "overlay", "candidate_id"], as_index=False)["r_multiple"].sum()
            g.rename(columns={"r_multiple": "total_r"}, inplace=True)
            g["window_label"] = "repo_coverage"
            _write_csv(out / "overlay_repo_coverage_by_candidate.csv", g.to_dict("records"), list(g.columns))
        else:
            _write_csv(
                out / "overlay_repo_coverage_by_candidate.csv",
                [],
                ["window_label", "profile", "overlay", "candidate_id", "total_r"],
            )
        if len(cov_combined) and "exit_reason" in cov_combined.columns:
            ge = cov_combined.groupby(["profile", "overlay", "exit_reason"]).size().reset_index(name="count")
            _write_csv(out / "overlay_repo_coverage_by_exit_reason.csv", ge.to_dict("records"), list(ge.columns))
        else:
            _write_csv(
                out / "overlay_repo_coverage_by_exit_reason.csv",
                [],
                ["profile", "overlay", "exit_reason", "count"],
            )
    else:
        (out / "repo_coverage_not_run_reason.md").write_text(
            "``--repo-coverage`` not passed; full-span QQQ diagnostic skipped.\n", encoding="utf-8"
        )

    if all_summary:
        _write_csv(summary_path, all_summary, list(all_summary[0].keys()))
    (out / "overlay_smoke_summary.md").write_text(
        "# Overlay smoke summary\n\nSee `overlay_smoke_summary.csv`.\n", encoding="utf-8"
    )
    by_prof = [r for r in all_summary if r.get("window_label") == "smoke"]
    _write_csv(out / "overlay_by_profile.csv", by_prof, list(by_prof[0].keys()) if by_prof else ["empty"])

    if len(smoke_combined):
        gc = smoke_combined.groupby(["profile", "overlay", "candidate_id"], as_index=False)["r_multiple"].sum()
        gc["window_label"] = "smoke"
        _write_csv(out / "overlay_by_candidate.csv", gc.to_dict("records"), list(gc.columns))
        ge = smoke_combined.groupby(["profile", "overlay", "exit_reason"]).size().reset_index(name="count")
        ge["window_label"] = "smoke"
        _write_csv(out / "overlay_by_exit_reason.csv", ge.to_dict("records"), list(ge.columns))
        gb = smoke_combined.groupby(["profile", "overlay", "bars_held"]).size().reset_index(name="count")
        gb["window_label"] = "smoke"
        _write_csv(out / "overlay_by_bars_held.csv", gb.to_dict("records"), list(gb.columns))
    else:
        _write_csv(
            out / "overlay_by_candidate.csv",
            [],
            ["window_label", "profile", "overlay", "candidate_id", "r_multiple"],
        )
        _write_csv(
            out / "overlay_by_exit_reason.csv",
            [],
            ["window_label", "profile", "overlay", "exit_reason", "count"],
        )
        _write_csv(
            out / "overlay_by_bars_held.csv",
            [],
            ["window_label", "profile", "overlay", "bars_held", "count"],
        )

    dtn_rows: list[dict[str, Any]] = []
    if len(smoke_trades) and "daily_trade_number" in smoke_trades.columns:
        for _, row in smoke_trades.iterrows():
            dtn_rows.append(
                {
                    "window_label": "smoke",
                    "profile": row.get("diagnostic_profile", ""),
                    "overlay": "baseline_execution_backed",
                    "daily_trade_number": row.get("daily_trade_number", ""),
                    "r_multiple": row.get("r_multiple", ""),
                }
            )
    _write_csv(
        out / "overlay_by_trade_number.csv",
        dtn_rows,
        ["window_label", "profile", "overlay", "daily_trade_number", "r_multiple"],
    )

    seen_un: set[tuple[Any, ...]] = set()
    uns_dedup: list[dict[str, Any]] = []
    for u in all_unsup:
        k = (u.get("overlay"), u.get("candidate_id"), u.get("reason"))
        if k in seen_un:
            continue
        seen_un.add(k)
        uns_dedup.append(u)
    _write_csv(
        out / "overlay_unsupported.csv",
        uns_dedup,
        ["overlay", "candidate_id", "reason"] if uns_dedup else ["overlay", "candidate_id", "reason"],
    )
    man = [
        {
            "step": "exit_overlay_execution_path",
            "profile": ",".join(profiles),
            "start": args.start,
            "end": args.end,
            "repo_coverage": str(args.repo_coverage),
            "status": "OK",
        }
    ]
    _write_csv(out / "overlay_run_manifest.csv", man, list(man[0].keys()))
    sch = [
        {"field": "window_label", "required": "yes"},
        {"field": "overlay", "required": "yes"},
        {"field": "total_r", "required": "yes"},
        {"field": "trades", "required": "yes"},
    ]
    _write_csv(out / "overlay_schema_validation.csv", sch, ["field", "required"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
