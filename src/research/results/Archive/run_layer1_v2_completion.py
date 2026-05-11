"""Layer 1 sweeps for Strategy Library v2 completion strategies (QQQ, manifest + caps)."""

from __future__ import annotations

import argparse
import csv
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
from src.research.run_layer1_focused import (
    _best_row_metrics,
    _latest_tagged_sweep_folder,
    _parse_summary_txt,
)
from src.strategies.loader import (
    grid_size,
    load_strategy,
    load_strategy_config,
    strategy_root,
)

SWEEP_PY = _ROOT / "src" / "backtest" / "sweep.py"
SELECT_PY = _ROOT / "src" / "research" / "select_candidates.py"

COMPLETION_STRATEGIES: tuple[str, ...] = (
    "sma20_reclaim_reject",
    "macd_momentum_turn",
    "stochastic_oversold_cross",
    "cci_extreme_snapback",
    "adx_dmi_trend_continuation",
    "supertrend_atr_flip",
    "large_candle_failure",
    "multi_day_level_trap",
    "prior_close_reclaim",
)


def grid_cap_policy(raw_grid_size: int) -> tuple[bool, int | None, str]:
    """Return (capped, max_combos_or_none, reason)."""
    if raw_grid_size <= 1500:
        return False, None, "full_grid_raw_le_1500"
    if raw_grid_size <= 5000:
        return True, 750, "cap_750_raw_gt_1500"
    return True, 500, "cap_500_raw_gt_5000"


def recommend_max_combos(raw_grid_size: int) -> int | None:
    capped, mx, _ = grid_cap_policy(raw_grid_size)
    return mx if capped else None


MANIFEST_FIELDS = [
    "strategy",
    "status",
    "elapsed_sec",
    "raw_grid_size",
    "capped",
    "max_combos",
    "result_rows",
    "best_trades",
    "best_total_r",
    "best_profit_factor",
    "best_profit_factor_r",
    "best_max_drawdown_r",
    "best_avg_bars_held",
    "best_eod_count",
    "best_end_of_data_count",
    "sweep_folder",
    "results_csv",
    "warning",
]


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def _md_table(title: str, rows: list[dict[str, Any]], cols: list[str]) -> str:
    lines = [title, ""]
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join("---" for _ in cols) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(c, "")) for c in cols) + " |")
    return "\n".join(lines) + "\n"


def run_preflight(strategies: list[str], out_dir: Path) -> list[dict[str, Any]]:
    from src.strategies.metadata import get_strategy_metadata

    rows: list[dict[str, Any]] = []
    for strategy in strategies:
        row: dict[str, Any] = {k: "" for k in (
            "strategy",
            "loader_ok",
            "parameters_yaml_exists",
            "focused_yaml_exists",
            "metadata_ok",
            "supports_fast",
            "required_features_no_lookahead",
            "default_config_valid",
            "focused_config_valid",
            "warning",
        )}
        row["strategy"] = strategy
        warn: list[str] = []
        try:
            strat = load_strategy(strategy)
            row["loader_ok"] = "yes"
        except Exception as e:
            row["loader_ok"] = "no"
            row["warning"] = f"load_strategy:{e}"
            rows.append(row)
            continue

        p_yaml = strategy_root() / "parameters" / f"{strategy}.yaml"
        f_yaml = strategy_root() / "testing_parameters" / f"{strategy}_focused.yaml"
        row["parameters_yaml_exists"] = "yes" if p_yaml.is_file() else "no"
        row["focused_yaml_exists"] = "yes" if f_yaml.is_file() else "no"

        try:
            meta = get_strategy_metadata(strategy)
            row["metadata_ok"] = "yes" if meta else "no"
        except Exception:
            row["metadata_ok"] = "no"

        row["supports_fast"] = "yes" if getattr(strat, "supports_fast", False) else "no"
        req = list(getattr(strat, "required_features", lambda: [])())
        bad = [c for c in req if "LOOKAHEAD" in str(c)]
        row["required_features_no_lookahead"] = "yes" if not bad else "no"
        if bad:
            warn.append(f"lookahead_in_required:{bad}")

        try:
            base = load_strategy_config(strategy)
            strat.validate_config(base)
            row["default_config_valid"] = "yes"
        except Exception as e:
            row["default_config_valid"] = "no"
            warn.append(f"default_cfg:{e}")

        row["focused_config_valid"] = "no"
        if f_yaml.is_file():
            try:
                with f_yaml.open(encoding="utf-8") as fh:
                    doc = yaml.safe_load(fh)
                if isinstance(doc, dict) and doc.get("strategy") == strategy:
                    validate_testing_grid_for_strategy(strategy, doc)
                    row["focused_config_valid"] = "yes"
                else:
                    warn.append("focused_yaml_strategy_mismatch")
            except Exception as e:
                warn.append(f"focused_grid:{e}")

        if row["supports_fast"] == "no":
            warn.append("supports_fast_false")
        row["warning"] = "; ".join(warn)
        rows.append(row)
    return rows


def run_grid_review(strategies: list[str], out_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for strategy in strategies:
        f_yaml = strategy_root() / "testing_parameters" / f"{strategy}_focused.yaml"
        raw_sz = 0
        if f_yaml.is_file():
            with f_yaml.open(encoding="utf-8") as fh:
                doc = yaml.safe_load(fh)
            if isinstance(doc, dict):
                raw_sz = grid_size(doc)
        capped, max_c, reason = grid_cap_policy(raw_sz)
        rec = max_c if capped else raw_sz
        rows.append(
            {
                "strategy": strategy,
                "focused_yaml": str(f_yaml.relative_to(_ROOT)) if f_yaml.is_file() else "",
                "raw_grid_size": raw_sz,
                "recommended_max_combos": rec if capped else raw_sz,
                "capped": "yes" if capped else "no",
                "reason": reason,
                "notes": "" if capped else "run_full_grid",
            }
        )
    return rows


def _write_manifest(out_dir: Path, rows: list[dict[str, Any]]) -> None:
    _write_csv(out_dir / "sweep_manifest.csv", rows, MANIFEST_FIELDS)
    cols = [
        "strategy",
        "status",
        "elapsed_sec",
        "raw_grid_size",
        "capped",
        "max_combos",
        "result_rows",
        "best_trades",
        "best_total_r",
        "best_profit_factor",
        "warning",
    ]
    (out_dir / "sweep_manifest.md").write_text(_md_table("# Layer 1 v2 completion — sweep manifest", rows, cols), encoding="utf-8")


def run_sweeps(
    *,
    strategies: list[str],
    out_dir: Path,
    asset: str,
    symbol: str,
    start: str,
    end: str,
    tag: str,
    top: int,
    min_trades: int,
    progress_every: int,
    grid_by_strategy: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    sym = symbol.upper().strip()
    manifest_rows: list[dict[str, Any]] = []
    for strategy in strategies:
        ginfo = grid_by_strategy.get(strategy, {})
        raw_sz = int(ginfo.get("raw_grid_size", 0))
        capped = str(ginfo.get("capped", "no")) == "yes"
        max_combos: int | None = None
        if capped:
            mc = ginfo.get("recommended_max_combos")
            max_combos = int(mc) if mc is not None else recommend_max_combos(raw_sz)

        focused = strategy_root() / "testing_parameters" / f"{strategy}_focused.yaml"
        warning_parts: list[str] = []

        if not focused.is_file():
            manifest_rows.append(
                {
                    "strategy": strategy,
                    "status": "missing_focused_yaml",
                    "elapsed_sec": "",
                    "raw_grid_size": raw_sz,
                    "capped": "yes" if capped else "no",
                    "max_combos": max_combos if max_combos is not None else "",
                    "result_rows": 0,
                    "best_trades": "",
                    "best_total_r": "",
                    "best_profit_factor": "",
                    "best_profit_factor_r": "",
                    "best_max_drawdown_r": "",
                    "best_avg_bars_held": "",
                    "best_eod_count": "",
                    "best_end_of_data_count": "",
                    "sweep_folder": "",
                    "results_csv": "",
                    "warning": "missing_focused_yaml",
                }
            )
            _write_manifest(out_dir, manifest_rows)
            continue

        try:
            with focused.open(encoding="utf-8") as f:
                testing_doc = yaml.safe_load(f)
            if not isinstance(testing_doc, dict) or testing_doc.get("strategy") != strategy:
                raise ValueError("strategy field mismatch")
            validate_testing_grid_for_strategy(strategy, testing_doc)
        except Exception as e:
            manifest_rows.append(
                {
                    "strategy": strategy,
                    "status": "grid_validation_failed",
                    "elapsed_sec": "",
                    "raw_grid_size": raw_sz,
                    "capped": "yes" if capped else "no",
                    "max_combos": max_combos if max_combos is not None else "",
                    "result_rows": 0,
                    "best_trades": "",
                    "best_total_r": "",
                    "best_profit_factor": "",
                    "best_profit_factor_r": "",
                    "best_max_drawdown_r": "",
                    "best_avg_bars_held": "",
                    "best_eod_count": "",
                    "best_end_of_data_count": "",
                    "sweep_folder": "",
                    "results_csv": "",
                    "warning": str(e),
                }
            )
            _write_manifest(out_dir, manifest_rows)
            continue

        cmd = [
            sys.executable,
            str(SWEEP_PY),
            "--strategy",
            strategy,
            "--testing-config",
            str(focused.resolve()),
            "--asset",
            asset,
            "--symbols",
            sym,
            "--start",
            start,
            "--end",
            end,
            "--top",
            str(top),
            "--min-trades",
            str(min_trades),
            "--profile",
            "--tag",
            tag,
            "--progress-every",
            str(progress_every),
        ]
        if max_combos is not None:
            cmd.extend(["--max-combos", str(max_combos)])

        print("=" * 72, flush=True)
        print(f"[v2_completion] strategy={strategy} raw_grid={raw_sz} capped={capped} max_combos={max_combos}", flush=True)
        print(f"[CMD] {' '.join(cmd)}", flush=True)
        print("=" * 72, flush=True)

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

        sweep_dir = _latest_tagged_sweep_folder(strategy, tag)
        results_csv = sweep_dir / "results.csv" if sweep_dir else Path("")
        summary_txt = sweep_dir / "summary.txt" if sweep_dir else Path("")
        summ = _parse_summary_txt(summary_txt) if summary_txt.is_file() else {}

        if code != 0:
            warning_parts.append(f"exit_{code}")
        if not results_csv.is_file():
            warning_parts.append("missing_results_csv")

        result_rows = 0
        best: dict[str, Any] = {}
        pfr = ""
        if results_csv.is_file():
            df = pd.read_csv(results_csv)
            result_rows = len(df)
            best = _best_row_metrics(df)
            if "profit_factor_r" in df.columns and not df.empty:
                d = df.sort_values("profit_factor", ascending=False, na_position="last").iloc[0]
                v = d.get("profit_factor_r")
                pfr = float(v) if pd.notna(v) else ""
            if result_rows == 0:
                warning_parts.append("zero_result_rows")

        manifest_rows.append(
            {
                "strategy": strategy,
                "status": "ok" if code == 0 else f"exit_{code}",
                "elapsed_sec": round(elapsed, 3),
                "raw_grid_size": raw_sz,
                "capped": "yes" if capped else "no",
                "max_combos": max_combos if max_combos is not None else "",
                "result_rows": result_rows,
                "best_trades": best.get("best_trades", ""),
                "best_total_r": best.get("best_total_r", ""),
                "best_profit_factor": best.get("best_profit_factor", ""),
                "best_profit_factor_r": pfr,
                "best_max_drawdown_r": best.get("best_max_drawdown_r", ""),
                "best_avg_bars_held": best.get("best_avg_bars_held", ""),
                "best_eod_count": best.get("best_eod_count", ""),
                "best_end_of_data_count": best.get("best_end_of_data_count", ""),
                "sweep_folder": str(sweep_dir.resolve()) if sweep_dir else "",
                "results_csv": str(results_csv.resolve()) if results_csv.is_file() else "",
                "warning": "; ".join(warning_parts),
            }
        )
        _write_manifest(out_dir, manifest_rows)

    return manifest_rows


def write_candidate_selection_config(out_dir: Path) -> None:
    body = """# Candidate selection — Layer 1 v2 completion (QQQ 2023–2024)

Generated via `src/research/select_candidates.py --manifest sweep_manifest.csv`.

## Strict thresholds

- `min_trades`: 40
- `min_profit_factor`: 1.05
- `min_total_r`: 0
- `max_drawdown_r`: -60
- `max_avg_bars_held`: 120
- `max_eod_count`: 0
- `max_end_of_data_count`: 0

## Relaxed fallback (enabled)

- `min_trades`: 25
- `min_profit_factor`: 1.00
- `min_total_r`: -5
- `max_drawdown_r`: -70
- `max_avg_bars_held`: 150 (`--relaxed-max-avg-bars-held`)

## Top per strategy

- `--top-per-strategy`: **5**

## Output files

- `selected_candidates.csv`
- `selected_candidates/*.yaml`
- `candidate_summary.md`
- `summary.txt`
- `no_candidate_strategies.txt`

Strategies with **no** rows passing strict or relaxed filters are listed in `no_candidate_strategies.txt`.
"""
    (out_dir / "candidate_selection_config.md").write_text(body, encoding="utf-8")


def write_no_candidate_strategies(out_dir: Path, universe: list[str]) -> None:
    sel_csv = out_dir / "selected_candidates.csv"
    if not sel_csv.is_file():
        (out_dir / "no_candidate_strategies.txt").write_text(
            "\n".join(universe) + "\n", encoding="utf-8"
        )
        return
    df = pd.read_csv(sel_csv)
    if df.empty or "strategy" not in df.columns:
        missing = universe
    else:
        have = set(df["strategy"].astype(str).unique())
        missing = [s for s in universe if s not in have]
    lines = [s for s in missing]
    (out_dir / "no_candidate_strategies.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_select_candidates(out_dir: Path, *, tag: str) -> int:
    man = out_dir / "sweep_manifest.csv"
    if not man.is_file():
        print("ERROR missing sweep_manifest.csv", file=sys.stderr)
        return 2
    cmd = [
        sys.executable,
        str(SELECT_PY),
        "--manifest",
        str(man.resolve()),
        "--output-root",
        str(out_dir.resolve()),
        "--tag",
        tag,
        "--top-per-strategy",
        "5",
        "--min-trades",
        "40",
        "--min-profit-factor",
        "1.05",
        "--min-total-r",
        "0",
        "--max-drawdown-r",
        "-60",
        "--max-avg-bars-held",
        "120",
        "--max-eod-count",
        "0",
        "--max-end-of-data-count",
        "0",
        "--allow-relaxed-fallback",
        "--relaxed-min-trades",
        "25",
        "--relaxed-min-profit-factor",
        "1.0",
        "--relaxed-min-total-r",
        "-5",
        "--relaxed-max-drawdown-r",
        "-70",
        "--relaxed-max-avg-bars-held",
        "150",
    ]
    print("[select_candidates] " + " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=str(_ROOT))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Layer 1 sweeps: Strategy Library v2 completion (9 strategies).")
    p.add_argument("--asset", default="equity")
    p.add_argument("--symbol", default="QQQ")
    p.add_argument("--start", default="2023-01-01")
    p.add_argument("--end", default="2024-12-31")
    p.add_argument("--tag", default="layer1_v2_completion_qqq_2023_2024")
    p.add_argument("--output-root", type=Path, default=Path("src/research/results/layer1_v2_completion_qqq_2023_2024"))
    p.add_argument("--top", type=int, default=50)
    p.add_argument("--min-trades", type=int, default=25)
    p.add_argument("--progress-every", type=int, default=50)
    p.add_argument("--no-sweeps", action="store_true", help="Preflight + grid_review only.")
    p.add_argument(
        "--select-candidates",
        action="store_true",
        help="After sweeps (or if manifest exists), run select_candidates + sidecar files.",
    )
    args = p.parse_args(argv)

    out_dir = args.output_root
    if not out_dir.is_absolute():
        out_dir = Path.cwd() / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    strategies = list(COMPLETION_STRATEGIES)

    pre_rows = run_preflight(strategies, out_dir)
    pf_fields = list(pre_rows[0].keys()) if pre_rows else []
    _write_csv(out_dir / "preflight_check.csv", pre_rows, pf_fields)
    (out_dir / "preflight_check.md").write_text(
        _md_table("# Layer 1 v2 completion — preflight", pre_rows, pf_fields),
        encoding="utf-8",
    )

    grid_rows = run_grid_review(strategies, out_dir)
    gf = list(grid_rows[0].keys()) if grid_rows else []
    _write_csv(out_dir / "grid_review.csv", grid_rows, gf)
    (out_dir / "grid_review.md").write_text(
        _md_table("# Layer 1 v2 completion — grid review", grid_rows, gf),
        encoding="utf-8",
    )

    failed_pf = [r for r in pre_rows if r.get("loader_ok") != "yes" or r.get("default_config_valid") != "yes" or r.get("focused_config_valid") != "yes"]
    if failed_pf:
        print("ERROR preflight failures — fix before sweeps:", failed_pf, file=sys.stderr)
        return 2

    grid_by_strategy = {r["strategy"]: r for r in grid_rows}

    if args.no_sweeps:
        print("[done] preflight + grid_review only", flush=True)
        return 0

    run_sweeps(
        strategies=strategies,
        out_dir=out_dir,
        asset=args.asset,
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        tag=args.tag,
        top=args.top,
        min_trades=args.min_trades,
        progress_every=args.progress_every,
        grid_by_strategy=grid_by_strategy,
    )

    if args.select_candidates:
        rc = run_select_candidates(out_dir, tag=args.tag)
        write_candidate_selection_config(out_dir)
        write_no_candidate_strategies(out_dir, strategies)
        return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
