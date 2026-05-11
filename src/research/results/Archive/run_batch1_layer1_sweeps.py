"""Run Layer 1 2023–2024 sweeps for Strategy Library v2 Batch 1; write sweep_manifest.{csv,md}."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.strategies.loader import grid_size, load_testing_config

TAG = "layer1_v2_batch1_qqq_2023_2024"
BATCH1 = [
    "intraday_ma_crossover",
    "rsi_failure_swing",
    "bollinger_squeeze_breakout",
    "bollinger_band_fade_chop",
    "donchian_channel_breakout",
    "consecutive_bar_exhaustion",
]

# Raw grid > 2000 → cap 500 combos; donchian tuned to 1728 → full grid.
MAX_COMBOS_CAP = 500
FULL_GRID_THRESHOLD = 2000


def _best_row(df: pd.DataFrame, min_trades: int = 25) -> pd.Series | None:
    if df.empty or "trades" not in df.columns:
        return None
    sub = df[df["trades"] >= min_trades].copy()
    if sub.empty:
        return None
    sc = "profit_factor"
    if sc not in sub.columns:
        return sub.iloc[0]
    sub = sub.sort_values(
        sc,
        ascending=False,
        key=lambda s: s.astype(float).replace(float("inf"), 1e308),
    )
    return sub.iloc[0]


def _run_sweep(strategy: str) -> dict[str, object]:
    raw_n = grid_size(load_testing_config(strategy))
    capped = raw_n > FULL_GRID_THRESHOLD
    max_arg: list[str] = []
    if capped:
        max_arg = ["--max-combos", str(MAX_COMBOS_CAP)]

    cmd = [
        sys.executable,
        str(_ROOT / "src" / "backtest" / "sweep.py"),
        "--strategy",
        strategy,
        "--testing-config",
        str(_ROOT / "src" / "strategies" / "testing_parameters" / f"{strategy}_focused.yaml"),
        "--asset",
        "equity",
        "--symbols",
        "QQQ",
        "--start",
        "2023-01-01",
        "--end",
        "2024-12-31",
        "--top",
        "50",
        "--min-trades",
        "25",
        "--profile",
        "--tag",
        TAG,
        "--progress-every",
        "50",
        *max_arg,
    ]
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, cwd=str(_ROOT), capture_output=True, text=True)
    elapsed = time.perf_counter() - t0
    stdout = proc.stdout or ""
    m = re.search(r"Wrote sweep results to:\s*(.+)", stdout)
    sweep_folder = ""
    results_csv = ""
    if m:
        sweep_folder = m.group(1).strip()
        results_csv = str(Path(sweep_folder) / "results.csv")
    row: dict[str, object] = {
        "strategy": strategy,
        "status": "ok" if proc.returncode == 0 and results_csv else f"error_{proc.returncode}",
        "elapsed_sec": round(elapsed, 3),
        "capped": capped,
        "max_combos": MAX_COMBOS_CAP if capped else "",
        "raw_grid_size": raw_n,
        "sweep_folder": sweep_folder,
        "results_csv": results_csv,
        "stderr_tail": (proc.stderr or "")[-500:] if proc.stderr else "",
    }
    if results_csv and Path(results_csv).is_file():
        df = pd.read_csv(results_csv)
        row["result_rows"] = len(df)
        br = _best_row(df, min_trades=25)
        if br is not None:
            row["best_trades"] = int(br.get("trades", 0))
            row["best_total_r"] = float(br.get("total_r", 0))
            row["best_profit_factor"] = float(br.get("profit_factor", 0))
            if "profit_factor_r" in br.index:
                row["best_profit_factor_r"] = float(br.get("profit_factor_r", float("nan")))
            else:
                row["best_profit_factor_r"] = ""
            row["best_max_drawdown_r"] = float(br.get("max_drawdown_r", 0))
            row["best_avg_bars_held"] = float(br.get("avg_bars_held", 0))
        else:
            row["best_trades"] = ""
            row["best_total_r"] = ""
            row["best_profit_factor"] = ""
            row["best_profit_factor_r"] = ""
            row["best_max_drawdown_r"] = ""
            row["best_avg_bars_held"] = ""
    else:
        row["result_rows"] = 0
        row["best_trades"] = ""
        row["best_total_r"] = ""
        row["best_profit_factor"] = ""
        row["best_profit_factor_r"] = ""
        row["best_max_drawdown_r"] = ""
        row["best_avg_bars_held"] = ""
    return row


def _write_manifest_md(out_dir: Path, mf: pd.DataFrame) -> None:
    cols = [
        "strategy",
        "status",
        "elapsed_sec",
        "capped",
        "max_combos",
        "raw_grid_size",
        "result_rows",
        "best_trades",
        "best_total_r",
        "best_profit_factor",
        "best_profit_factor_r",
        "best_max_drawdown_r",
        "best_avg_bars_held",
        "sweep_folder",
        "results_csv",
    ]
    for c in cols:
        if c not in mf.columns:
            mf[c] = ""
    lines = [
        "# Layer 1 Batch 1 — sweep manifest (QQQ 2023–2024)",
        "",
        f"Tag: `{TAG}`. Grids > {FULL_GRID_THRESHOLD} raw combos use `--max-combos {MAX_COMBOS_CAP}` (capped).",
        "",
    ]
    disp = mf[cols].copy()
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join("---" for _ in cols) + " |")
    for _, r in disp.iterrows():
        cells = [str(r[c]).replace("|", "\\|") for c in cols]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    (out_dir / "sweep_manifest.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    out_dir = _ROOT / "src" / "research" / "results" / "layer1_v2_batch1_qqq_2023_2024"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_csv = out_dir / "sweep_manifest.csv"
    if manifest_csv.is_file() and not os.environ.get("QT_REGENERATE_BATCH1_SWEEPS"):
        print(f"Skip sweeps (exists {manifest_csv}); set QT_REGENERATE_BATCH1_SWEEPS=1 to rerun.", flush=True)
        if not (out_dir / "sweep_manifest.md").is_file():
            mf = pd.read_csv(manifest_csv)
            _write_manifest_md(out_dir, mf)
        return 0

    manifest_rows: list[dict[str, object]] = []
    for s in BATCH1:
        print(f"=== sweep {s} ===", flush=True)
        manifest_rows.append(_run_sweep(s))

    mf = pd.DataFrame(manifest_rows)
    cols = [
        "strategy",
        "status",
        "elapsed_sec",
        "capped",
        "max_combos",
        "raw_grid_size",
        "result_rows",
        "best_trades",
        "best_total_r",
        "best_profit_factor",
        "best_profit_factor_r",
        "best_max_drawdown_r",
        "best_avg_bars_held",
        "sweep_folder",
        "results_csv",
    ]
    for c in cols:
        if c not in mf.columns:
            mf[c] = ""
    mf[cols].to_csv(out_dir / "sweep_manifest.csv", index=False)
    _write_manifest_md(out_dir, mf)
    print(f"Wrote {out_dir / 'sweep_manifest.csv'}", flush=True)
    return 0 if all(manifest_rows[i].get("status") == "ok" for i in range(len(manifest_rows))) else 1


if __name__ == "__main__":
    raise SystemExit(main())
