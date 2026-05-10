"""Layer 1: select top candidates from sweep results.csv into YAML library."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.research.scoring import candidate_score, passes_filters, safe_float
from src.strategies.loader import set_nested
from src.strategies.metadata import get_strategy_metadata

PREFIXES = ("features.", "signal.", "risk.", "backtest.")


def _strategy_slug_upper(strategy: str) -> str:
    return strategy.upper().replace("-", "_")


def strategy_metadata(strategy: str) -> dict[str, Any]:
    m = get_strategy_metadata(strategy)
    return {
        "strategy_family": m.get("family", "unknown"),
        "default_priority": int(m.get("default_priority", 50)),
        "default_active_start_minute": int(m.get("default_active_start_minute", 0)),
        "default_active_end_minute": int(m.get("default_active_end_minute", 389)),
        "conflict_group": str(m.get("conflict_group", "QQQ_directional")),
    }


def _parse_cell_value(v: Any) -> Any:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, str):
        s = v.strip()
        if (s.startswith("[") and s.endswith("]")) or (s.startswith("(") and s.endswith(")")):
            try:
                return json.loads(s.replace("(", "[").replace(")", "]"))
            except json.JSONDecodeError:
                pass
    return v


def unflatten_config_from_row(row: pd.Series) -> dict[str, Any]:
    """Build nested config from results.csv dotted columns; fall back to params_json."""
    out: dict[str, Any] = {}
    for col, val in row.items():
        if not isinstance(col, str):
            continue
        for prefix, section in (
            ("features.", "features"),
            ("signal.", "signal"),
            ("risk.", "risk"),
            ("backtest.", "backtest"),
        ):
            if col.startswith(prefix):
                key = col[len(prefix) :]
                v = _parse_cell_value(val)
                if key and v is not None and not (isinstance(v, float) and pd.isna(v)):
                    set_nested(out.setdefault(section, {}), key, v)
                break
    pj = row.get("params_json")
    if isinstance(pj, str) and pj.strip():
        try:
            flat = json.loads(pj)
            if isinstance(flat, dict):
                for k, v in flat.items():
                    if not isinstance(k, str):
                        continue
                    for prefix, section in (
                        ("features.", "features"),
                        ("signal.", "signal"),
                        ("risk.", "risk"),
                        ("backtest.", "backtest"),
                    ):
                        if k.startswith(prefix):
                            key = k[len(prefix) :]
                            vv = _parse_cell_value(v)
                            if key and vv is not None:
                                set_nested(out.setdefault(section, {}), key, vv)
                            break
        except json.JSONDecodeError:
            pass
    return out


def params_hash_from_config(config: dict[str, Any]) -> str:
    blob = json.dumps(config, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:12]


def resolve_results_csv(glob_or_path: str, *, cwd: Path) -> Path:
    """Resolve a concrete results.csv path; if pattern contains glob chars, use cwd-relative glob."""
    if "*" in glob_or_path or "?" in glob_or_path:
        matches = sorted(cwd.glob(glob_or_path.replace("\\", "/")))
        if not matches:
            raise FileNotFoundError(f"no match for {glob_or_path!r} (cwd={cwd})")
        return matches[-1]
    p = Path(glob_or_path)
    if not p.is_absolute():
        p = cwd / p
    if not p.is_file():
        raise FileNotFoundError(f"not a file: {p}")
    return p


def _validate_results_df(df: pd.DataFrame, *, path: Path) -> None:
    need = [
        "strategy",
        "symbol",
        "trades",
        "profit_factor",
        "total_r",
        "max_drawdown_r",
        "params_json",
    ]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise ValueError(f"{path}: missing columns {miss}")


def _candidate_id(strategy: str, rank: int) -> str:
    return f"{_strategy_slug_upper(strategy)}_{rank:03d}"


def _emit_yaml_and_rows(
    *,
    strategy: str,
    csv_path: Path,
    df: pd.DataFrame,
    filt: pd.DataFrame,
    top_k: int,
    args_sort: str,
    args_ascending: bool,
    sel_dir: Path,
    filters_used: str,
    warning: str | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    meta = strategy_metadata(strategy)
    filt = filt.copy()
    filt["_candidate_score"] = filt.apply(candidate_score, axis=1)
    sort_col = args_sort if args_sort != "candidate_score" else "_candidate_score"
    if sort_col == "_candidate_score":
        filt = filt.sort_values("_candidate_score", ascending=args_ascending)
    elif sort_col == "profit_factor":
        filt = filt.sort_values(
            "profit_factor",
            ascending=args_ascending,
            key=lambda s: s.astype(float).replace(float("inf"), 1e308),
        )
    else:
        filt = filt.sort_values(sort_col, ascending=args_ascending)

    top = filt.head(int(top_k))
    all_rows: list[dict[str, Any]] = []
    summary_lines: list[str] = []
    for rank, (idx, row) in enumerate(top.iterrows(), start=1):
        cid = _candidate_id(strategy, rank)
        cfg = unflatten_config_from_row(row)
        if not cfg.get("strategy"):
            cfg = {"strategy": strategy, **cfg} if strategy else cfg
        ph = params_hash_from_config(cfg)
        score_v = float(row["_candidate_score"])

        yaml_body: dict[str, Any] = {
            "candidate_id": cid,
            "strategy": strategy,
            "asset": str(row.get("asset", "equity")),
            "symbol": str(row.get("symbol", "")),
            "strategy_family": meta["strategy_family"],
            "conflict_group": meta.get("conflict_group", "QQQ_directional"),
            "default_priority": int(meta["default_priority"]),
            "default_active_start_minute": int(meta["default_active_start_minute"]),
            "default_active_end_minute": int(meta["default_active_end_minute"]),
            "metadata": {
                "family": meta["strategy_family"],
                "conflict_group": str(meta.get("conflict_group", "QQQ_directional")),
                "default_priority": int(meta["default_priority"]),
                "default_active_start_minute": int(meta["default_active_start_minute"]),
                "default_active_end_minute": int(meta["default_active_end_minute"]),
            },
            "selection": {
                "score": score_v,
                "filters_used": filters_used,
                "warning": warning or "",
            },
            "source": {
                "results_csv": str(csv_path.resolve()),
                "row_index": int(row["__source_row__"]),
                "sweep_folder": str(csv_path.parent.resolve()),
            },
            "metrics": {
                "trades": int(safe_float(row.get("trades"), 0)),
                "profit_factor": safe_float(row.get("profit_factor")),
                "total_r": safe_float(row.get("total_r")),
                "win_rate": safe_float(row.get("win_rate")),
                "total_net_pnl": safe_float(row.get("total_net_pnl")),
                "avg_r": safe_float(row.get("avg_r")),
                "avg_net_pnl": safe_float(row.get("avg_net_pnl")),
                "max_drawdown_pnl": safe_float(row.get("max_drawdown_pnl")),
                "max_drawdown_r": safe_float(row.get("max_drawdown_r")),
                "avg_bars_held": safe_float(row.get("avg_bars_held")),
                "stop_count": int(safe_float(row.get("stop_count"), 0)),
                "target_count": int(safe_float(row.get("target_count"), 0)),
                "eod_count": int(safe_float(row.get("eod_count"), 0)),
                "end_of_data_count": int(safe_float(row.get("end_of_data_count"), 0)),
                "max_hold_count": int(safe_float(row.get("max_hold_count"), 0)),
            },
            "config": cfg,
        }
        ypath = sel_dir / f"{cid}.yaml"
        with ypath.open("w", encoding="utf-8") as f:
            yaml.safe_dump(yaml_body, f, sort_keys=False, default_flow_style=False)

        rel_yaml = f"selected_candidates/{cid}.yaml"
        src_ix = int(row["__source_row__"])
        all_rows.append(
            {
                "candidate_id": cid,
                "strategy": strategy,
                "symbol": str(row.get("symbol", "")),
                "asset": str(row.get("asset", "equity")),
                "source_results_csv": str(csv_path.resolve()),
                "source_row_index": src_ix,
                "source_sweep_folder": str(csv_path.parent.resolve()),
                "candidate_rank": rank,
                "candidate_score": score_v,
                "strategy_family": meta["strategy_family"],
                "default_priority": meta["default_priority"],
                "default_active_start_minute": meta["default_active_start_minute"],
                "default_active_end_minute": meta["default_active_end_minute"],
                "params_hash": ph,
                "params_json": row.get("params_json", ""),
                "config_yaml": rel_yaml,
                "filters_used": filters_used,
                "warning": warning or "",
                "trades": int(safe_float(row.get("trades"), 0)),
                "win_rate": safe_float(row.get("win_rate")),
                "total_net_pnl": safe_float(row.get("total_net_pnl")),
                "total_r": safe_float(row.get("total_r")),
                "avg_r": safe_float(row.get("avg_r")),
                "profit_factor": safe_float(row.get("profit_factor")),
                "max_drawdown_pnl": safe_float(row.get("max_drawdown_pnl")),
                "max_drawdown_r": safe_float(row.get("max_drawdown_r")),
                "avg_bars_held": safe_float(row.get("avg_bars_held")),
                "stop_count": int(safe_float(row.get("stop_count"), 0)),
                "target_count": int(safe_float(row.get("target_count"), 0)),
                "eod_count": int(safe_float(row.get("eod_count"), 0)),
                "end_of_data_count": int(safe_float(row.get("end_of_data_count"), 0)),
                "max_hold_count": int(safe_float(row.get("max_hold_count"), 0)),
            }
        )
        summary_lines.append(
            f"  {cid} {strategy} score={score_v:.4f} trades={int(safe_float(row.get('trades'), 0))} "
            f"pf={safe_float(row.get('profit_factor'))} warn={warning or ''}"
        )
    return all_rows, summary_lines


def _main_manifest(
    args: argparse.Namespace,
    *,
    cwd: Path,
    out_dir: Path,
    sel_dir: Path,
    top_k: int,
) -> int:
    man_path = args.manifest
    assert man_path is not None
    if not man_path.is_absolute():
        man_path = cwd / man_path
    mf = pd.read_csv(man_path)
    all_rows: list[dict[str, Any]] = []
    cand_lines = [
        "# Layer 1 candidate summary (manifest)",
        "",
        "Interpretation: in-sample sweep rankings only; not live-ready.",
        "",
    ]
    strict_ns = argparse.Namespace(
        min_trades=int(args.min_trades),
        min_profit_factor=args.min_profit_factor,
        min_total_r=args.min_total_r,
        max_drawdown_r=args.max_drawdown_r,
        max_avg_bars_held=args.max_avg_bars_held,
        max_eod_count=args.max_eod_count,
        max_end_of_data_count=args.max_end_of_data_count,
        max_max_hold_count=args.max_max_hold_count,
    )
    relaxed_max_abh = (
        float(args.relaxed_max_avg_bars_held)
        if getattr(args, "relaxed_max_avg_bars_held", None) is not None
        else args.max_avg_bars_held
    )
    relaxed_ns = argparse.Namespace(
        min_trades=int(args.relaxed_min_trades),
        min_profit_factor=float(args.relaxed_min_profit_factor),
        min_total_r=float(args.relaxed_min_total_r),
        max_drawdown_r=float(args.relaxed_max_drawdown_r),
        max_avg_bars_held=relaxed_max_abh,
        max_eod_count=args.max_eod_count,
        max_end_of_data_count=args.max_end_of_data_count,
        max_max_hold_count=args.max_max_hold_count,
    )

    for _, mrow in mf.iterrows():
        strategy = str(mrow.get("strategy", "")).strip()
        status = str(mrow.get("status", "")).strip()
        rcsv = str(mrow.get("results_csv", "")).strip()
        if status not in ("ok", "ok_zero_trade"):
            cand_lines.append(f"- **{strategy}**: skipped (status={status})")
            continue
        csv_path = Path(rcsv)
        if not csv_path.is_file():
            cand_lines.append(f"- **{strategy}**: missing results_csv `{rcsv}`")
            continue
        df = pd.read_csv(csv_path)
        try:
            _validate_results_df(df, path=csv_path)
        except ValueError as e:
            cand_lines.append(f"- **{strategy}**: invalid CSV ({e})")
            continue
        df.insert(0, "__source_row__", range(len(df)))
        df = df[df["strategy"].astype(str) == strategy].copy()
        if df.empty:
            cand_lines.append(f"- **{strategy}**: no rows for this strategy in CSV")
            continue

        filt = df[df.apply(lambda r: passes_filters(r, strict_ns), axis=1)].copy()
        warn: str | None = None
        fu = "strict"
        if filt.empty and args.allow_relaxed_fallback:
            filt = df[df.apply(lambda r: passes_filters(r, relaxed_ns), axis=1)].copy()
            if not filt.empty:
                warn = "relaxed_filter"
                fu = "relaxed"
        if filt.empty:
            cand_lines.append(f"- **{strategy}**: no candidates passing filters (strict or relaxed)")
            continue

        chunk, slog = _emit_yaml_and_rows(
            strategy=strategy,
            csv_path=csv_path,
            df=df,
            filt=filt,
            top_k=top_k,
            args_sort=args.sort_by,
            args_ascending=args.ascending,
            sel_dir=sel_dir,
            filters_used=fu,
            warning=warn,
        )
        all_rows.extend(chunk)
        cand_lines.append(f"### {strategy}")
        cand_lines.extend(slog)
        cand_lines.append("")

    out_csv = out_dir / "selected_candidates.csv"
    pd.DataFrame(all_rows).to_csv(out_csv, index=False)
    (out_dir / "candidate_summary.md").write_text("\n".join(cand_lines) + "\n", encoding="utf-8")

    summary_lines = [
        f"tag={args.tag or ''}",
        f"out_dir={out_dir.resolve()}",
        f"candidates_written={len(all_rows)}",
        "",
        "candidates:",
    ]
    for r in all_rows:
        summary_lines.append(
            f"  {r['candidate_id']} {r['strategy']} score={r['candidate_score']:.4f} trades={r['trades']}"
        )
    (out_dir / "summary.txt").write_text("\n".join(summary_lines), encoding="utf-8")

    print(f"Wrote {out_csv}", flush=True)
    print(f"Wrote {out_dir / 'candidate_summary.md'}", flush=True)
    print(f"Wrote {len(all_rows)} YAML files under {sel_dir}", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Select Layer 1 candidates from sweep results.")
    p.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="sweep_manifest.csv from run_layer1_focused (alternative to --result)",
    )
    p.add_argument(
        "--result",
        action="append",
        default=None,
        metavar="STRATEGY=PATH_OR_GLOB",
        help="Repeatable: strategy_name=glob or path to results.csv",
    )
    p.add_argument("--top-k", type=int, default=3)
    p.add_argument("--top-per-strategy", type=int, default=None, help="Alias for --top-k in manifest mode.")
    p.add_argument("--min-trades", type=int, default=0)
    p.add_argument("--min-profit-factor", type=float, default=None)
    p.add_argument("--min-total-r", type=float, default=None)
    p.add_argument("--max-drawdown-r", type=float, default=None)
    p.add_argument("--max-avg-bars-held", type=float, default=None)
    p.add_argument("--max-eod-count", type=int, default=None)
    p.add_argument("--max-end-of-data-count", type=int, default=None)
    p.add_argument("--max-max-hold-count", type=int, default=None)
    p.add_argument("--sort-by", default="candidate_score", choices=("candidate_score", "profit_factor", "total_r"))
    p.add_argument("--ascending", action="store_true")
    p.add_argument("--out-dir", type=str, default=None)
    p.add_argument("--output-root", type=str, default=None, metavar="PATH", help="Alias for --out-dir.")
    p.add_argument("--tag", default="")
    p.add_argument(
        "--allow-relaxed-fallback",
        action="store_true",
        help="If strict filters yield no rows, retry with relaxed thresholds (manifest mode).",
    )
    p.add_argument(
        "--relaxed-min-trades",
        type=int,
        default=80,
        help="Manifest relaxed fallback: min trades (default 80).",
    )
    p.add_argument(
        "--relaxed-min-profit-factor",
        type=float,
        default=1.0,
        help="Manifest relaxed fallback: min profit factor (default 1.0).",
    )
    p.add_argument(
        "--relaxed-min-total-r",
        type=float,
        default=-10.0,
        help="Manifest relaxed fallback: min total R (default -10).",
    )
    p.add_argument(
        "--relaxed-max-drawdown-r",
        type=float,
        default=-100.0,
        help="Manifest relaxed fallback: max drawdown R floor (default -100).",
    )
    p.add_argument(
        "--relaxed-max-avg-bars-held",
        type=float,
        default=None,
        help="Manifest relaxed fallback: max avg bars held (default: same as strict --max-avg-bars-held).",
    )
    args = p.parse_args(argv)

    cwd = Path.cwd()
    out_raw = args.output_root or args.out_dir
    if not out_raw:
        print("ERROR need --out-dir or --output-root", file=sys.stderr)
        return 2
    out_dir = Path(out_raw)
    if not out_dir.is_absolute():
        out_dir = cwd / out_dir
    sel_dir = out_dir / "selected_candidates"
    sel_dir.mkdir(parents=True, exist_ok=True)

    top_k = int(args.top_per_strategy or args.top_k)

    if args.manifest:
        return _main_manifest(args, cwd=cwd, out_dir=out_dir, sel_dir=sel_dir, top_k=top_k)

    if not args.result:
        print("ERROR need --result STRATEGY=path or --manifest", file=sys.stderr)
        return 2

    all_rows: list[dict[str, Any]] = []

    for spec in args.result:
        if "=" not in spec:
            print(f"ERROR bad --result {spec!r}, want strategy=path", file=sys.stderr)
            return 2
        strategy, path_glob = spec.split("=", 1)
        strategy = strategy.strip()
        path_glob = path_glob.strip()
        csv_path = resolve_results_csv(path_glob, cwd=cwd)
        df = pd.read_csv(csv_path)
        _validate_results_df(df, path=csv_path)
        df.insert(0, "__source_row__", range(len(df)))
        df = df[df["strategy"].astype(str) == strategy].copy()
        filt = df[df.apply(lambda r: passes_filters(r, args), axis=1)].copy()
        chunk, _ = _emit_yaml_and_rows(
            strategy=strategy,
            csv_path=csv_path,
            df=df,
            filt=filt,
            top_k=top_k,
            args_sort=args.sort_by,
            args_ascending=args.ascending,
            sel_dir=sel_dir,
            filters_used="cli",
            warning=None,
        )
        all_rows.extend(chunk)

    out_csv = out_dir / "selected_candidates.csv"
    pd.DataFrame(all_rows).to_csv(out_csv, index=False)

    summary_lines = [
        f"tag={args.tag or ''}",
        f"out_dir={out_dir.resolve()}",
        f"candidates_written={len(all_rows)}",
        "",
        "candidates:",
    ]
    for r in all_rows:
        summary_lines.append(f"  {r['candidate_id']} {r['strategy']} score={r['candidate_score']:.4f} trades={r['trades']}")

    (out_dir / "summary.txt").write_text("\n".join(summary_lines), encoding="utf-8")

    print(f"Wrote {out_csv}", flush=True)
    print(f"Wrote {len(all_rows)} YAML files under {sel_dir}", flush=True)
    for r in all_rows:
        print(f"  {r['candidate_id']} strategy={r['strategy']} score={r['candidate_score']:.4f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
