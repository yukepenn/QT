"""Generic Layer 2 postprocessing: sweep dedupe, diagnostics summary, cost stress."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.combiner.candidate import (
    apply_combiner_rules,
    build_enabled_mask,
    encode_candidate_metadata,
    load_candidates,
)
from src.combiner.precompute import (
    precompute_candidate_signal_matrices,
    resolve_precompute_signal_cache_settings,
)
from src.combiner.behavior import behavior_hash_from_trades, behavior_summary_from_trades, dedupe_behavior_rows
from src.combiner.metrics import execution_config_from_parts, summarize_combiner
from src.combiner.run import _build_execution_arrays, _combiner_cfg_from_yaml
from src.combiner.simulator import simulate_combiner_numba
from src.backtest.metrics import period_breakdown, summarize_trades, summarize_r_distribution, total_r_over_abs_dd

SLIPPAGE_GRID = (0.005, 0.01, 0.02, 0.03)
COMMISSION_GRID = (0.0,)


def _sort_sweep_df(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(
        by=["combiner_score", "profit_factor", "total_r"],
        ascending=[False, False, False],
        na_position="last",
    ).reset_index(drop=True)


def _full_dedupe_key(row: pd.Series) -> tuple[Any, ...]:
    """One row per distinct combiner configuration (grid + candidate list)."""
    return (
        str(row["candidate_set"]),
        int(row["top_per_strategy"]),
        int(row["max_trades_per_day"]),
        float(row["daily_max_loss_r"]),
        int(row["cooldown_after_loss_minutes"]),
        str(row["priority_policy"]),
        str(row["candidate_ids_json"]),
    )


def dedupe_sweep(
    sweep_dir: Path,
    output_root: Path,
    *,
    dedupe_top: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    results_path = sweep_dir / "results.csv"
    df = pd.read_csv(results_path)
    df_sorted = _sort_sweep_df(df)
    seen: set[tuple[Any, ...]] = set()
    rows_out: list[pd.Series] = []
    source_ranks: list[int] = []

    for i, (_, row) in enumerate(df_sorted.iterrows()):
        key = _full_dedupe_key(row)
        if key in seen:
            continue
        seen.add(key)
        rows_out.append(row)
        source_ranks.append(i + 1)
        if len(rows_out) >= dedupe_top:
            break

    out = pd.DataFrame(rows_out).reset_index(drop=True)
    out.insert(0, "unique_rank", range(1, len(out) + 1))
    out.insert(1, "source_rank", source_ranks)

    scanned = 0
    seen2: set = set()
    for i, (_, row) in enumerate(df_sorted.iterrows()):
        key = _full_dedupe_key(row)
        scanned = i + 1
        seen2.add(key)
        if len(seen2) >= dedupe_top:
            break

    stats = {
        "total_sweep_rows": len(df),
        "dedupe_top_requested": dedupe_top,
        "unique_collected": len(out),
        "rows_scanned_for_top_unique": scanned,
    }

    output_root.mkdir(parents=True, exist_ok=True)
    out_path = output_root / "top_unique_systems.csv"
    base_cols = [
        "unique_rank",
        "source_rank",
        "combo_id",
        "candidate_set",
        "top_per_strategy",
        "max_trades_per_day",
        "daily_max_loss_r",
        "cooldown_after_loss_minutes",
        "priority_policy",
        "n_candidates",
        "candidate_ids_json",
        "trades",
        "total_r",
        "profit_factor",
        "max_drawdown_r",
        "avg_bars_held",
        "combiner_score",
        "trades_by_strategy_json",
        "r_by_strategy_json",
        "rejected_by_reason_json",
    ]
    cols = [c for c in base_cols if c in out.columns]
    out[cols].to_csv(out_path, index=False)

    md_lines = [
        "# Top unique combiner systems",
        "",
        f"- Sweep rows: **{stats['total_sweep_rows']}**",
        f"- Requested top unique: **{dedupe_top}**",
        f"- Collected: **{stats['unique_collected']}** (dedupe key: candidate_set, top_per_strategy, max_trades_per_day, daily_max_loss_r, cooldown_after_loss_minutes, priority_policy, candidate_ids_json)",
        f"- Rows scanned (sorted): **{stats['rows_scanned_for_top_unique']}**",
        "",
    ]
    try:
        md_lines.append(out.head(20)[cols].to_markdown(index=False))
    except Exception:
        md_lines.append(out.head(20)[cols].to_string(index=False))
    (output_root / "top_unique_systems.md").write_text("\n".join(md_lines), encoding="utf-8")
    return out, stats


def write_diagnostics_summary(diagnostics_dir: Path, *, date_range: str) -> None:
    sig_path = diagnostics_dir / "candidate_signal_summary.csv"
    conf_path = diagnostics_dir / "candidate_conflict_summary.csv"
    if not sig_path.exists():
        raise FileNotFoundError(sig_path)

    sig = pd.read_csv(sig_path)
    total_signals = int(sig["signals"].sum())
    by_st = sig.groupby("strategy")["signals"].sum().sort_values(ascending=False)
    by_fam = sig.groupby("family")["signals"].sum().sort_values(ascending=False)
    zero = sig[sig["signals"] == 0]["candidate_id"].tolist()

    def _md2(df: pd.DataFrame) -> str:
        try:
            return df.to_markdown(index=False)
        except Exception:
            return df.to_string(index=False)

    lines = [
        "# Full-period diagnostics summary",
        "",
        f"- **Date range:** {date_range}",
        f"- **Candidates in table:** {len(sig)}",
        f"- **Total signals (sum):** {total_signals}",
        "",
        "## Signals by strategy",
        "",
        _md2(by_st.reset_index()),
        "",
        "## Signals by family",
        "",
        _md2(by_fam.reset_index()),
        "",
        "## Zero-signal candidates",
        "",
        str(zero) if zero else "*(none)*",
        "",
    ]

    if conf_path.exists():
        cf = pd.read_csv(conf_path)
        top_same_bar = cf.nlargest(20, "same_bar_overlap")[
            ["candidate_a", "candidate_b", "same_bar_overlap", "opposite_side_same_bar", "same_direction_same_bar"]
        ]
        top_same_day = cf.nlargest(20, "same_day_overlap")[
            ["candidate_a", "candidate_b", "same_day_overlap", "same_bar_overlap"]
        ]
        top_opp = cf.nlargest(15, "opposite_side_same_bar")[
            ["candidate_a", "candidate_b", "opposite_side_same_bar", "same_bar_overlap"]
        ]

        def _md(df: pd.DataFrame) -> str:
            try:
                return df.to_markdown(index=False)
            except Exception:
                return df.to_string(index=False)

        lines += [
            "## Top 20 same-bar overlap pairs",
            "",
            _md(top_same_bar),
            "",
            "## Top 20 same-day overlap pairs (session-day count)",
            "",
            _md(top_same_day),
            "",
            "## Top opposite-side same-bar pairs",
            "",
            _md(top_opp),
            "",
            "## Interpreting overlap for multi-candidate systems",
            "",
            "Non-zero **same_bar_overlap** means two candidates sometimes fire on the same bar; "
            "the combiner picks one via priority / score. Use **opposite_side_same_bar** to see "
            "whether pairs disagree on direction on those bars (more complementary) vs same-direction crowding.",
            "",
        ]

    (diagnostics_dir / "diagnostics_summary.md").write_text("\n".join(lines), encoding="utf-8")


def _selected_from_ids(universe: list[Any], ids: list[str]) -> list[Any]:
    by_id = {c.candidate_id: c for c in universe}
    return [by_id[i] for i in ids if i in by_id]


def _merged_cfg_for_row(base_cfg: dict[str, Any], row: pd.Series) -> dict[str, Any]:
    cfg = copy.deepcopy(base_cfg)
    cfg.setdefault("system", {})
    cfg["system"]["max_trades_per_day"] = int(row["max_trades_per_day"])
    cfg["system"]["daily_max_loss_r"] = float(row["daily_max_loss_r"])
    cfg["system"]["cooldown_after_loss_minutes"] = int(row["cooldown_after_loss_minutes"])
    cfg.setdefault("conflict", {})
    cfg["conflict"]["priority_policy"] = str(row["priority_policy"])
    return cfg


def _cost_robustness_label(tr01: float, pf01: float, tr02: float, pf02: float, tr03: float, pf03: float) -> str:
    ok03 = tr03 > 0 and pf03 > 1.0
    ok02 = tr02 > 0 and pf02 > 1.0
    ok01 = tr01 > 0 and pf01 > 1.0
    if ok03:
        return "robust_positive_at_0_03"
    if ok02:
        return "robust_positive_at_0_02"
    if ok01:
        return "positive_but_sensitive"
    return "cost_fragile"


def cost_stress(
    *,
    unique_df: pd.DataFrame,
    output_root: Path,
    candidate_root: Path,
    base_config_path: Path,
    asset: str,
    symbol: str,
    start: str,
    end: str,
    data_dir: str,
    top_n: int,
    use_signal_cache: bool = False,
    signal_cache_root: str | Path | None = None,
    refresh_signal_cache: bool = False,
) -> pd.DataFrame:
    with base_config_path.open(encoding="utf-8") as f:
        base_cfg = yaml.safe_load(f)

    use_sc, sc_root, refresh_sc = resolve_precompute_signal_cache_settings(
        base_cfg,
        cli_use_signal_cache=use_signal_cache,
        cli_signal_cache_root=signal_cache_root,
        cli_refresh_signal_cache=refresh_signal_cache,
    )
    print(
        f"[precompute-cache] use_signal_cache={use_sc} root={sc_root} refresh={refresh_sc}",
        flush=True,
    )

    raw = load_candidates(candidate_root)
    if not raw:
        raise SystemExit("ERROR: no candidate YAMLs under candidate_root; restore Layer 1 library first.")

    strategy_rules = base_cfg.get("strategy_rules") or {}
    raw_eligible: list[Any] = []
    for sp in raw:
        rules = strategy_rules.get(sp.strategy) or {}
        if rules.get("enabled", True) is False:
            continue
        raw_eligible.append(sp)
    universe = [apply_combiner_rules(sp, strategy_rules) for sp in raw_eligible]

    stress_dir = output_root / "cost_stress"
    stress_dir.mkdir(parents=True, exist_ok=True)

    print(f"[postprocess] cost stress: precomputing {len(universe)} candidates...", flush=True)
    csm = precompute_candidate_signal_matrices(
        candidates=universe,
        asset=asset,
        symbol=symbol,
        start=start,
        end=end,
        data_dir=data_dir,
        profile_csv_path=stress_dir / "candidate_precompute_profile.csv",
        use_signal_cache=use_sc,
        signal_cache_root=sc_root,
        refresh_signal_cache=refresh_sc,
    )
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
    _, _, pri, score, rank, ast, aen, _, _, _ = encode_candidate_metadata(universe)

    rows_out: list[dict[str, Any]] = []

    head = unique_df.head(top_n)
    for _, urow in head.iterrows():
        ur = int(urow["unique_rank"])
        ids = json.loads(str(urow["candidate_ids_json"]))
        selected = _selected_from_ids(universe, ids)
        if len(selected) != len(ids):
            print(f"[postprocess] WARN unique_rank {ur}: some candidate_ids missing in universe", flush=True)
        enabled = build_enabled_mask(universe, selected)
        merged_base = _merged_cfg_for_row(base_cfg, urow)

        metrics_by_slip: dict[float, dict[str, Any]] = {}
        for slip in SLIPPAGE_GRID:
            for comm in COMMISSION_GRID:
                mc = copy.deepcopy(merged_base)
                mc.setdefault("execution", {})
                mc["execution"]["slippage_per_share"] = float(slip)
                mc["execution"]["commission_per_trade"] = float(comm)
                comb_cfg = _combiner_cfg_from_yaml(mc)
                max_hold, recomp, qty, min_risk = _build_execution_arrays(universe, mc, comb_cfg)
                sim_out = simulate_combiner_numba(
                    backtest_arrays=bt_arr,
                    candidate_arrays=mats,
                    candidates=universe,
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
                exec_cfg = execution_config_from_parts(float(slip), float(comm), qty)
                metrics = summarize_combiner(
                    sim_out["trades_df"],
                    pd.DataFrame(),
                    pd.DataFrame(),
                    rejection_counts=sim_out.get("rejection_counts"),
                    execution_config=exec_cfg,
                )
                metrics_by_slip[float(slip)] = metrics

        def _m(sl: float, k: str) -> Any:
            return metrics_by_slip[sl].get(k)

        tr01 = float(_m(0.01, "total_r") or 0.0)
        pf01 = float(_m(0.01, "profit_factor") or 0.0)
        tr02 = float(_m(0.02, "total_r") or 0.0)
        pf02 = float(_m(0.02, "profit_factor") or 0.0)
        tr03 = float(_m(0.03, "total_r") or 0.0)
        pf03 = float(_m(0.03, "profit_factor") or 0.0)
        label = _cost_robustness_label(tr01, pf01, tr02, pf02, tr03, pf03)

        for slip in SLIPPAGE_GRID:
            for comm in COMMISSION_GRID:
                m = metrics_by_slip[float(slip)]
                csf = float(m.get("combiner_score", 0.0) or 0.0)
                rows_out.append(
                    {
                        "unique_rank": ur,
                        "source_combo_id": int(urow.get("combo_id", -1)),
                        "candidate_set": urow["candidate_set"],
                        "top_per_strategy": int(urow["top_per_strategy"]),
                        "max_trades_per_day": int(urow["max_trades_per_day"]),
                        "daily_max_loss_r": float(urow["daily_max_loss_r"]),
                        "cooldown_after_loss_minutes": int(urow["cooldown_after_loss_minutes"]),
                        "priority_policy": str(urow["priority_policy"]),
                        "slippage_per_share": slip,
                        "commission_per_trade": comm,
                        "n_candidates": int(enabled.sum()),
                        "candidate_ids_json": str(urow["candidate_ids_json"]),
                        "trades": int(m.get("trades", 0)),
                        "total_net_pnl": m.get("total_net_pnl", 0),
                        "total_r": m.get("total_r", 0),
                        "profit_factor": m.get("profit_factor", 0),
                        "max_drawdown_r": m.get("max_drawdown_r", 0),
                        "avg_bars_held": m.get("avg_bars_held", 0),
                        "avg_cost_r": m.get("avg_cost_r"),
                        "median_cost_r": m.get("median_cost_r"),
                        "combiner_score": csf,
                        "robust_positive_at_0_02": bool(tr02 > 0 and pf02 > 1.0),
                        "robust_positive_at_0_03": bool(tr03 > 0 and pf03 > 1.0),
                        "cost_robustness_label": label,
                    }
                )

    out = pd.DataFrame(rows_out)
    out.to_csv(stress_dir / "cost_stress_results.csv", index=False)

    summ_lines: list[str] = ["# Cost stress (top unique systems)", ""]
    for ur in sorted(head["unique_rank"].unique()):
        sub = out[out["unique_rank"] == ur]
        if sub.empty:
            continue
        piv = sub.pivot_table(
            index="slippage_per_share",
            values=["total_r", "profit_factor", "max_drawdown_r", "combiner_score"],
            aggfunc="first",
        )
        lbl = sub["cost_robustness_label"].iloc[0]
        summ_lines.append(f"## unique_rank {ur}")
        summ_lines.append("")
        try:
            summ_lines.append(piv.to_markdown())
        except Exception:
            summ_lines.append(str(piv))
        summ_lines.append("")
        summ_lines.append(f"- **cost_robustness_label:** `{lbl}`")
        summ_lines.append("")

    (stress_dir / "cost_stress_summary.md").write_text("\n".join(summ_lines), encoding="utf-8")
    return out


def collect_fixed_run_summary(fixed_runs_root: Path, output_root: Path) -> tuple[pd.DataFrame, str]:
    rows: list[dict[str, Any]] = []
    for d in sorted(fixed_runs_root.iterdir()):
        if not d.is_dir() or not d.name.startswith("run_"):
            continue
        mj = d / "metrics.json"
        cr = d / "config_resolved.yaml"
        cu = d / "candidates_used.csv"
        if not mj.exists() or not cr.exists():
            continue
        metrics = json.loads(mj.read_text(encoding="utf-8"))
        cfg = yaml.safe_load(cr.read_text(encoding="utf-8"))
        run = cfg.get("run") or {}
        tag = str(run.get("tag", ""))
        cdf = pd.read_csv(cu) if cu.exists() else pd.DataFrame()
        cids = cdf["candidate_id"].tolist() if "candidate_id" in cdf.columns else []

        rows.append(
            {
                "tag": tag,
                "folder": str(d.resolve()),
                "candidate_set": run.get("candidate_set"),
                "top_per_strategy": run.get("top_per_strategy"),
                "candidates_used_json": json.dumps(cids, sort_keys=True),
                "n_candidates": len(cids),
                "trades": metrics.get("trades", 0),
                "total_net_pnl": metrics.get("total_net_pnl", 0),
                "total_r": metrics.get("total_r", 0),
                "profit_factor": metrics.get("profit_factor", 0),
                "max_drawdown_r": metrics.get("max_drawdown_r", 0),
                "avg_bars_held": metrics.get("avg_bars_held", 0),
                "max_hold_count": metrics.get("max_hold_count", 0),
                "eod_count": metrics.get("eod_count", 0),
                "end_of_session_count": metrics.get("end_of_session_count", 0),
                "end_of_data_count": metrics.get("end_of_data_count", 0),
                "candidate_signals": metrics.get("candidate_signals", 0),
                "selected_signals": metrics.get("selected_signals", 0),
                "rejected_signals": metrics.get("rejected_signals", 0),
                "selection_rate": metrics.get("selection_rate", 0),
                "rejected_by_reason_json": metrics.get("rejected_by_reason_json", "{}"),
                "trades_by_strategy_json": metrics.get("trades_by_strategy_json", "{}"),
                "r_by_strategy_json": metrics.get("r_by_strategy_json", "{}"),
                "pnl_by_strategy_json": metrics.get("pnl_by_strategy_json", "{}"),
                "trades_by_family_json": metrics.get("trades_by_family_json", "{}"),
                "r_by_family_json": metrics.get("r_by_family_json", "{}"),
                "pnl_by_family_json": metrics.get("pnl_by_family_json", "{}"),
            }
        )

    out = pd.DataFrame(rows)
    output_root.mkdir(parents=True, exist_ok=True)
    csv_path = output_root / "fixed_run_summary.csv"
    out.to_csv(csv_path, index=False)

    md_lines = ["# Fixed run summary", "", f"- Runs found: **{len(out)}** under `{fixed_runs_root}`", ""]
    if len(out):
        try:
            md_lines.append(
                out[
                    [
                        "tag",
                        "trades",
                        "total_r",
                        "profit_factor",
                        "max_drawdown_r",
                        "candidate_set",
                        "n_candidates",
                    ]
                ].to_markdown(index=False)
            )
        except Exception:
            md_lines.append(
                out[
                    [
                        "tag",
                        "trades",
                        "total_r",
                        "profit_factor",
                        "max_drawdown_r",
                        "candidate_set",
                        "n_candidates",
                    ]
                ].to_string(index=False)
            )
    (output_root / "fixed_run_summary.md").write_text("\n".join(md_lines), encoding="utf-8")
    return out, str(csv_path)


def _parse_combo_id_from_summary(summary_text: str) -> int | None:
    m = re.search(r"combo_id=(\d+)", summary_text)
    return int(m.group(1)) if m else None


def map_unique_to_top_runs(
    unique_df: pd.DataFrame,
    sweep_dir: Path,
    output_root: Path,
    *,
    max_rank: int = 50,
) -> None:
    top_runs = sweep_dir / "top_runs"
    if not top_runs.is_dir():
        pd.DataFrame(
            columns=[
                "unique_rank",
                "source_rank",
                "source_top_run_folder",
                "detailed_folder",
                "rerun_needed",
                "status",
            ]
        ).to_csv(output_root / "top_unique_run_map.csv", index=False)
        return

    rank_to_combo: dict[int, int] = {}
    for rdir in sorted(top_runs.iterdir()):
        if not rdir.is_dir() or not rdir.name.startswith("rank_"):
            continue
        try:
            rk = int(rdir.name.split("_")[1])
        except (IndexError, ValueError):
            continue
        if rk > max_rank:
            continue
        st = rdir / "summary.txt"
        if st.exists():
            cid = _parse_combo_id_from_summary(st.read_text(encoding="utf-8"))
            if cid is not None:
                rank_to_combo[rk] = cid

    maps: list[dict[str, Any]] = []
    for _, urow in unique_df.iterrows():
        ur = int(urow["unique_rank"])
        combo_id = int(urow["combo_id"])
        hit_rank: int | None = None
        for rk, cid in rank_to_combo.items():
            if cid == combo_id:
                hit_rank = rk
                break
        if hit_rank is not None:
            folder = top_runs / f"rank_{hit_rank:03d}"
            maps.append(
                {
                    "unique_rank": ur,
                    "source_rank": int(urow["source_rank"]),
                    "source_top_run_folder": str(folder.resolve()),
                    "detailed_folder": str(folder.resolve()),
                    "rerun_needed": False,
                    "status": "matched_existing_top_run",
                }
            )
        else:
            maps.append(
                {
                    "unique_rank": ur,
                    "source_rank": int(urow["source_rank"]),
                    "source_top_run_folder": "",
                    "detailed_folder": "",
                    "rerun_needed": True,
                    "status": "not_found",
                }
            )

    pd.DataFrame(maps).to_csv(output_root / "top_unique_run_map.csv", index=False)


def _trades_dt_series(df: pd.DataFrame) -> pd.Series:
    if "session_date" in df.columns:
        return pd.to_datetime(df["session_date"], errors="coerce")
    if "entry_ts_utc" in df.columns:
        return pd.to_datetime(df["entry_ts_utc"], utc=True, errors="coerce")
    if "exit_ts_utc" in df.columns:
        return pd.to_datetime(df["exit_ts_utc"], utc=True, errors="coerce")
    return pd.Series(pd.NaT, index=df.index)


def _period_breakdown_by_field(trades_df: pd.DataFrame, freq: str, field: str) -> pd.DataFrame:
    base_cols = [
        "period",
        "trades",
        "total_r",
        "total_net_pnl",
        "profit_factor",
        "profit_factor_r",
        "max_drawdown_r",
        "win_rate",
        "avg_r",
        "median_r",
    ]
    out_cols = ["period", field] + base_cols[1:]
    if trades_df is None or len(trades_df) == 0 or field not in trades_df.columns:
        return pd.DataFrame(columns=out_cols)
    df = trades_df.copy()
    df["_dt"] = _trades_dt_series(df)
    df["_period"] = df["_dt"].dt.to_period(freq)
    rows: list[dict[str, Any]] = []
    for (per, fv), sub in df.groupby(["_period", field], dropna=False):
        if per is pd.NaT or str(per) == "NaT":
            continue
        m = summarize_trades(sub)
        rd = summarize_r_distribution(sub)
        rows.append(
            {
                "period": str(per),
                field: fv,
                "trades": m["trades"],
                "total_r": m["total_r"],
                "total_net_pnl": m["total_net_pnl"],
                "profit_factor": m["profit_factor"],
                "profit_factor_r": rd["profit_factor_r"],
                "max_drawdown_r": m["max_drawdown_r"],
                "win_rate": m["win_rate"],
                "avg_r": m["avg_r"],
                "median_r": rd["median_r"],
            }
        )
    return pd.DataFrame(rows, columns=out_cols)


def write_period_breakdowns_for_run(run_dir: Path) -> None:
    p = run_dir / "trades.csv"
    if not p.exists():
        return
    df = pd.read_csv(p)
    period_breakdown(df, "M").to_csv(run_dir / "monthly_r.csv", index=False)
    period_breakdown(df, "Q").to_csv(run_dir / "quarterly_r.csv", index=False)
    if "strategy" in df.columns:
        _period_breakdown_by_field(df, "M", "strategy").to_csv(run_dir / "strategy_by_month.csv", index=False)
    if "candidate_id" in df.columns:
        _period_breakdown_by_field(df, "M", "candidate_id").to_csv(run_dir / "candidate_by_month.csv", index=False)


def write_period_breakdowns_for_sweep_top_runs(sweep_dir: Path) -> None:
    top = sweep_dir / "top_runs"
    if not top.is_dir():
        return
    for rdir in sorted(top.iterdir()):
        if rdir.is_dir() and rdir.name.startswith("rank_"):
            write_period_breakdowns_for_run(rdir)


def write_period_breakdowns_for_fixed_runs(fixed_root: Path) -> None:
    if not fixed_root.is_dir():
        return
    for d in sorted(fixed_root.iterdir()):
        if d.is_dir() and d.name.startswith("run_"):
            write_period_breakdowns_for_run(d)


def _execution_from_resolved_yaml(cfg_path: Path) -> dict[str, Any]:
    if not cfg_path.exists():
        return {}
    y = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    ex = y.get("execution")
    if ex is None and isinstance(y.get("combiner_yaml"), dict):
        ex = (y["combiner_yaml"] or {}).get("execution")
    ex = ex or {}
    return {
        "slippage_per_share": ex.get("slippage_per_share"),
        "commission_per_trade": ex.get("commission_per_trade"),
        "quantity": float(ex.get("quantity", 1.0) or 1.0),
    }


def _row_from_trades_and_config(
    urow: pd.Series,
    trades_path: Path,
    *,
    config_yaml: Path | None,
    source_rank: int,
    config_rank: int,
) -> dict[str, Any] | None:
    if not trades_path.exists():
        return None
    tdf = pd.read_csv(trades_path)
    ec = _execution_from_resolved_yaml(config_yaml) if config_yaml else {}
    slip = ec.get("slippage_per_share")
    comm = ec.get("commission_per_trade")
    qty = ec.get("quantity")
    sm = summarize_trades(
        tdf,
        slippage_per_share=float(slip) if slip is not None else None,
        commission_per_trade=float(comm) if comm is not None else None,
        quantity=float(qty) if qty is not None else None,
    )
    bsum = behavior_summary_from_trades(tdf)
    base = {k: urow.get(k) for k in urow.index}
    out: dict[str, Any] = dict(base)
    out.update(sm)
    out["behavior_hash"] = bsum["behavior_hash"]
    out["behavior_hash_quality"] = bsum["behavior_hash_quality"]
    out["source_rank"] = int(source_rank)
    out["config_rank"] = int(config_rank)
    return out


def write_behavior_unique_systems(
    *,
    unique_df: pd.DataFrame,
    sweep_dir: Path,
    output_root: Path,
    behavior_dedupe_top: int,
    behavior_source: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    map_path = output_root / "top_unique_run_map.csv"
    run_map = pd.read_csv(map_path) if map_path.exists() else pd.DataFrame()

    head = unique_df.head(behavior_dedupe_top)
    rows: list[dict[str, Any]] = []
    weak_quality = 0
    missing_trades = 0
    if behavior_source != "top_runs":
        behavior_source = "top_runs"
    for config_rank, (_, urow) in enumerate(head.iterrows(), start=1):
        ur = int(urow["unique_rank"])
        folder_str = ""
        if len(run_map) and "unique_rank" in run_map.columns:
            sub = run_map[run_map["unique_rank"] == ur]
            if len(sub):
                folder_str = str(sub.iloc[0].get("detailed_folder", "") or "")
        run_dir = Path(folder_str) if folder_str else None
        trades_path = (run_dir / "trades.csv") if run_dir else None
        cfg_yaml = (run_dir / "config_resolved.yaml") if run_dir else None
        if trades_path is None or not trades_path.exists():
            missing_trades += 1
            continue
        rec = _row_from_trades_and_config(
            urow,
            trades_path,
            config_yaml=cfg_yaml,
            source_rank=int(urow.get("source_rank", config_rank)),
            config_rank=config_rank,
        )
        if rec is None:
            missing_trades += 1
            continue
        if rec.get("behavior_hash_quality") == "weak":
            weak_quality += 1
        rows.append(rec)

    if not rows:
        empty = pd.DataFrame()
        stats = {
            "config_rows_considered": len(head),
            "rows_with_trades": 0,
            "behavior_unique_count": 0,
            "weak_behavior_hash_rows": 0,
            "missing_trades_rows": missing_trades,
        }
        return empty, stats

    df = pd.DataFrame(rows)
    sort_cols: list[str] = []
    for c in ("combiner_score", "total_r", "profit_factor_r"):
        if c in df.columns:
            sort_cols.append(c)
    if sort_cols:
        df = df.sort_values(by=sort_cols, ascending=[False] * len(sort_cols), na_position="last")
    df = dedupe_behavior_rows(df)
    df.insert(0, "behavior_rank", range(1, len(df) + 1))

    stats = {
        "config_rows_considered": len(head),
        "rows_with_trades": len(rows),
        "behavior_unique_count": len(df),
        "weak_behavior_hash_rows": weak_quality,
        "missing_trades_rows": missing_trades,
    }

    want_cols = [
        "behavior_rank",
        "source_rank",
        "config_rank",
        "behavior_hash",
        "behavior_hash_quality",
        "candidate_set",
        "top_per_strategy",
        "max_trades_per_day",
        "daily_max_loss_r",
        "cooldown_after_loss_minutes",
        "priority_policy",
        "candidate_ids_json",
        "candidates_short",
        "trades",
        "total_r",
        "total_net_pnl",
        "profit_factor",
        "profit_factor_r",
        "max_drawdown_r",
        "avg_bars_held",
        "avg_cost_r",
        "median_cost_r",
        "p90_cost_r",
        "pct_trades_cost_r_gt_0_50",
        "active_days",
        "positive_day_rate",
        "avg_daily_r",
        "worst_day_r",
        "trades_by_strategy_json",
        "r_by_strategy_json",
        "trades_by_candidate_json",
        "r_by_candidate_json",
        "trades_by_daily_trade_number_json",
        "r_by_daily_trade_number_json",
        "profit_factor_r_by_daily_trade_number_json",
    ]
    cols = [c for c in want_cols if c in df.columns]
    df[cols].to_csv(output_root / "behavior_unique_systems.csv", index=False)

    maps: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        maps.append(
            {
                "behavior_rank": int(r["behavior_rank"]),
                "behavior_hash": r.get("behavior_hash"),
                "unique_rank": r.get("unique_rank"),
                "source_rank": r.get("source_rank"),
                "config_rank": r.get("config_rank"),
                "combiner_score": r.get("combiner_score"),
                "total_r": r.get("total_r"),
            }
        )
    pd.DataFrame(maps).to_csv(output_root / "behavior_unique_run_map.csv", index=False)

    top10 = df.head(10)
    md = [
        "# Behavior-unique combiner systems",
        "",
        "Deduplication uses **actual trade sequences** (`behavior_hash_from_trades`), not YAML alone.",
        "",
        f"- Config rows inspected: **{stats['config_rows_considered']}**",
        f"- Rows with `trades.csv` loaded: **{stats['rows_with_trades']}**",
        f"- Behavior-unique systems: **{stats['behavior_unique_count']}**",
        f"- Rows with weak hash quality (missing id/entry/exit columns): **{stats['weak_behavior_hash_rows']}**",
        f"- Missing detailed trades (no matched `top_runs` folder): **{stats['missing_trades_rows']}**",
        "",
        "## Top 10 behavior-unique",
        "",
    ]
    try:
        md.append(top10[cols].to_markdown(index=False))
    except Exception:
        md.append(top10[cols].to_string(index=False))
    md.append("")
    (output_root / "behavior_unique_systems.md").write_text("\n".join(md), encoding="utf-8")
    return df, stats


def _add_total_r_over_dd(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "total_r" not in out.columns or "max_drawdown_r" not in out.columns:
        out["total_r_over_abs_dd"] = float("nan")
        return out
    out["total_r_over_abs_dd"] = [
        total_r_over_abs_dd(float(r.get("total_r", 0) or 0), float(r.get("max_drawdown_r", 0) or 0))
        for _, r in out.iterrows()
    ]
    return out


def write_rank_high_trade_systems(
    systems_df: pd.DataFrame,
    output_root: Path,
    *,
    min_trades_rank: int,
    rank_high_trade_top: int,
) -> pd.DataFrame:
    """Filter config-unique systems by trade count and rank for high-activity research views."""
    output_root.mkdir(parents=True, exist_ok=True)
    if "trades" not in systems_df.columns or len(systems_df) == 0:
        systems_df.iloc[0:0].to_csv(output_root / "rank_high_trade_systems.csv", index=False)
        (output_root / "rank_high_trade_systems.md").write_text(
            "# High-trade systems rank\n\n*No rows or missing `trades` column.*\n", encoding="utf-8"
        )
        return pd.DataFrame()

    sub = systems_df[systems_df["trades"].fillna(0).astype(float) >= float(min_trades_rank)].copy()
    if len(sub) == 0:
        sub.to_csv(output_root / "rank_high_trade_systems.csv", index=False)
        (output_root / "rank_high_trade_systems.md").write_text(
            f"# High-trade systems rank\n\n*No systems with trades >= {min_trades_rank}.*\n",
            encoding="utf-8",
        )
        return sub

    sort_cols: list[str] = ["total_r"]
    ascending: list[bool] = [False]
    if "profit_factor_r" in sub.columns and sub["profit_factor_r"].notna().any():
        sort_cols.append("profit_factor_r")
        ascending.append(False)
    elif "profit_factor" in sub.columns:
        sort_cols.append("profit_factor")
        ascending.append(False)
    if "max_drawdown_r" in sub.columns:
        sort_cols.append("max_drawdown_r")
        ascending.append(False)

    n_after_min_trades = len(sub)
    sub = sub.sort_values(by=sort_cols, ascending=ascending, na_position="last").reset_index(drop=True)
    sub = sub.head(int(rank_high_trade_top)).copy()
    sub.insert(0, "high_trade_rank", range(1, len(sub) + 1))

    out_root = output_root
    out_root.mkdir(parents=True, exist_ok=True)
    sub.to_csv(out_root / "rank_high_trade_systems.csv", index=False)
    md = [
        "# High-trade systems rank",
        "",
        f"- Source rows: **{len(systems_df)}**",
        f"- After trades >= **{min_trades_rank}**: **{n_after_min_trades}** (showing top **{len(sub)}**, cap **{rank_high_trade_top}**)",
        f"- Sort: `{', '.join(sort_cols)}` (descending)",
        "",
    ]
    disp_cols = [c for c in ["high_trade_rank", "combo_id", "candidate_set", "top_per_strategy", "max_trades_per_day", "trades", "total_r", "profit_factor", "profit_factor_r", "max_drawdown_r", "combiner_score"] if c in sub.columns]
    try:
        md.append(sub[disp_cols].to_markdown(index=False))
    except Exception:
        md.append(sub[disp_cols].to_string(index=False))
    md.append("")
    (out_root / "rank_high_trade_systems.md").write_text("\n".join(md), encoding="utf-8")
    return sub


def write_rank_leaderboards(sweep_results: pd.DataFrame, output_root: Path, *, min_trades_cost_rank: int) -> None:
    df = _add_total_r_over_dd(sweep_results)
    root = output_root
    root.mkdir(parents=True, exist_ok=True)

    def _rank_csv(sub: pd.DataFrame, col: str, path: Path, ascending: bool = False) -> None:
        if col not in sub.columns:
            return
        s = sub.sort_values(by=col, ascending=ascending, na_position="last").reset_index(drop=True)
        s.insert(0, "rank", range(1, len(s) + 1))
        s.to_csv(path, index=False)

    _rank_csv(df, "combiner_score", root / "rank_by_combiner_score.csv")
    _rank_csv(df, "total_r", root / "rank_by_total_r.csv")
    _rank_csv(df, "profit_factor", root / "rank_by_profit_factor.csv")
    if "profit_factor_r" in df.columns:
        _rank_csv(df, "profit_factor_r", root / "rank_by_profit_factor_r.csv")
    _rank_csv(df, "total_r_over_abs_dd", root / "rank_by_total_r_over_abs_dd.csv")

    sub_cost = (
        df[df["trades"].fillna(0).astype(float) >= float(min_trades_cost_rank)]
        if "trades" in df.columns
        else df
    )
    _rank_csv(sub_cost, "avg_cost_r", root / "rank_by_avg_cost_r.csv", ascending=True)
    _rank_csv(sub_cost, "median_cost_r", root / "rank_by_median_cost_r.csv", ascending=True)

    stress_path = root / "cost_stress" / "cost_stress_results.csv"
    if stress_path.exists():
        cs = pd.read_csv(stress_path)
        slip = cs[np.isclose(cs["slippage_per_share"].astype(float), 0.02)]
        if len(slip):
            _rank_csv(slip, "total_r", root / "rank_by_cost_0_02_total_r.csv")


def write_cost_robust_systems(
    output_root: Path,
    *,
    min_trades: int,
    slip: float,
    min_total_r: float,
    min_pf: float,
    max_dd_r: float,
    max_median_cost_r: float,
) -> None:
    stress_path = output_root / "cost_stress" / "cost_stress_results.csv"
    lines = ["# Cost-robust systems (research filters)", "",]
    if not stress_path.exists():
        lines += [
            "*Cost stress results not found — skipped `cost_robust_systems` filter.*",
            "",
        ]
        (output_root / "cost_robust_systems.md").write_text("\n".join(lines), encoding="utf-8")
        pd.DataFrame().to_csv(output_root / "cost_robust_systems.csv", index=False)
        return

    cs = pd.read_csv(stress_path)
    sub = cs[np.isclose(cs["slippage_per_share"].astype(float), float(slip))]
    if "median_cost_r" not in sub.columns:
        sub = sub.copy()
        sub["median_cost_r"] = float("nan")
    mask = (
        (sub["trades"].astype(int) >= int(min_trades))
        & (sub["total_r"].astype(float) > float(min_total_r))
        & (sub["profit_factor"].astype(float) > float(min_pf))
        & (sub["max_drawdown_r"].astype(float) > float(max_dd_r))
    )
    med = sub["median_cost_r"].astype(float)
    mask_m = med.isna() | (med <= float(max_median_cost_r))
    out = sub[mask & mask_m].sort_values(by="total_r", ascending=False)
    out.to_csv(output_root / "cost_robust_systems.csv", index=False)
    lines += [
        "Thresholds (not trading advice):",
        f"- min_trades >= {min_trades}",
        f"- slippage_per_share = {slip}",
        f"- total_r > {min_total_r}",
        f"- profit_factor > {min_pf}",
        f"- max_drawdown_r > {max_dd_r}",
        f"- median_cost_r <= {max_median_cost_r} (or missing)",
        "",
        f"- Matching rows: **{len(out)}**",
        "",
    ]
    if len(out):
        try:
            lines.append(out.head(30).to_markdown(index=False))
        except Exception:
            lines.append(out.head(30).to_string(index=False))
    (output_root / "cost_robust_systems.md").write_text("\n".join(lines), encoding="utf-8")


def write_fixed_vs_sweep_comparison(
    *,
    fixed_summary_csv: Path,
    sweep_results: pd.DataFrame,
    unique_df: pd.DataFrame | None,
    behavior_df: pd.DataFrame | None,
    cost_robust_csv: Path,
    output_root: Path,
) -> None:
    rows: list[dict[str, Any]] = []
    fx = pd.read_csv(fixed_summary_csv)
    cols_pick = [
        "source",
        "label",
        "candidate_set",
        "top_per_strategy",
        "trades",
        "total_r",
        "profit_factor",
        "profit_factor_r",
        "max_drawdown_r",
        "total_r_over_abs_dd",
        "avg_cost_r",
        "median_cost_r",
        "candidate_ids_json",
        "trades_by_strategy_json",
        "r_by_strategy_json",
    ]

    def _add_row(source: str, label: str, r: pd.Series | dict[str, Any]) -> None:
        d = dict(r) if isinstance(r, dict) else r.to_dict()
        if "candidate_ids_json" not in d and d.get("candidates_used_json") is not None:
            d["candidate_ids_json"] = d.get("candidates_used_json")
        tr = float(d.get("total_r", 0) or 0)
        dd = float(d.get("max_drawdown_r", 0) or 0)
        d["total_r_over_abs_dd"] = total_r_over_abs_dd(tr, dd)
        d["source"] = source
        d["label"] = label
        rows.append({k: d.get(k) for k in cols_pick})

    if len(fx):
        fx2 = _add_total_r_over_dd(fx)
        for col, lbl in [
            ("total_r", "top_fixed_by_total_r"),
            ("profit_factor", "top_fixed_by_profit_factor"),
            ("total_r_over_abs_dd", "top_fixed_by_total_r_over_abs_dd"),
        ]:
            if col not in fx2.columns:
                continue
            best = fx2.sort_values(by=col, ascending=False, na_position="last").iloc[0]
            _add_row("fixed", lbl, best)

    if len(sweep_results):
        uq = dedupe_sweep_from_results(_add_total_r_over_dd(sweep_results))
        if len(uq):
            best = uq.sort_values(by="combiner_score", ascending=False, na_position="last").iloc[0]
            _add_row("sweep", "top_config_unique_by_combiner_score", best)

    if unique_df is not None and len(unique_df):
        best = unique_df.sort_values(by="combiner_score", ascending=False, na_position="last").iloc[0]
        _add_row("sweep", "top_from_top_unique_systems", best)

    if behavior_df is not None and len(behavior_df):
        best = behavior_df.sort_values(by="combiner_score", ascending=False, na_position="last").iloc[0]
        _add_row("sweep", "top_behavior_unique", best)

    if cost_robust_csv.exists():
        cr = pd.read_csv(cost_robust_csv)
        if len(cr):
            best = cr.sort_values(by="total_r", ascending=False, na_position="last").iloc[0]
            _add_row("sweep", "top_cost_robust", best)

    out = pd.DataFrame(rows)
    out.to_csv(output_root / "fixed_vs_sweep_comparison.csv", index=False)
    md = [
        "# Fixed runs vs sweep (illustrative)",
        "",
        "Broad fixed runs may show higher **total_r** with lower **profit factor** or worse **drawdown**; sweep winners may have higher **combiner_score** but fewer trades. "
        "These tables are for diagnostics only.",
        "",
    ]
    try:
        md.append(out.to_markdown(index=False))
    except Exception:
        md.append(out.to_string(index=False))
    (output_root / "fixed_vs_sweep_comparison.md").write_text("\n".join(md), encoding="utf-8")


def dedupe_sweep_from_results(df: pd.DataFrame) -> pd.DataFrame:
    """Config-level dedupe on full sweep results (same key as top_unique)."""
    if len(df) == 0:
        return df
    d = _sort_sweep_df(df)
    seen: set[tuple[Any, ...]] = set()
    out_rows: list[pd.Series] = []
    for _, row in d.iterrows():
        key = _full_dedupe_key(row)
        if key in seen:
            continue
        seen.add(key)
        out_rows.append(row)
    return pd.DataFrame(out_rows).reset_index(drop=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Layer 2 combiner postprocess (dedupe, cost stress, diagnostics summary).")
    p.add_argument("--sweep-dir", type=Path, default=None)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--dedupe-top", type=int, default=0)
    p.add_argument("--cost-stress-top", type=int, default=0)
    p.add_argument("--candidate-root", type=Path, default=None)
    p.add_argument("--config", type=Path, default=None, help="Base layer2 YAML (e.g. layer2_qqq_v1.yaml) for cost stress.")
    p.add_argument("--asset", default="equity")
    p.add_argument("--symbol", default="QQQ")
    p.add_argument("--start", default="2025-01-01")
    p.add_argument("--end", default="2026-04-30")
    p.add_argument("--data-dir", default="data/raw/ibkr")
    p.add_argument("--use-signal-cache", action="store_true")
    p.add_argument("--signal-cache-root", default=None)
    p.add_argument("--refresh-signal-cache", action="store_true")
    p.add_argument("--diagnostics-dir", type=Path, default=None)
    p.add_argument("--diagnostics-date-range", default="2025-01-01 — 2026-04-30")
    p.add_argument("--collect-fixed-runs", type=Path, default=None, help="Scan run_* folders and write fixed_run_summary.")
    p.add_argument("--fixed-runs-dir", type=Path, default=None, help="Root with run_* folders for period CSV exports.")
    p.add_argument("--write-period-breakdowns", action="store_true", help="Write monthly/quarterly CSVs for top_runs / fixed runs.")
    p.add_argument("--behavior-dedupe-top", type=int, default=0, help="Top N config-unique rows to hash; 0 = same as --dedupe-top.")
    p.add_argument("--write-behavior-unique", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--behavior-source", default="top_runs", help="Only top_runs is implemented (detailed trades under sweep top_runs).")
    p.add_argument("--behavior-top-rerun", type=int, default=100, help="Reserved for future detailed reruns.")
    p.add_argument("--min-trades-cost-rank", type=int, default=300, help="Min trades for cost-r leaderboards.")
    p.add_argument("--cost-robust-min-trades", type=int, default=300)
    p.add_argument("--cost-robust-slip", type=float, default=0.02)
    p.add_argument("--cost-robust-min-total-r", type=float, default=0.0)
    p.add_argument("--cost-robust-min-pf", type=float, default=1.0)
    p.add_argument("--cost-robust-max-dd-r", type=float, default=-100.0)
    p.add_argument("--cost-robust-max-median-cost-r", type=float, default=0.50)
    p.add_argument("--compare-fixed-runs", type=Path, default=None, help="Path to fixed_run_summary.csv for sweep comparison.")
    p.add_argument(
        "--min-trades-rank",
        type=int,
        default=0,
        help="With --rank-high-trade-top > 0, write rank_high_trade_systems.* from top_unique (trades >= this).",
    )
    p.add_argument(
        "--rank-high-trade-top",
        type=int,
        default=0,
        help="Max rows for rank_high_trade_systems.* (0 = skip).",
    )
    args = p.parse_args(argv)

    cwd = Path.cwd()
    out_root = args.output_root
    if not out_root.is_absolute():
        out_root = cwd / out_root

    def _abs(path: Path | None) -> Path | None:
        if path is None:
            return None
        return path if path.is_absolute() else cwd / path

    sweep_dir = _abs(args.sweep_dir)
    _ = args.behavior_top_rerun

    if args.collect_fixed_runs:
        fr = _abs(args.collect_fixed_runs)
        assert fr is not None
        collect_fixed_run_summary(fr, out_root)
        print(f"[postprocess] collected fixed runs from {fr}", flush=True)

    if args.diagnostics_dir:
        ddir = _abs(args.diagnostics_dir)
        assert ddir is not None
        write_diagnostics_summary(ddir, date_range=args.diagnostics_date_range)
        print(f"[postprocess] wrote {ddir / 'diagnostics_summary.md'}", flush=True)

    if args.write_period_breakdowns and args.fixed_runs_dir:
        frd = _abs(args.fixed_runs_dir)
        assert frd is not None
        write_period_breakdowns_for_fixed_runs(frd)
        print(f"[postprocess] period breakdowns under fixed runs {frd}", flush=True)

    unique_df: pd.DataFrame | None = None
    if args.dedupe_top and sweep_dir is not None:
        unique_df, stats = dedupe_sweep(sweep_dir, out_root, dedupe_top=args.dedupe_top)
        print(f"[postprocess] dedupe: {stats}", flush=True)
        map_unique_to_top_runs(unique_df, sweep_dir, out_root, max_rank=50)

    if args.write_period_breakdowns and sweep_dir is not None:
        write_period_breakdowns_for_sweep_top_runs(sweep_dir)
        print(f"[postprocess] period breakdowns under {sweep_dir / 'top_runs'}", flush=True)

    if args.cost_stress_top and unique_df is None and (out_root / "top_unique_systems.csv").exists():
        unique_df = pd.read_csv(out_root / "top_unique_systems.csv")

    if args.cost_stress_top and unique_df is not None and args.candidate_root and args.config:
        cr = _abs(args.candidate_root)
        cf = _abs(args.config)
        assert cr is not None and cf is not None
        cost_stress(
            unique_df=unique_df,
            output_root=out_root,
            candidate_root=cr,
            base_config_path=cf,
            asset=args.asset,
            symbol=args.symbol,
            start=args.start,
            end=args.end,
            data_dir=args.data_dir,
            top_n=args.cost_stress_top,
            use_signal_cache=bool(args.use_signal_cache),
            signal_cache_root=args.signal_cache_root,
            refresh_signal_cache=bool(args.refresh_signal_cache),
        )
        print(f"[postprocess] wrote {out_root / 'cost_stress'}", flush=True)

    behavior_df: pd.DataFrame | None = None
    bh_top = int(args.behavior_dedupe_top) if args.behavior_dedupe_top > 0 else int(args.dedupe_top)
    if (
        args.write_behavior_unique
        and bh_top > 0
        and unique_df is not None
        and sweep_dir is not None
    ):
        behavior_df, bh_stats = write_behavior_unique_systems(
            unique_df=unique_df,
            sweep_dir=sweep_dir,
            output_root=out_root,
            behavior_dedupe_top=bh_top,
            behavior_source=args.behavior_source,
        )
        print(f"[postprocess] behavior dedupe: {bh_stats}", flush=True)

    sweep_results: pd.DataFrame | None = None
    if sweep_dir is not None:
        rp = sweep_dir / "results.csv"
        if rp.exists():
            sweep_results = pd.read_csv(rp)
            write_rank_leaderboards(
                sweep_results,
                out_root,
                min_trades_cost_rank=int(args.min_trades_cost_rank),
            )
            print(f"[postprocess] rank leaderboards -> {out_root}", flush=True)

    write_cost_robust_systems(
        out_root,
        min_trades=int(args.cost_robust_min_trades),
        slip=float(args.cost_robust_slip),
        min_total_r=float(args.cost_robust_min_total_r),
        min_pf=float(args.cost_robust_min_pf),
        max_dd_r=float(args.cost_robust_max_dd_r),
        max_median_cost_r=float(args.cost_robust_max_median_cost_r),
    )

    if int(args.min_trades_rank) > 0 and int(args.rank_high_trade_top) > 0:
        df_ht: pd.DataFrame | None = unique_df
        if df_ht is None or len(df_ht) == 0:
            tu_path = out_root / "top_unique_systems.csv"
            if tu_path.exists():
                df_ht = pd.read_csv(tu_path)
        if df_ht is not None and len(df_ht):
            write_rank_high_trade_systems(
                df_ht,
                out_root,
                min_trades_rank=int(args.min_trades_rank),
                rank_high_trade_top=int(args.rank_high_trade_top),
            )
            print(f"[postprocess] rank_high_trade -> {out_root}", flush=True)

    if args.compare_fixed_runs and sweep_dir is not None and sweep_results is not None:
        cfixed = _abs(args.compare_fixed_runs)
        assert cfixed is not None
        if unique_df is None and (out_root / "top_unique_systems.csv").exists():
            unique_df = pd.read_csv(out_root / "top_unique_systems.csv")
        if behavior_df is None and (out_root / "behavior_unique_systems.csv").exists():
            behavior_df = pd.read_csv(out_root / "behavior_unique_systems.csv")
        write_fixed_vs_sweep_comparison(
            fixed_summary_csv=cfixed,
            sweep_results=sweep_results,
            unique_df=unique_df,
            behavior_df=behavior_df,
            cost_robust_csv=out_root / "cost_robust_systems.csv",
            output_root=out_root,
        )
        print(f"[postprocess] wrote fixed_vs_sweep_comparison under {out_root}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
