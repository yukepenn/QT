"""Thin Layer1 promotion / candidate validation (no backtests, no PnL).

Reads ``sweep_results.csv`` + ``sweep_meta.json`` under a ``runs-root``,
reconstructs frozen configs, and writes combiner-compatible ``*.yaml`` files
under ``candidate-root`` when ``--write`` is used.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from src.backtest.strategy_runner import (
    apply_combo_overrides,
    finalize_backtest_config,
    merge_strategy_config,
)
from src.combiner.candidate import load_candidate_yaml, load_candidates


def _repo_relative(p: Path, *, cwd: Path) -> str:
    try:
        return p.resolve().relative_to(cwd.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def _slug(strategy: str) -> str:
    return strategy.strip().upper()


def _safe_float(x: Any, default: float = float("nan")) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    if math.isnan(v) or math.isinf(v):
        return default
    return v


def _default_metadata_from_cfg(strategy: str, cfg: dict[str, Any]) -> dict[str, Any]:
    sig = cfg.get("signal") or {}
    side = str(sig.get("side", "long_only"))
    est = sig.get("entry_start_minute")
    eed = sig.get("entry_end_minute")
    return {
        "family": strategy.split("_")[0] if "_" in strategy else strategy,
        "setup_type": strategy,
        "conflict_group": "QQQ_directional",
        "default_priority": 50,
        "default_active_start_minute": int(est or 0),
        "default_active_end_minute": int(eed or 389),
        "allowed_sides": side,
        "default_management_mode": str((cfg.get("risk") or {}).get("target_mode", "fixed_r")),
    }


def run_validate_candidates(candidate_root: Path, *, allow_empty: bool) -> None:
    paths = sorted(candidate_root.glob("*.yaml"))
    if not paths:
        if allow_empty:
            return
        raise ValueError(f"no *.yaml under {candidate_root}")
    for p in paths:
        load_candidate_yaml(p)
    load_candidates(candidate_root)


def _rank_key(row: pd.Series) -> tuple[Any, ...]:
    warn = str(row.get("notes", "") or "").strip()
    pfr = _safe_float(row.get("profit_factor_r"), float("nan"))
    pfr_sort = pfr if not math.isnan(pfr) else float("-inf")
    total_r = _safe_float(row.get("total_r", 0.0), 0.0)
    mdd = _safe_float(row.get("max_drawdown_r", 0.0), 0.0)
    tc = int(float(row.get("trade_count", 0) or 0))
    cid = str(row.get("combo_id", ""))
    return (0 if not warn else 1, -pfr_sort, -total_r, mdd, -tc, cid)


def run_promote(
    *,
    runs_root: Path,
    candidate_root: Path,
    max_per_strategy: int,
    min_trades: int,
    min_profit_factor_r: float,
    min_total_r: float,
    gate_label: str,
    dry_run: bool,
    cwd: Path | None = None,
) -> None:
    cwd = cwd or Path.cwd()
    runs_root = runs_root.resolve()
    candidate_root = candidate_root.resolve()
    if not runs_root.is_dir():
        raise FileNotFoundError(runs_root)

    run_dirs = sorted(d for d in runs_root.iterdir() if d.is_dir())
    selected_rows: list[dict[str, Any]] = []
    reject_rows: list[dict[str, Any]] = []

    for rd in run_dirs:
        meta_p = rd / "sweep_meta.json"
        csv_p = rd / "sweep_results.csv"
        if not meta_p.is_file() or not csv_p.is_file():
            continue
        meta = json.loads(meta_p.read_text(encoding="utf-8"))
        df = pd.read_csv(csv_p)
        strategy = str(meta.get("strategy", ""))
        if not strategy or df.empty:
            continue
        for _, row in df.iterrows():
            tc = int(float(row.get("trade_count", 0) or 0))
            total_r = _safe_float(row.get("total_r", 0.0), 0.0)
            pfr = _safe_float(row.get("profit_factor_r"), float("nan"))
            rec = {**row.to_dict(), "_run_dir": str(rd), "_strategy": strategy, "_meta": meta}
            if tc < min_trades:
                rr = {k: v for k, v in rec.items() if k != "_meta"}
                rr["reject_reason"] = "min_trades"
                reject_rows.append(rr)
                continue
            if total_r < min_total_r:
                rr = {k: v for k, v in rec.items() if k != "_meta"}
                rr["reject_reason"] = "min_total_r"
                reject_rows.append(rr)
                continue
            if math.isnan(pfr) or pfr < min_profit_factor_r:
                rr = {k: v for k, v in rec.items() if k != "_meta"}
                rr["reject_reason"] = "min_profit_factor_r"
                reject_rows.append(rr)
                continue
            selected_rows.append(rec)

    by_s: dict[str, list[dict[str, Any]]] = {}
    for r in selected_rows:
        by_s.setdefault(str(r["_strategy"]), []).append(r)
    final: list[dict[str, Any]] = []
    for s in sorted(by_s.keys()):
        rows = sorted(by_s[s], key=_rank_key)
        final.extend(rows[: max(1, int(max_per_strategy))])

    if dry_run:
        print(f"[dry-run] would write {len(final)} candidate(s) to {candidate_root}", flush=True)
        for r in final:
            print(f"  - {r.get('combo_id')} {r.get('_strategy')} trade_count={r.get('trade_count')}", flush=True)
        return

    candidate_root.mkdir(parents=True, exist_ok=True)
    rank_by_strategy: dict[str, int] = {}

    for r in final:
        strategy = str(r["_strategy"])
        meta = r["_meta"]
        rd = Path(r["_run_dir"])
        rank_by_strategy[strategy] = rank_by_strategy.get(strategy, 0) + 1
        rk = rank_by_strategy[strategy]
        cid = f"{_slug(strategy)}_L1E_{rk:03d}"

        cfg_path = str(meta.get("config_path") or "").strip()
        base = merge_strategy_config(strategy, Path(cfg_path) if cfg_path else None, None)
        params = json.loads(str(r.get("params_json") or "{}"))
        cfg = apply_combo_overrides(base, params)
        finalize_backtest_config(cfg)

        metrics = {
            "trade_count": int(float(r.get("trade_count", 0) or 0)),
            "total_r": _safe_float(r.get("total_r", 0.0), 0.0),
            "profit_factor_r": _safe_float(r.get("profit_factor_r"), float("nan")),
            "max_drawdown_r": _safe_float(r.get("max_drawdown_r", 0.0), 0.0),
            "avg_r": _safe_float(r.get("avg_r", 0.0), 0.0),
            "win_rate": _safe_float(r.get("win_rate", 0.0), 0.0),
            "config_hash": str(r.get("config_hash", "")),
            "combo_id": str(r.get("combo_id", "")),
        }
        meta_out = _default_metadata_from_cfg(strategy, cfg)
        sem = str(r.get("execution_semantics_version") or meta.get("execution_semantics_version") or "")
        sigv = str(r.get("signal_contract_version") or "")
        sym = str(meta.get("symbols") or meta.get("symbol") or "QQQ")
        out_doc: dict[str, Any] = {
            "candidate_id": cid,
            "strategy": strategy,
            "symbol": sym,
            "asset": str(meta.get("asset", "equity")),
            "candidate_rank": rk,
            "config": cfg,
            "metrics": metrics,
            "metadata": meta_out,
            "selection": {
                "gate_label": gate_label,
                "score": float(metrics["total_r"]),
                "warning": str(r.get("notes", "") or ""),
            },
            "source": {
                "results_csv": _repo_relative(rd / "sweep_results.csv", cwd=cwd),
                "sweep_folder": _repo_relative(rd, cwd=cwd),
            },
            "execution": {
                "execution_engine": "execution_backed",
                "execution_semantics_version": sem,
                "signal_contract_version": sigv,
            },
        }
        out_p = candidate_root / f"{cid}.yaml"
        out_p.write_text(yaml.safe_dump(out_doc, sort_keys=False, default_flow_style=False), encoding="utf-8")

    index_rows = []
    for p in sorted(candidate_root.glob("*.yaml")):
        c = load_candidate_yaml(p)
        index_rows.append(
            {
                "candidate_id": c.candidate_id,
                "strategy": c.strategy,
                "path": p.name,
                "gate_label": gate_label,
            }
        )
    if index_rows:
        pd.DataFrame(index_rows).to_csv(candidate_root / "CANDIDATE_INDEX.csv", index=False)
    if final:
        clean = [{k: v for k, v in r.items() if not k.startswith("_")} for r in final]
        pd.DataFrame(clean).to_csv(candidate_root / "selected_candidates_summary.csv", index=False)
    if reject_rows:
        pd.DataFrame(reject_rows).to_csv(candidate_root / "candidate_rejects_summary.csv", index=False)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Layer1 execution-backed controlled promotion / validation.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("promote", help="Select sweep rows and write candidate YAMLs.")
    pr.add_argument("--runs-root", type=Path, required=True)
    pr.add_argument("--candidate-root", type=Path, required=True)
    pr.add_argument("--max-per-strategy", type=int, default=3)
    pr.add_argument("--min-trades", type=int, default=20)
    pr.add_argument("--min-profit-factor-r", type=float, default=1.05)
    pr.add_argument("--min-total-r", type=float, default=0.0)
    pr.add_argument("--gate-label", type=str, default="L1_EXECUTION_BACKED_CONTROLLED_STRICT_V1")
    pr.add_argument("--write", action="store_true", help="Write YAML/CSVs (default is dry-run).")
    pr.set_defaults(handler="promote")

    va = sub.add_parser("validate-candidates", help="Load all *.yaml under root with combiner loader.")
    va.add_argument("--candidate-root", type=Path, required=True)
    va.add_argument("--allow-empty", action="store_true")
    va.set_defaults(handler="validate")

    return p


def main(argv: list[str] | None = None) -> int:
    p = _build_parser()
    args = p.parse_args(argv)
    if args.handler == "validate":
        try:
            run_validate_candidates(args.candidate_root, allow_empty=bool(args.allow_empty))
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        return 0
    if args.handler == "promote":
        try:
            run_promote(
                runs_root=args.runs_root,
                candidate_root=args.candidate_root,
                max_per_strategy=int(args.max_per_strategy),
                min_trades=int(args.min_trades),
                min_profit_factor_r=float(args.min_profit_factor_r),
                min_total_r=float(args.min_total_r),
                gate_label=str(args.gate_label),
                dry_run=not bool(args.write),
            )
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
