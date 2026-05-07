"""Layer 2 combiner rule sweep: single signal precompute, fast Numba evaluation."""

from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from datetime import datetime, timezone
from itertools import product
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
    resolve_candidate_universe_for_grid,
    select_candidate_set,
    write_candidates_used,
)
from src.combiner.precompute import (
    precompute_candidate_signal_matrices,
    resolve_precompute_signal_cache_settings,
)
from src.combiner.metrics import execution_config_from_parts, summarize_combiner
from src.combiner.run import _build_execution_arrays, _combiner_cfg_from_yaml, _safe_tag
from src.combiner.simulator import simulate_combiner_legacy_logs, simulate_combiner_numba
from src.utils.config_validation import validate_common_combiner_config


def _deep_set(cfg: dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    cur: dict[str, Any] = cfg
    for p in parts[:-1]:
        nxt = cur.get(p)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[p] = nxt
        cur = nxt
    cur[parts[-1]] = value


def _merge_dotted(fixed: dict[str, Any], target: dict[str, Any]) -> None:
    for k, v in fixed.items():
        if "." in k:
            _deep_set(target, k, v)
        else:
            target[k] = v


def _expand_grid(grid: dict[str, Any]) -> list[dict[str, Any]]:
    keys = list(grid.keys())
    lists: list[list[Any]] = []
    for k in keys:
        v = grid[k]
        if isinstance(v, list):
            lists.append(v)
        else:
            lists.append([v])
    return [dict(zip(keys, combo)) for combo in product(*lists)]


def _apply_combo_to_cfg(
    base: dict[str, Any],
    combo: dict[str, Any],
    *,
    reserved: set[str],
) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in combo.items():
        if k in reserved:
            continue
        if "." in str(k):
            _deep_set(out, str(k), v)
        else:
            out[k] = v
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Layer 2 combiner sweep.")
    p.add_argument("--candidate-root", required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--asset", default="equity")
    p.add_argument("--symbol", required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--data-dir", default="data/raw/ibkr")
    p.add_argument("--output-root", default="src/combiner/results/layer2_qqq_v1")
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--detail-top", type=int, default=10)
    p.add_argument("--progress-every", type=int, default=100)
    p.add_argument("--tag", default="sweep")
    p.add_argument("--use-signal-cache", action="store_true")
    p.add_argument("--signal-cache-root", default=None)
    p.add_argument("--refresh-signal-cache", action="store_true")
    args = p.parse_args(argv)

    cwd = Path.cwd()
    sweep_path = Path(args.config)
    if not sweep_path.is_absolute():
        sweep_path = cwd / sweep_path
    with sweep_path.open(encoding="utf-8") as f:
        sweep_doc = yaml.safe_load(f)

    base_rel = Path(str(sweep_doc["base_config"]))
    if not base_rel.is_absolute():
        base_path = cwd / base_rel
    else:
        base_path = base_rel
    with base_path.open(encoding="utf-8") as f:
        base_cfg = yaml.safe_load(f)

    use_sc, sc_root, refresh_sc = resolve_precompute_signal_cache_settings(
        base_cfg,
        cli_use_signal_cache=bool(args.use_signal_cache),
        cli_signal_cache_root=args.signal_cache_root,
        cli_refresh_signal_cache=bool(args.refresh_signal_cache),
    )
    print(
        f"[precompute-cache] use_signal_cache={use_sc} root={sc_root} refresh={refresh_sc}",
        flush=True,
    )

    fixed = sweep_doc.get("fixed") or {}
    _merge_dotted(fixed, base_cfg)

    grid = sweep_doc.get("grid") or {}
    reserved = {"candidate_set", "top_per_strategy"}
    combo_rows = _expand_grid(grid)
    n_combo = len(combo_rows)

    root = Path(args.candidate_root)
    if not root.is_absolute():
        root = cwd / root

    raw = load_candidates(root)
    strategy_rules = base_cfg.get("strategy_rules") or {}
    raw_eligible: list[Any] = []
    for sp in raw:
        rules = strategy_rules.get(sp.strategy) or {}
        if rules.get("enabled", True) is False:
            continue
        raw_eligible.append(sp)

    out_root = Path(args.output_root)
    if not out_root.is_absolute():
        out_root = cwd / out_root
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    tag_s = _safe_tag(args.tag)
    sweep_dir = out_root / f"sweep_{ts}_{tag_s}"
    sweep_dir.mkdir(parents=True, exist_ok=True)

    pre_raw = resolve_candidate_universe_for_grid(raw_eligible, base_cfg, combo_rows)
    universe = [apply_combiner_rules(sp, strategy_rules) for sp in pre_raw]
    n_full = len(raw_eligible)
    n_pre = len(universe)
    if n_pre < n_full:
        print(
            f"[Layer2 sweep] precompute universe filtered: {n_pre}/{n_full} candidates "
            f"(union over grid candidate_sets × top_per_strategy)",
            flush=True,
        )
    else:
        print(
            f"[Layer2 sweep] precompute universe: all {n_pre} eligible candidates",
            flush=True,
        )

    if not universe:
        print("ERROR empty candidate universe", file=sys.stderr)
        return 2

    print(f"[Layer2 sweep] precomputing signals for {len(universe)} candidates...", flush=True)
    t0 = time.perf_counter()
    csm = precompute_candidate_signal_matrices(
        candidates=universe,
        asset=args.asset,
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        data_dir=args.data_dir,
        profile_csv_path=sweep_dir / "candidate_precompute_profile.csv",
        use_signal_cache=use_sc,
        signal_cache_root=sc_root,
        refresh_signal_cache=refresh_sc,
    )
    print(f"[Layer2 sweep] precompute done in {(time.perf_counter()-t0):.1f}s", flush=True)

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

    sets_cfg = base_cfg.get("candidate_sets") or {}

    results_rows: list[dict[str, Any]] = []
    t_sweep0 = time.perf_counter()
    best_score = float("-inf")

    for idx, combo in enumerate(combo_rows, start=1):
        row_start = time.perf_counter()
        cs_name = str(combo["candidate_set"])
        tps = int(combo["top_per_strategy"])
        if cs_name not in sets_cfg:
            print(f"WARN skip unknown candidate_set {cs_name}", file=sys.stderr)
            continue
        profile = dict(sets_cfg[cs_name])
        merged_cfg = _apply_combo_to_cfg(base_cfg, combo, reserved=reserved)
        validate_common_combiner_config(merged_cfg)
        comb_cfg = _combiner_cfg_from_yaml(merged_cfg)
        max_hold, recomp, qty, min_risk = _build_execution_arrays(universe, merged_cfg, comb_cfg)

        selected = select_candidate_set(raw_eligible, profile, top_per_strategy=tps)
        enabled = build_enabled_mask(universe, selected)

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
        trades_df = sim_out["trades_df"]
        rej_counts = sim_out.get("rejection_counts")
        empty_log = pd.DataFrame()
        exec_cfg = execution_config_from_parts(
            comb_cfg.slippage_per_share,
            comb_cfg.commission_per_trade,
            qty,
        )
        metrics = summarize_combiner(
            trades_df,
            pd.DataFrame(),
            empty_log,
            rejection_counts=rej_counts,
            execution_config=exec_cfg,
        )
        elapsed_ms = int((time.perf_counter() - row_start) * 1000)
        cs = float(metrics.get("combiner_score", 0.0) or 0.0)
        best_score = max(best_score, cs)

        row_out: dict[str, Any] = {
            "combo_id": idx,
            "candidate_set": cs_name,
            "top_per_strategy": tps,
            "max_trades_per_day": comb_cfg.max_trades_per_day,
            "daily_max_loss_r": comb_cfg.daily_max_loss_r,
            "cooldown_after_loss_minutes": comb_cfg.cooldown_after_loss_minutes,
            "priority_policy": comb_cfg.priority_policy,
            "n_candidates": int(enabled.sum()),
            "candidate_ids_json": json.dumps([c.candidate_id for c in selected], sort_keys=True),
            "elapsed_ms": elapsed_ms,
            **{k: metrics[k] for k in metrics if isinstance(k, str)},
        }
        results_rows.append(row_out)

        pe = int(args.progress_every)
        if pe > 0 and (idx % pe == 0 or idx == n_combo):
            print(
                f"[Layer2 sweep] combo {idx}/{n_combo} best_score={best_score:.4f} elapsed_sweep={(time.perf_counter()-t_sweep0):.1f}s",
                flush=True,
            )

    df = pd.DataFrame(results_rows)
    if len(df):
        df = df.sort_values(
            by=["combiner_score", "profit_factor", "total_r"],
            ascending=[False, False, False],
            na_position="last",
        )

    results_path = sweep_dir / "results.csv"
    df.to_csv(results_path, index=False)

    top_n = int(args.top)
    head_df = df.head(top_n) if len(df) else df
    try:
        top_tbl = head_df.to_markdown(index=False) if len(head_df) else "(empty)"
    except Exception:
        top_tbl = head_df.to_string(index=False) if len(head_df) else "(empty)"
    md_lines = [
        f"# Layer 2 sweep `{tag_s}`",
        "",
        f"- combos: {len(df)}",
        f"- precompute_candidates: {len(universe)}",
        f"- eligible_candidates_full: {n_full}",
        "",
        "## Top rows",
        "",
        top_tbl,
        "",
    ]
    (sweep_dir / "summary.md").write_text("\n".join(md_lines), encoding="utf-8")

    # Detailed reruns for top `--detail-top`
    detail_n = min(int(args.detail_top), len(df))
    if detail_n > 0:
        top_dir = sweep_dir / "top_runs"
        top_dir.mkdir(exist_ok=True)
        for rank, (_, row) in enumerate(df.head(detail_n).iterrows(), start=1):
            combo_id = int(row["combo_id"])
            combo = combo_rows[combo_id - 1]
            cs_name = str(combo["candidate_set"])
            tps = int(combo["top_per_strategy"])
            merged_cfg = _apply_combo_to_cfg(base_cfg, combo, reserved=reserved)
            comb_cfg = _combiner_cfg_from_yaml(merged_cfg)
            max_hold, recomp, qty, min_risk = _build_execution_arrays(universe, merged_cfg, comb_cfg)
            profile = dict(sets_cfg[cs_name])
            selected = select_candidate_set(raw_eligible, profile, top_per_strategy=tps)
            enabled = build_enabled_mask(universe, selected)

            sim_out = simulate_combiner_legacy_logs(
                backtest_arrays=bt_arr,
                candidate_arrays=mats,
                candidate_specs=universe,
                session_date=meta["session_date"],
                minute=meta["minute_from_open"],
                ts_utc=meta["ts_utc"],
                combiner_cfg=comb_cfg,
                opposite_direction_skip_all=comb_cfg.opposite_direction_skip_all,
                max_hold_per_candidate=max_hold,
                recompute_target=recomp,
                quantity_per_candidate=qty,
                min_risk_per_candidate=min_risk,
                enabled_mask=enabled,
            )
            rdir = top_dir / f"rank_{rank:03d}"
            rdir.mkdir(parents=True, exist_ok=True)
            sim_out["trades_df"].to_csv(rdir / "trades.csv", index=False)
            sim_out["equity_df"].to_csv(rdir / "equity.csv", index=False)
            sim_out["candidate_signal_log_df"].to_csv(rdir / "candidate_signal_log.csv", index=False)
            sim_out["rejected_signals_df"].to_csv(rdir / "rejected_signals.csv", index=False)
            write_candidates_used(selected, rdir / "candidates_used.csv")
            exec_cfg_d = execution_config_from_parts(
                comb_cfg.slippage_per_share,
                comb_cfg.commission_per_trade,
                qty,
            )
            metrics_d = summarize_combiner(
                sim_out["trades_df"],
                sim_out["rejected_signals_df"],
                sim_out["candidate_signal_log_df"],
                rejection_counts=None,
                execution_config=exec_cfg_d,
            )
            (rdir / "metrics.json").write_text(json.dumps(metrics_d, indent=2, default=str), encoding="utf-8")
            (rdir / "config_resolved.yaml").write_text(yaml.safe_dump(merged_cfg, sort_keys=False), encoding="utf-8")
            (rdir / "summary.txt").write_text(
                f"combo_id={combo_id}\ncandidate_set={cs_name}\nmetrics={json.dumps({k: metrics_d.get(k) for k in ('trades','total_r','profit_factor','combiner_score')}, default=str)}\n",
                encoding="utf-8",
            )

    print(f"[Layer2 sweep] wrote {results_path} ({len(df)} rows)", flush=True)
    print(f"[Layer2 sweep] total_elapsed_s={(time.perf_counter()-t_sweep0):.1f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
