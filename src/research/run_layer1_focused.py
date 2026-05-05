"""Generic Layer 1 orchestration: run sweep.py per strategy with *_focused.yaml grids."""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.backtest.sweep import validate_testing_grid_for_strategy
from src.strategies.loader import available_strategies, grid_size, load_testing_config, strategy_root

SWEEP_PY = _ROOT / "src" / "backtest" / "sweep.py"


def _safe_tag(tag: str) -> str:
    s = tag.strip().replace(" ", "_").replace("/", "_").replace("\\", "_")
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", s)


def _parse_summary_txt(path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip()
        if k in ("combinations_completed", "combinations_skipped_duplicate", "grid_size", "min_trades"):
            try:
                out[k] = int(v)
            except ValueError:
                out[k] = v
        elif k == "elapsed_sec":
            try:
                out[k] = float(v)
            except ValueError:
                out[k] = v
        else:
            out[k] = v
    return out


def _latest_tagged_sweep_folder(strategy: str, tag: str) -> Path | None:
    td = strategy_root() / "testing_parameters_results" / strategy
    if not td.is_dir():
        return None
    suf = _safe_tag(tag)
    pat = f"sweep_*_{suf}"
    matches = sorted(td.glob(pat), key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def _best_row_metrics(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {}
    sort_col = "profit_factor" if "profit_factor" in df.columns else None
    if sort_col:
        d = df.sort_values(sort_col, ascending=False, na_position="last").iloc[0]
    else:
        d = df.iloc[0]
    return {
        "best_profit_factor": float(d.get("profit_factor", float("nan")))
        if pd.notna(d.get("profit_factor"))
        else None,
        "best_total_r": float(d.get("total_r", float("nan"))) if pd.notna(d.get("total_r")) else None,
        "best_total_net_pnl": float(d.get("total_net_pnl", float("nan")))
        if pd.notna(d.get("total_net_pnl"))
        else None,
        "best_trades": int(d.get("trades", 0)) if pd.notna(d.get("trades")) else 0,
        "best_max_drawdown_r": float(d.get("max_drawdown_r", float("nan")))
        if pd.notna(d.get("max_drawdown_r"))
        else None,
        "best_avg_bars_held": float(d.get("avg_bars_held", float("nan")))
        if pd.notna(d.get("avg_bars_held"))
        else None,
        "best_max_hold_count": int(d.get("max_hold_count", 0)) if pd.notna(d.get("max_hold_count")) else 0,
        "best_eod_count": int(d.get("eod_count", 0)) if pd.notna(d.get("eod_count")) else 0,
        "best_end_of_data_count": int(d.get("end_of_data_count", 0))
        if pd.notna(d.get("end_of_data_count"))
        else 0,
    }


MANIFEST_FIELDS = [
    "strategy",
    "status",
    "sweep_folder",
    "results_csv",
    "summary_txt",
    "testing_config_used",
    "grid_size",
    "combinations_completed",
    "combinations_skipped_duplicate",
    "elapsed_sec",
    "result_rows",
    "best_profit_factor",
    "best_total_r",
    "best_total_net_pnl",
    "best_trades",
    "best_max_drawdown_r",
    "best_avg_bars_held",
    "best_max_hold_count",
    "best_eod_count",
    "best_end_of_data_count",
    "notes",
]


def _read_manifest(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    out: dict[str, dict[str, Any]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            s = row.get("strategy", "").strip()
            if s:
                out[s] = row
    return out


def _write_manifest_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in MANIFEST_FIELDS})


def _write_manifest_md(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Layer 1 sweep manifest",
        "",
        "| strategy | status | elapsed_sec | result_rows | best_pf | best_total_r | sweep_folder |",
        "|----------|--------|-------------|-------------|---------|--------------|--------------|",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('strategy','')} | {row.get('status','')} | {row.get('elapsed_sec','')} | "
            f"{row.get('result_rows','')} | {row.get('best_profit_factor','')} | "
            f"{row.get('best_total_r','')} | {Path(str(row.get('sweep_folder',''))).name} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _manifest_list(by_str: dict[str, dict[str, Any]], priority_order: list[str]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for s in priority_order:
        if s in by_str and s not in seen:
            out.append(by_str[s])
            seen.add(s)
    for s in sorted(by_str.keys()):
        if s not in seen:
            out.append(by_str[s])
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run Layer 1 focused sweeps for multiple strategies.")
    p.add_argument("--asset", default="equity")
    p.add_argument("--symbols", nargs="+", default=["QQQ"])
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument(
        "--strategies",
        default="all",
        help='Comma-separated names or "all" for loader.available_strategies().',
    )
    p.add_argument("--tag", required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--top", type=int, default=50)
    p.add_argument("--min-trades", type=int, default=30)
    p.add_argument("--progress-every", type=int, default=50)
    p.add_argument("--resume", action="store_true")
    args = p.parse_args(argv)

    out_root = args.output_root
    if not out_root.is_absolute():
        out_root = Path.cwd() / out_root
    out_root.mkdir(parents=True, exist_ok=True)
    manifest_csv = out_root / "sweep_manifest.csv"
    manifest_md = out_root / "sweep_manifest.md"

    if args.strategies.strip().lower() == "all":
        strat_list = available_strategies()
    else:
        strat_list = [s.strip() for s in args.strategies.split(",") if s.strip()]

    if not args.resume:
        if manifest_csv.is_file():
            manifest_csv.unlink()
        if manifest_md.is_file():
            manifest_md.unlink()
    manifest_by = _read_manifest(manifest_csv) if args.resume else {}
    priority_order = list(strat_list)
    sym_args = [str(x).upper() for x in args.symbols]

    for strategy in strat_list:
        focused = strategy_root() / "testing_parameters" / f"{strategy}_focused.yaml"
        if not focused.is_file():
            row = {
                "strategy": strategy,
                "status": "missing_focused_yaml",
                "sweep_folder": "",
                "results_csv": "",
                "summary_txt": "",
                "testing_config_used": str(focused),
                "grid_size": "",
                "combinations_completed": "",
                "combinations_skipped_duplicate": "",
                "elapsed_sec": "",
                "result_rows": "",
                "best_profit_factor": "",
                "best_total_r": "",
                "best_total_net_pnl": "",
                "best_trades": "",
                "best_max_drawdown_r": "",
                "best_avg_bars_held": "",
                "best_max_hold_count": "",
                "best_eod_count": "",
                "best_end_of_data_count": "",
                "notes": "no focused yaml",
            }
            manifest_by[strategy] = row
            rows = _manifest_list(manifest_by, priority_order)
            _write_manifest_csv(manifest_csv, rows)
            _write_manifest_md(manifest_md, rows)
            print(f"[SKIP] {strategy} missing {focused}", flush=True)
            continue

        if args.resume:
            prev = manifest_by.get(strategy)
            if prev and str(prev.get("status", "")).strip() == "ok":
                rc_path = Path(str(prev.get("results_csv", "")))
                if rc_path.is_file():
                    print(f"[SKIP] strategy={strategy} already completed manifest ok + results exist", flush=True)
                    continue

        try:
            testing = load_testing_config(strategy)
            gs = grid_size(testing) if testing else ""
        except Exception:
            gs = ""

        try:
            with focused.open(encoding="utf-8") as f:
                testing_doc = yaml.safe_load(f)
            if not isinstance(testing_doc, dict) or testing_doc.get("strategy") != strategy:
                raise ValueError(f"testing YAML strategy mismatch in {focused}")
            validate_testing_grid_for_strategy(strategy, testing_doc)
        except Exception as e:
            print(f"[ERROR] {strategy} grid validation failed: {e}", flush=True)
            row = {
                "strategy": strategy,
                "status": "grid_validation_failed",
                "sweep_folder": "",
                "results_csv": "",
                "summary_txt": "",
                "testing_config_used": str(focused),
                "grid_size": gs,
                "combinations_completed": "",
                "combinations_skipped_duplicate": "",
                "elapsed_sec": "",
                "result_rows": "",
                "best_profit_factor": "",
                "best_total_r": "",
                "best_total_net_pnl": "",
                "best_trades": "",
                "best_max_drawdown_r": "",
                "best_avg_bars_held": "",
                "best_max_hold_count": "",
                "best_eod_count": "",
                "best_end_of_data_count": "",
                "notes": str(e),
            }
            manifest_by[strategy] = row
            rows = _manifest_list(manifest_by, priority_order)
            _write_manifest_csv(manifest_csv, rows)
            _write_manifest_md(manifest_md, rows)
            continue

        cmd = [
            sys.executable,
            str(SWEEP_PY),
            "--strategy",
            strategy,
            "--testing-config",
            str(focused.resolve()),
            "--asset",
            args.asset,
            "--symbols",
            *sym_args,
            "--start",
            args.start,
            "--end",
            args.end,
            "--top",
            str(args.top),
            "--min-trades",
            str(args.min_trades),
            "--profile",
            "--tag",
            args.tag,
            "--progress-every",
            str(args.progress_every),
        ]

        print("=" * 60, flush=True)
        print(f"[LAYER1] strategy={strategy} start...", flush=True)
        print(f"[CMD] {' '.join(cmd)}", flush=True)
        print("=" * 60, flush=True)

        t0 = time.perf_counter()
        proc = subprocess.Popen(
            cmd,
            cwd=str(_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="", flush=True)
        code = proc.wait()
        elapsed = time.perf_counter() - t0

        sweep_dir = _latest_tagged_sweep_folder(strategy, args.tag)
        results_csv = sweep_dir / "results.csv" if sweep_dir else Path("")
        summary_txt = sweep_dir / "summary.txt" if sweep_dir else Path("")
        summ = _parse_summary_txt(summary_txt) if summary_txt.is_file() else {}

        notes = ""
        result_rows = 0
        best: dict[str, Any] = {}
        if code == 0 and results_csv.is_file():
            df = pd.read_csv(results_csv)
            result_rows = len(df)
            best = _best_row_metrics(df)
            if result_rows == 0:
                notes = "no_candidates_or_no_rows"
        elif code != 0:
            notes = f"subprocess_exit_{code}"

        row = {
            "strategy": strategy,
            "status": "ok" if code == 0 else f"exit_{code}",
            "sweep_folder": str(sweep_dir.resolve()) if sweep_dir else "",
            "results_csv": str(results_csv.resolve()) if results_csv.is_file() else "",
            "summary_txt": str(summary_txt.resolve()) if summary_txt.is_file() else "",
            "testing_config_used": str(focused.resolve()),
            "grid_size": gs,
            "combinations_completed": summ.get("combinations_completed", ""),
            "combinations_skipped_duplicate": summ.get("combinations_skipped_duplicate", ""),
            "elapsed_sec": round(elapsed, 3),
            "result_rows": result_rows,
            "best_profit_factor": best.get("best_profit_factor", ""),
            "best_total_r": best.get("best_total_r", ""),
            "best_total_net_pnl": best.get("best_total_net_pnl", ""),
            "best_trades": best.get("best_trades", ""),
            "best_max_drawdown_r": best.get("best_max_drawdown_r", ""),
            "best_avg_bars_held": best.get("best_avg_bars_held", ""),
            "best_max_hold_count": best.get("best_max_hold_count", ""),
            "best_eod_count": best.get("best_eod_count", ""),
            "best_end_of_data_count": best.get("best_end_of_data_count", ""),
            "notes": notes,
        }
        manifest_by[strategy] = row
        rows = _manifest_list(manifest_by, priority_order)
        _write_manifest_csv(manifest_csv, rows)
        _write_manifest_md(manifest_md, rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
