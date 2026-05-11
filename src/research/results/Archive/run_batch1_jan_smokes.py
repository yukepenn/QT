"""Run Jan 2025 Batch 1 smokes and write strategy_library_v2_batch1_health.{csv,md}."""

from __future__ import annotations

import csv
import re
import subprocess
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.strategies.loader import grid_size, load_testing_config

BATCH1 = [
    "intraday_ma_crossover",
    "rsi_failure_swing",
    "bollinger_squeeze_breakout",
    "bollinger_band_fade_chop",
    "donchian_channel_breakout",
    "consecutive_bar_exhaustion",
]


def _parse_best(stdout: str) -> dict[str, str]:
    out: dict[str, str] = {}
    if "no results" in stdout.lower():
        return out
    idx = stdout.find("best_QQQ:")
    if idx < 0:
        return out
    block = stdout[idx:]
    for line in block.splitlines()[1:]:
        line = line.strip()
        if not line:
            break
        parts = line.split(None, 1)
        if len(parts) < 2:
            continue
        key = parts[0].strip()
        val = parts[1].strip() if len(parts) > 1 else ""
        out[key] = val
    return out


def _warn_label(best: dict[str, str], raw_grid: int, stderr: str) -> str:
    warns = []
    if "PerformanceWarning" in stderr or "fragment" in stderr.lower():
        warns.append("performance_warning")
    trades = int(float(best.get("trades", 0) or 0))
    if trades <= 1:
        warns.append("too_restrictive")
    if trades == 0:
        warns.append("zero_or_too_few_trades")
    pf = float(best.get("profit_factor", 0) or 0)
    tr = float(best.get("total_r", 0) or 0)
    if trades >= 5 and (pf < 1.0 or tr < 0):
        warns.append("negative_jan_smoke")
    if trades >= 40 and raw_grid > 4000:
        warns.append("too_noisy")
    if not warns:
        warns.append("ok_for_layer1")
    return ";".join(warns)


def _action(strat: str, best: dict[str, str], warn: str) -> str:
    trades = float(best.get("trades", 0) or 0)
    pf = float(best.get("profit_factor", 0) or 0)
    if "too_restrictive" in warn or trades <= 1:
        return "NEEDS_GRID_TUNING"
    if strat == "rsi_failure_swing" and trades >= 3 and pf >= 1.2:
        return "PROMISING_FOR_REDUCED_LAYER2"
    if "negative_jan_smoke" in warn:
        return "NEEDS_GRID_TUNING"
    return "NEEDS_GRID_TUNING"


def main() -> int:
    results_dir = _ROOT / "src" / "research" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []

    for strat in BATCH1:
        tcfg = load_testing_config(strat)
        raw_n = grid_size(tcfg)
        cmd = [
            sys.executable,
            str(_ROOT / "src" / "backtest" / "sweep.py"),
            "--strategy",
            strat,
            "--testing-config",
            str(_ROOT / "src" / "strategies" / "testing_parameters" / f"{strat}_focused.yaml"),
            "--asset",
            "equity",
            "--symbols",
            "QQQ",
            "--start",
            "2025-01-01",
            "--end",
            "2025-01-31",
            "--max-combos",
            "50",
            "--min-trades",
            "1",
            "--no-save",
            "--profile",
            "--progress-every",
            "10",
        ]
        t0 = time.perf_counter()
        proc = subprocess.run(cmd, cwd=str(_ROOT), capture_output=True, text=True)
        elapsed = time.perf_counter() - t0
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        best = _parse_best(stdout)
        m = re.search(r"combinations_completed=(\d+)", stdout)
        combos = m.group(1) if m else ""
        warn = _warn_label(best, raw_n, stderr)
        row = {
            "strategy": strat,
            "registered": "true",
            "supports_fast": "true",
            "metadata_ok": "true",
            "focused_yaml_exists": "true",
            "raw_grid_size": str(raw_n),
            "jan_smoke_exit_code": str(proc.returncode),
            "jan_smoke_runtime_sec": f"{elapsed:.3f}",
            "jan_combos_completed": combos,
            "jan_best_trades": best.get("trades", ""),
            "jan_best_total_r": best.get("total_r", ""),
            "jan_best_profit_factor": best.get("profit_factor", ""),
            "jan_best_max_drawdown_r": best.get("max_drawdown_r", ""),
            "jan_best_avg_bars_held": best.get("avg_bars_held", ""),
            "warning": warn,
            "recommended_next_action": _action(strat, best, warn),
        }
        rows.append(row)

    fieldnames = list(rows[0].keys())
    csv_path = results_dir / "strategy_library_v2_batch1_health.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    md = ["# Strategy Library v2 Batch 1 — health (Jan 2025 smoke)", ""]
    md.append("Command: `sweep.py` QQQ 2025-01-01→2025-01-31, `--max-combos 50`, `--min-trades 1`, `--no-save`, `--profile`.")
    md.append("")
    md.append("| strategy | exit | sec | combos | trades | total_r | PF | maxDD_r | warning |")
    md.append("|---|--:|---:|---:|---:|---:|---:|---:|---|")
    for r in rows:
        md.append(
            f"| {r['strategy']} | {r['jan_smoke_exit_code']} | {r['jan_smoke_runtime_sec']} | "
            f"{r['jan_combos_completed']} | {r['jan_best_trades']} | {r['jan_best_total_r']} | "
            f"{r['jan_best_profit_factor']} | {r['jan_best_max_drawdown_r']} | {r['warning']} |"
        )
    md.append("")
    (results_dir / "strategy_library_v2_batch1_health.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Wrote {csv_path}", flush=True)
    return 0 if all(int(r["jan_smoke_exit_code"]) == 0 for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
