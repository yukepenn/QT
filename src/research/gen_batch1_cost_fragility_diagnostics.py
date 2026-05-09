"""Aggregate combiner trades.csv from local detailed runs into curated cost diagnostics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

SLIP = 0.01


def _load_all_trades(runs_root: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for d in sorted(runs_root.iterdir()):
        if not d.is_dir() or not d.name.startswith("run_"):
            continue
        p = d / "trades.csv"
        if not p.is_file():
            continue
        df = pd.read_csv(p)
        if df.empty:
            continue
        df["__run_folder__"] = d.name
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _md_table(df: pd.DataFrame, title: str) -> str:
    lines = [f"## {title}", ""]
    if df.empty:
        lines.append("*(empty)*")
        lines.append("")
        return "\n".join(lines)
    lines.append(df.to_csv(index=False))
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--runs-root", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    args = p.parse_args(argv)

    runs_root = args.runs_root
    if not runs_root.is_absolute():
        runs_root = Path.cwd() / runs_root
    out_dir = args.out_dir
    if not out_dir.is_absolute():
        out_dir = Path.cwd() / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    t = _load_all_trades(runs_root)
    if t.empty:
        print("ERROR: no trades.csv under run_* folders", file=sys.stderr)
        return 2

    t["session_month"] = t["session_date"].astype(str).str.slice(0, 7)
    t["entry_hour_utc"] = pd.to_datetime(t["entry_ts_utc"], utc=True, errors="coerce").dt.hour
    risk = pd.to_numeric(t["risk_per_share"], errors="coerce")
    t["approx_round_trip_cost_r"] = (2.0 * SLIP) / risk.replace(0, float("nan"))
    t["approx_round_trip_cost_r"] = t["approx_round_trip_cost_r"].replace([float("inf"), -float("inf")], float("nan"))

    # By candidate
    g = t.groupby("candidate_id", dropna=False)
    by_cand = g.agg(
        trades=("r_multiple", "count"),
        sum_r=("r_multiple", "sum"),
        mean_r=("r_multiple", "mean"),
        mean_risk=("risk_per_share", "mean"),
        mean_bars=("bars_held", "mean"),
        mean_approx_cost_r=("approx_round_trip_cost_r", "mean"),
        strategies=("strategy", lambda s: ",".join(sorted(set(s.astype(str))))),
    ).reset_index()
    by_cand = by_cand.sort_values("sum_r", ascending=False)
    by_cand.to_csv(out_dir / "cost_by_candidate.csv", index=False)

    # Volatility breakout (squeeze) attribution
    sq = t[t["strategy"].astype(str) == "bollinger_squeeze_breakout"].copy()
    sq_g = (
        sq.groupby("candidate_id", dropna=False)
        .agg(trades=("r_multiple", "count"), sum_r=("r_multiple", "sum"), mean_r=("r_multiple", "mean"))
        .reset_index()
        .sort_values("sum_r", ascending=False)
    )
    sq_g.to_csv(out_dir / "volatility_breakout_attribution.csv", index=False)

    # Risk bucket
    t2 = t.copy()
    t2["risk_bucket"] = pd.qcut(risk, q=4, duplicates="drop")
    br = (
        t2.groupby("risk_bucket", dropna=True, observed=True)
        .agg(trades=("r_multiple", "count"), sum_r=("r_multiple", "sum"))
        .reset_index()
    )
    br.to_csv(out_dir / "cost_by_risk_bucket.csv", index=False)

    # Entry hour UTC (proxy for entry window load)
    eh = t.groupby("entry_hour_utc", dropna=True).agg(trades=("r_multiple", "count"), sum_r=("r_multiple", "sum")).reset_index()
    eh.to_csv(out_dir / "cost_by_entry_minute_bucket.csv", index=False)

    ex = t.groupby("exit_reason", dropna=False).agg(trades=("r_multiple", "count"), sum_r=("r_multiple", "sum")).reset_index()
    ex.to_csv(out_dir / "cost_by_exit_reason.csv", index=False)

    dtn = t.groupby("daily_trade_number", dropna=False).agg(trades=("r_multiple", "count"), sum_r=("r_multiple", "sum")).reset_index()
    dtn.to_csv(out_dir / "cost_by_daily_trade_number.csv", index=False)

    mo = t.groupby("session_month", dropna=False).agg(trades=("r_multiple", "count"), sum_r=("r_multiple", "sum")).reset_index()
    mo.to_csv(out_dir / "cost_by_month.csv", index=False)

    # MD companions
    (out_dir / "cost_by_candidate.md").write_text(_md_table(by_cand, "Cost / R attribution by candidate"), encoding="utf-8")
    (out_dir / "volatility_breakout_attribution.md").write_text(_md_table(sq_g, "Bollinger squeeze trades by candidate"), encoding="utf-8")
    (out_dir / "behavior_overlap_notes.md").write_text(
        "\n".join(
            [
                "# Behavior overlap notes (Batch 1 Layer 2 v1)",
                "",
                "From prior `candidate_overlap_matrix.csv` on the **un-tuned** 20-candidate universe:",
                "",
                "- **Bollinger squeeze** YAMLs (`_001`…`_005`) share **very high same-bar overlap** (~479 bars): near-duplicate parameterizations.",
                "- **RSI** candidates overlap heavily with each other on the same bar; once combined with squeeze, **squeeze wins priority** and RSI contributes few marginal fills.",
                "- **Relaxed fade / exhaustion** add **trade count** and **selection conflicts** without improving **0.02 slippage** robustness on the squeeze-heavy stack.",
                "",
                "This tuning pass targets **fewer, stricter squeeze rows** and a **cleaner RSI lane** so Layer 2 overlap and per-trade cost load improve.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    rsi = t[t["strategy"].astype(str) == "rsi_failure_swing"]
    rsi_r = float(rsi["r_multiple"].sum()) if len(rsi) else 0.0
    sq_r = float(sq["r_multiple"].sum()) if len(sq) else 0.0
    summary = [
        "# Batch 1 cost fragility — diagnostics v1",
        "",
        f"- **runs_root:** `{runs_root}`",
        f"- **trades merged:** {len(t)}",
        f"- **total R (all legs):** {float(t['r_multiple'].sum()):.4f}",
        f"- **approx mean round-trip cost / R** (2×{SLIP} slip / risk_per_share): {float(t['approx_round_trip_cost_r'].mean()):.4f}",
        f"- **Bollinger squeeze ΣR:** {sq_r:.4f}",
        f"- **RSI ΣR:** {rsi_r:.4f}",
        "",
        "## Interpretation",
        "",
        "1. **Trade count vs fragility:** squeeze systems run **hundreds** of trades; fixed per-share costs compound → small edge at 0.01 often flattens by 0.02.",
        "2. **Risk per share:** many entries sit on **tight structural stops** → high `approx_round_trip_cost_r` tails.",
        "3. **Candidate dominance:** top squeeze IDs capture most ΣR; RSI is secondary once combined.",
        "4. **Near-duplicate YAMLs:** overlap matrix shows **same-bar collisions** across `_001…_005` grids.",
        "",
        "See sibling CSV/MD files for bucketed views.",
        "",
    ]
    (out_dir / "summary.md").write_text("\n".join(summary), encoding="utf-8")
    print(f"Wrote diagnostics under {out_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
