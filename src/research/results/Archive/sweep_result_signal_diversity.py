"""Audit signal-mask diversity for raw Layer-1 sweep results.csv rows."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.features.feature_store import FeatureStore
from src.research.candidate_signal_diversity import analyze_merged_config
from src.research.scoring import candidate_score, passes_filters, safe_float
from src.research.select_candidates import _validate_results_df, unflatten_config_from_row
from src.strategies.loader import apply_overrides, load_strategy_config


def _filter_ns(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        min_trades=args.filter_min_trades,
        min_profit_factor=args.filter_min_profit_factor,
        min_total_r=args.filter_min_total_r,
        max_drawdown_r=args.filter_max_drawdown_r,
        max_avg_bars_held=args.filter_max_avg_bars_held,
        max_eod_count=0,
        max_end_of_data_count=0,
    )


def merged_config_from_row(
    strategy: str,
    row: pd.Series,
    *,
    base_cfg: dict[str, Any] | None,
) -> dict[str, Any]:
    overlay = unflatten_config_from_row(row)
    if not overlay.get("strategy"):
        overlay = {"strategy": strategy, **overlay}
    base = dict(base_cfg) if base_cfg is not None else dict(load_strategy_config(strategy))
    return apply_overrides(base, overlay)


def _count_unique_pure(rows: list[dict[str, Any]]) -> int:
    s = {r.get("pure_signal_hash", "") for r in rows if r.get("pure_signal_hash")}
    s.discard("")
    return len(s)


def run_audit(
    *,
    strategy: str,
    results_csv: Path,
    base_cfg: dict[str, Any] | None,
    asset: str,
    symbol: str,
    start: str,
    end: str,
    output_root: Path,
    top_pool: int,
    filter_ns: argparse.Namespace,
    top_per_signal_hash: int,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(results_csv)
    _validate_results_df(df, path=results_csv)
    df = df.copy()
    df.insert(0, "__source_row__", range(len(df)))
    df = df[df["strategy"].astype(str) == strategy].copy()
    summary: dict[str, Any] = {
        "strategy": strategy,
        "n_rows_in_csv": int(len(df)),
        "n_strict_eligible": 0,
        "unique_pure_top20": 0,
        "unique_pure_top50": 0,
        "unique_pure_top100": 0,
        "unique_pure_top_pool": 0,
        "errors_in_pool": 0,
    }

    raw_csv = output_root / f"raw_sweep_signal_diversity_{strategy}.csv"
    uniq_csv = output_root / f"unique_signal_hash_candidates_{strategy}.csv"
    dup_csv = output_root / f"duplicate_signal_hash_groups_{strategy}.csv"
    raw_md = output_root / f"raw_sweep_signal_diversity_{strategy}.md"

    if df.empty:
        summary["note"] = "no_rows_for_strategy"
        for p in (raw_csv, uniq_csv, dup_csv):
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["status", "message"])
                w.writerow(["empty", "no rows"])
        raw_md.write_text(f"# Raw sweep signal diversity — {strategy}\n\nEmpty.\n", encoding="utf-8")
        return summary

    filt = df[df.apply(lambda r: passes_filters(r, filter_ns), axis=1)].copy()
    summary["n_strict_eligible"] = int(len(filt))
    if filt.empty:
        summary["note"] = "no_strict_rows"
        fields = [
            "row_rank",
            "strategy",
            "source_row_index",
            "trades",
            "total_r",
            "profit_factor",
            "max_drawdown_r",
            "avg_bars_held",
            "candidate_score",
            "pure_signal_hash",
            "signal_detail_hash",
            "n_signals",
            "hash_group_rank",
            "is_unique_pure_signal_hash",
            "output_candidate_id_suggestion",
            "status",
            "error",
        ]
        for p in (raw_csv, uniq_csv):
            with p.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fields)
                w.writeheader()
        with dup_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["pure_signal_hash", "n_rows_in_pool", "source_row_indices"],
            )
            w.writeheader()
        raw_md.write_text(
            f"# Raw sweep signal diversity — {strategy}\n\n**No strict-eligible rows.**\n",
            encoding="utf-8",
        )
        return summary

    filt["_candidate_score"] = filt.apply(candidate_score, axis=1)
    filt = filt.sort_values("_candidate_score", ascending=False)

    store = FeatureStore(asset=asset, symbol=symbol.upper(), start=start, end=end)
    max_scan = min(100, len(filt))
    pure_seq: list[str] = []
    for _, row in filt.head(max_scan).iterrows():
        try:
            cfg = merged_config_from_row(strategy, row, base_cfg=base_cfg)
            core = analyze_merged_config(strategy, cfg, store=store)
            pure_seq.append(str(core.get("pure_signal_hash") or ""))
        except Exception:
            pure_seq.append("")

    def _nuniq_head(k: int) -> int:
        kk = min(k, len(pure_seq))
        return len({h for h in pure_seq[:kk] if h})

    summary["unique_pure_top20"] = _nuniq_head(20)
    summary["unique_pure_top50"] = _nuniq_head(50)
    summary["unique_pure_top100"] = _nuniq_head(100)

    pool = filt.head(min(int(top_pool), len(filt))).copy()

    pool_rows: list[dict[str, Any]] = []
    row_rank = 0
    for _, row in pool.iterrows():
        row_rank += 1
        out: dict[str, Any] = {
            "row_rank": row_rank,
            "strategy": strategy,
            "source_row_index": int(row["__source_row__"]),
            "trades": int(safe_float(row.get("trades"), 0)),
            "total_r": safe_float(row.get("total_r")),
            "profit_factor": safe_float(row.get("profit_factor")),
            "max_drawdown_r": safe_float(row.get("max_drawdown_r")),
            "avg_bars_held": safe_float(row.get("avg_bars_held")),
            "candidate_score": float(row["_candidate_score"]),
            "candidate_score_csv": safe_float(row.get("candidate_score"), float("nan")),
            "pure_signal_hash": "",
            "signal_detail_hash": "",
            "n_signals": 0,
            "hash_group_rank": "",
            "is_unique_pure_signal_hash": "",
            "output_candidate_id_suggestion": "",
            "status": "",
            "error": "",
        }
        try:
            cfg = merged_config_from_row(strategy, row, base_cfg=base_cfg)
            core = analyze_merged_config(strategy, cfg, store=store)
            out["pure_signal_hash"] = core.get("pure_signal_hash", "")
            out["signal_detail_hash"] = core.get("signal_hash", "")
            out["n_signals"] = core.get("n_signals", 0)
            out["status"] = core.get("status", "")
            ph = str(out["pure_signal_hash"])
            if ph:
                same_before = sum(
                    1 for pr in pool_rows if pr.get("pure_signal_hash") == ph
                )
                out["hash_group_rank"] = same_before + 1
                out["is_unique_pure_signal_hash"] = same_before == 0
            else:
                out["hash_group_rank"] = ""
                out["is_unique_pure_signal_hash"] = ""
            slug = strategy.upper().replace("-", "_")
            out["output_candidate_id_suggestion"] = f"{slug}_RAW_{row_rank:03d}"
        except Exception as e:
            out["status"] = "error"
            out["error"] = f"{type(e).__name__}: {e}"
            summary["errors_in_pool"] += 1
        pool_rows.append(out)

    ok_rows = [r for r in pool_rows if r.get("status") == "ok" and r.get("pure_signal_hash")]
    summary["unique_pure_top_pool"] = _count_unique_pure(ok_rows)

    fields = list(pool_rows[0].keys()) if pool_rows else [
        "row_rank",
        "strategy",
        "source_row_index",
        "trades",
        "total_r",
        "profit_factor",
        "max_drawdown_r",
        "avg_bars_held",
        "candidate_score",
        "pure_signal_hash",
        "signal_detail_hash",
        "n_signals",
        "hash_group_rank",
        "is_unique_pure_signal_hash",
        "output_candidate_id_suggestion",
        "status",
        "error",
    ]
    with raw_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in pool_rows:
            w.writerow(r)

    # unique_signal_hash_candidates: best row per hash, plus up to top_per_signal_hash per hash
    by_hash: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in pool_rows:
        if r.get("status") != "ok" or not r.get("pure_signal_hash"):
            continue
        by_hash[str(r["pure_signal_hash"])].append(r)

    uniq_rows: list[dict[str, Any]] = []
    for h, lst in sorted(
        by_hash.items(), key=lambda x: (-max(float(r["candidate_score"]) for r in x[1]), x[0])
    ):
        lst_sorted = sorted(lst, key=lambda x: -float(x["candidate_score"]))
        for i, r in enumerate(lst_sorted[: int(top_per_signal_hash)], start=1):
            ur = dict(r)
            ur["hash_pick_rank"] = i
            ur["pure_signal_hash_key"] = h
            uniq_rows.append(ur)

    uniq_fields = list(uniq_rows[0].keys()) if uniq_rows else fields + [
        "hash_pick_rank",
        "pure_signal_hash_key",
    ]
    with uniq_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=uniq_fields, extrasaction="ignore")
        w.writeheader()
        for r in uniq_rows:
            w.writerow(r)

    with dup_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["pure_signal_hash", "n_rows_in_pool", "source_row_indices"],
        )
        w.writeheader()
        for h, lst in sorted(by_hash.items(), key=lambda x: (-len(x[1]), x[0])):
            if len(lst) < 2:
                continue
            w.writerow(
                {
                    "pure_signal_hash": h,
                    "n_rows_in_pool": len(lst),
                    "source_row_indices": json.dumps(
                        sorted(int(x["source_row_index"]) for x in lst)
                    ),
                }
            )

    lines = [
        f"# Raw sweep signal diversity — `{strategy}`",
        "",
        f"- **results_csv:** `{results_csv.as_posix()}`",
        f"- **strict eligible:** {summary['n_strict_eligible']}",
        f"- **unique pure_signal_hash (top 20 / 50 / 100):** {summary['unique_pure_top20']} / {summary['unique_pure_top50']} / {summary['unique_pure_top100']}",
        f"- **unique pure in top_pool ({min(top_pool, len(filt))}):** {summary['unique_pure_top_pool']}",
        "",
        "See CSV for per-row hashes.",
    ]
    raw_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--strategy", required=True)
    p.add_argument("--results-csv", type=Path, required=True)
    p.add_argument(
        "--base-config",
        type=Path,
        default=None,
        help="Optional YAML to use as merge base instead of load_strategy_config(strategy).",
    )
    p.add_argument("--asset", default="equity")
    p.add_argument("--symbol", default="QQQ")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--top-pool", type=int, default=100)
    p.add_argument("--filter-min-trades", type=int, default=30)
    p.add_argument("--filter-min-profit-factor", type=float, default=1.05)
    p.add_argument("--filter-min-total-r", type=float, default=0.0)
    p.add_argument("--filter-max-drawdown-r", type=float, default=-50.0)
    p.add_argument("--filter-max-avg-bars-held", type=float, default=120.0)
    p.add_argument("--top-per-signal-hash", type=int, default=3)
    args = p.parse_args(argv)

    results_csv = args.results_csv
    if not results_csv.is_absolute():
        results_csv = Path.cwd() / results_csv
    out = args.output_root
    if not out.is_absolute():
        out = Path.cwd() / out

    base_cfg: dict[str, Any] | None = None
    if args.base_config is not None:
        bp = args.base_config if args.base_config.is_absolute() else Path.cwd() / args.base_config
        base_cfg = yaml.safe_load(bp.read_text(encoding="utf-8"))
        if not isinstance(base_cfg, dict):
            print("ERROR base-config must be a YAML mapping", file=sys.stderr)
            return 2

    summary = run_audit(
        strategy=args.strategy,
        results_csv=results_csv,
        base_cfg=base_cfg,
        asset=args.asset,
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        output_root=out,
        top_pool=args.top_pool,
        filter_ns=_filter_ns(args),
        top_per_signal_hash=args.top_per_signal_hash,
    )
    print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
