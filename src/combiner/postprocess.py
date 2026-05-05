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
    precompute_candidate_signal_matrices,
)
from src.combiner.metrics import summarize_combiner
from src.combiner.run import _build_execution_arrays, _combiner_cfg_from_yaml
from src.combiner.simulator import simulate_combiner_numba

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
) -> pd.DataFrame:
    with base_config_path.open(encoding="utf-8") as f:
        base_cfg = yaml.safe_load(f)

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

    print(f"[postprocess] cost stress: precomputing {len(universe)} candidates...", flush=True)
    csm = precompute_candidate_signal_matrices(
        candidates=universe,
        asset=asset,
        symbol=symbol,
        start=start,
        end=end,
        data_dir=data_dir,
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

    stress_dir = output_root / "cost_stress"
    stress_dir.mkdir(parents=True, exist_ok=True)
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
                metrics = summarize_combiner(
                    sim_out["trades_df"],
                    pd.DataFrame(),
                    pd.DataFrame(),
                    rejection_counts=sim_out.get("rejection_counts"),
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
    p.add_argument("--diagnostics-dir", type=Path, default=None)
    p.add_argument("--diagnostics-date-range", default="2025-01-01 — 2026-04-30")
    p.add_argument("--collect-fixed-runs", type=Path, default=None, help="Scan run_* folders and write fixed_run_summary.")
    args = p.parse_args(argv)

    cwd = Path.cwd()
    out_root = args.output_root
    if not out_root.is_absolute():
        out_root = cwd / out_root

    if args.collect_fixed_runs:
        fr = args.collect_fixed_runs
        if not fr.is_absolute():
            fr = cwd / fr
        collect_fixed_run_summary(fr, out_root)
        print(f"[postprocess] collected fixed runs from {fr}", flush=True)

    if args.diagnostics_dir:
        ddir = args.diagnostics_dir
        if not ddir.is_absolute():
            ddir = cwd / ddir
        write_diagnostics_summary(ddir, date_range=args.diagnostics_date_range)
        print(f"[postprocess] wrote {ddir / 'diagnostics_summary.md'}", flush=True)

    unique_df: pd.DataFrame | None = None
    if args.dedupe_top and args.sweep_dir:
        sd = args.sweep_dir
        if not sd.is_absolute():
            sd = cwd / sd
        unique_df, stats = dedupe_sweep(sd, out_root, dedupe_top=args.dedupe_top)
        print(f"[postprocess] dedupe: {stats}", flush=True)
        map_unique_to_top_runs(unique_df, sd, out_root, max_rank=50)

    if args.cost_stress_top and unique_df is None and (out_root / "top_unique_systems.csv").exists():
        unique_df = pd.read_csv(out_root / "top_unique_systems.csv")

    if args.cost_stress_top and unique_df is not None and args.candidate_root and args.config:
        cr = args.candidate_root
        cf = args.config
        if not cr.is_absolute():
            cr = cwd / cr
        if not cf.is_absolute():
            cf = cwd / cf
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
        )
        print(f"[postprocess] wrote {out_root / 'cost_stress'}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
