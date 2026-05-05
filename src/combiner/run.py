"""CLI: Layer 2 combiner — diagnostics, single runs, detailed logs."""

from __future__ import annotations

import argparse
import json
import re
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

from src.combiner.candidate import (
    apply_combiner_rules,
    encode_candidate_metadata,
    filter_candidates,
    load_candidates,
    merged_strategy_config,
    precompute_candidate_signal_matrices,
    select_candidate_set,
    write_candidate_diagnostics,
    write_candidates_used,
)
from src.combiner.metrics import summarize_combiner
from src.combiner.simulator import CombinerConfig, simulate_combiner_legacy_logs, simulate_combiner_numba
from src.strategies.strategy.fast_utils import get_min_risk_per_share
from src.utils.config_validation import validate_common_combiner_config


def _safe_tag(tag: str) -> str:
    s = tag.strip().replace(" ", "_").replace("/", "_").replace("\\", "_")
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", tag)


def _combiner_cfg_from_yaml(cfg: dict[str, Any]) -> CombinerConfig:
    ex = cfg.get("execution") or {}
    sy = cfg.get("system") or {}
    cf = cfg.get("conflict") or {}
    out = CombinerConfig(
        max_open_positions=int(sy.get("max_open_positions", 1)),
        max_trades_per_day=int(sy.get("max_trades_per_day", 2)),
        daily_max_loss_r=float(sy.get("daily_max_loss_r", -2.0)),
        no_new_after_minute=int(ex.get("no_new_after_minute", 360)),
        eod_exit_minute=int(ex.get("eod_exit_minute", 389)),
        commission_per_trade=float(ex.get("commission_per_trade", 0.0)),
        slippage_per_share=float(ex.get("slippage_per_share", 0.01)),
        cooldown_after_loss_minutes=int(sy.get("cooldown_after_loss_minutes", 0)),
        allow_same_bar_multiple_candidates=bool(sy.get("allow_same_bar_multiple_candidates", False)),
        priority_policy=str(cf.get("priority_policy", "metadata_priority")),
        opposite_direction_skip_all=str(cf.get("opposite_direction_policy", "")).lower() == "skip_all",
        min_risk_per_share=float(ex.get("min_risk_per_share", 0.0) or 0.0),
    )
    if out.max_open_positions != 1:
        raise NotImplementedError("Layer 2 simulator supports max_open_positions=1 only")
    return out


def _resolve_paths(cfg_path: Path, cwd: Path) -> Path:
    if not cfg_path.is_absolute():
        return cwd / cfg_path
    return cfg_path


def _build_execution_arrays(
    candidates: list[Any],
    combiner_yaml: dict[str, Any],
    comb_cfg: CombinerConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n_c = len(candidates)
    max_hold = np.full(n_c, -1, dtype=np.int32)
    recomp = np.zeros(n_c, dtype=np.int8)
    qty = np.ones(n_c, dtype=np.float64)
    min_risk = np.zeros(n_c, dtype=np.float64)
    ex_min = float(comb_cfg.min_risk_per_share or 0.0)
    for ci, sp in enumerate(candidates):
        full = merged_strategy_config(sp)
        bt = full.get("backtest") or {}
        mh = bt.get("max_hold_minutes")
        max_hold[ci] = -1 if mh is None else int(mh)
        recomp[ci] = 1 if bool(bt.get("recompute_target_from_entry", True)) else 0
        qty[ci] = float(bt.get("quantity", 1.0))
        mr = float(get_min_risk_per_share(full))
        min_risk[ci] = max(mr, ex_min)
    return max_hold, recomp, qty, min_risk


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Layer 2 combiner v1.")
    p.add_argument("--candidate-root", required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--asset", default="equity")
    p.add_argument("--symbol", required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--data-dir", default="data/raw/ibkr")
    p.add_argument("--candidate-set", default=None)
    p.add_argument("--candidate-ids", nargs="*", default=None)
    p.add_argument("--top-per-strategy", type=int, default=3)
    p.add_argument("--include-warnings", action="store_true", default=None)
    p.add_argument("--no-include-warnings", action="store_false", dest="include_warnings")
    p.set_defaults(include_warnings=None)
    p.add_argument("--tag", default="run")
    p.add_argument("--output-root", default="src/combiner/results/layer2_qqq_v1")
    p.add_argument("--diagnostics-only", action="store_true")
    p.add_argument("--detailed", action="store_true", default=True)
    p.add_argument("--no-detailed", action="store_false", dest="detailed")
    p.add_argument("--no-save", action="store_true")
    args = p.parse_args(argv)

    cwd = Path.cwd()
    cfg_path = _resolve_paths(Path(args.config), cwd)
    with cfg_path.open(encoding="utf-8") as f:
        combiner_yaml = yaml.safe_load(f)

    validate_common_combiner_config(combiner_yaml)
    comb_cfg = _combiner_cfg_from_yaml(combiner_yaml)
    strategy_rules = combiner_yaml.get("strategy_rules") or {}

    root = Path(args.candidate_root)
    if not root.is_absolute():
        root = cwd / root

    raw_specs = load_candidates(root)
    raw_eligible: list[Any] = []
    for sp in raw_specs:
        rules = strategy_rules.get(sp.strategy) or {}
        if rules.get("enabled", True) is False:
            continue
        raw_eligible.append(sp)

    out_root = Path(args.output_root)
    if not out_root.is_absolute():
        out_root = cwd / out_root

    if args.diagnostics_only:
        sets_cfg = combiner_yaml.get("candidate_sets") or {}
        profile: dict[str, Any]
        if args.candidate_set and args.candidate_set in sets_cfg:
            profile = dict(sets_cfg[args.candidate_set])
        else:
            profile = {"include_warnings": True, "max_per_strategy": args.top_per_strategy}
        if args.include_warnings is not None:
            profile["include_warnings"] = args.include_warnings
        diag_sel = select_candidate_set(raw_eligible, profile, top_per_strategy=args.top_per_strategy)
        if args.candidate_ids:
            want = set(args.candidate_ids)
            diag_sel = [c for c in diag_sel if c.candidate_id in want]

        csm = precompute_candidate_signal_matrices(
            candidates=diag_sel,
            asset=args.asset,
            symbol=args.symbol,
            start=args.start,
            end=args.end,
            data_dir=args.data_dir,
        )
        diag_dir = out_root / "diagnostics"
        write_candidate_diagnostics(csm, diag_dir)
        tot_sig = int(np.sum(csm.valid & (csm.side != 0)))
        by_st: dict[str, int] = {}
        zero_ids: list[str] = []
        for ci, c in enumerate(csm.candidates):
            v = int(np.sum(csm.valid[ci] & (csm.side[ci] != 0)))
            by_st[c.strategy] = by_st.get(c.strategy, 0) + v
            if v == 0:
                zero_ids.append(c.candidate_id)
        print(f"[diagnostics] candidates={len(diag_sel)} total_signals={tot_sig}", flush=True)
        print(f"[diagnostics] by_strategy={json.dumps(by_st, sort_keys=True)}", flush=True)
        if zero_ids:
            print(f"[diagnostics] zero_signal_candidates={zero_ids}", flush=True)
        print(f"[diagnostics] wrote {diag_dir}", flush=True)
        return 0

    if args.candidate_ids:
        merged_specs = filter_candidates(
            raw_eligible,
            candidate_ids=args.candidate_ids,
            top_per_strategy=None,
        )
    else:
        if not args.candidate_set:
            print("ERROR: --candidate-set or --candidate-ids required", file=sys.stderr)
            return 2
        sets_cfg = combiner_yaml.get("candidate_sets") or {}
        if args.candidate_set not in sets_cfg:
            print(f"ERROR: unknown candidate_set {args.candidate_set}", file=sys.stderr)
            return 2
        profile = dict(sets_cfg[args.candidate_set])
        if args.include_warnings is not None:
            profile["include_warnings"] = args.include_warnings
        merged_specs = select_candidate_set(raw_eligible, profile, top_per_strategy=args.top_per_strategy)

    merged: list[Any] = []
    for sp in merged_specs:
        rules = strategy_rules.get(sp.strategy) or {}
        if rules.get("enabled", True) is False:
            continue
        merged.append(apply_combiner_rules(sp, strategy_rules))

    if not merged:
        print("ERROR no candidates after filters", file=sys.stderr)
        return 2

    csm = precompute_candidate_signal_matrices(
        candidates=merged,
        asset=args.asset,
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        data_dir=args.data_dir,
    )

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

    if args.detailed:
        sim_out = simulate_combiner_legacy_logs(
            backtest_arrays=bt_arr,
            candidate_arrays=mats,
            candidate_specs=merged,
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
    else:
        sim_out = simulate_combiner_numba(
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
    equity_df = sim_out["equity_df"]
    log_df = sim_out["candidate_signal_log_df"]
    rej_df = sim_out["rejected_signals_df"]
    rej_counts = sim_out.get("rejection_counts")

    metrics = summarize_combiner(
        trades_df,
        rej_df,
        log_df,
        rejection_counts=rej_counts,
    )

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    tag_s = _safe_tag(args.tag) if args.tag else "run"
    run_dir = out_root / f"run_{ts}_{tag_s}"
    if not args.no_save:
        run_dir.mkdir(parents=True, exist_ok=True)
        trades_df.to_csv(run_dir / "trades.csv", index=False)
        equity_df.to_csv(run_dir / "equity.csv", index=False)
        if args.detailed:
            log_df.to_csv(run_dir / "candidate_signal_log.csv", index=False)
            rej_df.to_csv(run_dir / "rejected_signals.csv", index=False)
        (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")
        write_candidates_used(merged, run_dir / "candidates_used.csv")

        dump_cfg = {
            "combiner_yaml": combiner_yaml,
            "run": {
                "asset": args.asset,
                "symbol": args.symbol,
                "start": args.start,
                "end": args.end,
                "candidate_set": args.candidate_set,
                "candidate_ids": args.candidate_ids,
                "top_per_strategy": args.top_per_strategy,
                "tag": args.tag,
                "detailed": args.detailed,
            },
        }
        (run_dir / "config_resolved.yaml").write_text(yaml.safe_dump(dump_cfg, sort_keys=False), encoding="utf-8")

        summary_lines = [
            f"out={run_dir.resolve()}",
            f"candidates={','.join(s.candidate_id for s in merged)}",
            f"trades={metrics.get('trades', 0)}",
            f"total_r={metrics.get('total_r', 0)}",
            f"total_net_pnl={metrics.get('total_net_pnl', 0)}",
            f"profit_factor={metrics.get('profit_factor', 0)}",
            f"combiner_score={metrics.get('combiner_score', 0)}",
            f"selection_rate={metrics.get('selection_rate', 0)}",
            f"rejected_by_reason={metrics.get('rejected_by_reason_json', '{}')}",
        ]
        (run_dir / "summary.txt").write_text("\n".join(summary_lines), encoding="utf-8")

    print("candidates:", ", ".join(s.candidate_id for s in merged), flush=True)
    pick_keys = (
        "trades",
        "total_r",
        "profit_factor",
        "max_drawdown_r",
        "combiner_score",
        "selection_rate",
        "rejected_by_reason_json",
    )
    print("metrics:", json.dumps({k: metrics.get(k) for k in pick_keys}, indent=2, default=str), flush=True)
    if not args.no_save:
        print("output:", run_dir.resolve(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
