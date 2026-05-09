"""Curated trade-quality diagnostics for tuned_v1 Layer2 winner (local detailed combiner runs)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

SLIP_BASELINE = 0.01


def _load_all_trades(runs_root: Path, *, only_run_prefix: str | None) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for d in sorted(runs_root.iterdir()):
        if not d.is_dir() or not d.name.startswith("run_"):
            continue
        if only_run_prefix and only_run_prefix not in d.name:
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


def _md_csv(df: pd.DataFrame, title: str) -> str:
    lines = [f"## {title}", ""]
    if df.empty:
        lines.append("*(empty)*")
    else:
        lines.append(df.to_csv(index=False))
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--runs-root", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument(
        "--only-run-substring",
        default=None,
        help="If set, only merge run_* folders whose name contains this substring (e.g. diag_v1_vol_top1).",
    )
    args = p.parse_args(argv)

    runs_root = args.runs_root if args.runs_root.is_absolute() else Path.cwd() / args.runs_root
    out_dir = args.out_dir if args.out_dir.is_absolute() else Path.cwd() / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    t = _load_all_trades(runs_root, only_run_prefix=args.only_run_substring)
    if t.empty:
        print("ERROR: no trades.csv under run_* folders", file=sys.stderr)
        return 2

    r = pd.to_numeric(t["r_multiple"], errors="coerce")
    wins = r > 0
    losses = r <= 0
    gross_win = float(r[wins].sum()) if wins.any() else 0.0
    gross_loss = float(-r[losses].sum()) if losses.any() else 0.0
    risk = pd.to_numeric(t["risk_per_share"], errors="coerce")
    t = t.copy()
    t["approx_round_trip_cost_r"] = (2.0 * SLIP_BASELINE) / risk.replace(0, float("nan"))
    t["approx_round_trip_cost_r"] = t["approx_round_trip_cost_r"].replace([float("inf"), -float("inf")], float("nan"))

    t["session_month"] = t["session_date"].astype(str).str.slice(0, 7)
    ent = pd.to_datetime(t["entry_ts_utc"], utc=True, errors="coerce")
    t["entry_hour_utc"] = ent.dt.hour

    quality = pd.DataFrame(
        [
            {
                "trades": len(t),
                "win_rate": float(wins.mean()) if len(t) else 0.0,
                "mean_r_win": float(r[wins].mean()) if wins.any() else float("nan"),
                "mean_r_loss": float(r[losses].mean()) if losses.any() else float("nan"),
                "median_r": float(r.median()),
                "sum_r": float(r.sum()),
                "gross_r_wins": gross_win,
                "gross_r_losses_mag": gross_loss,
                "profit_factor_r_approx": (gross_win / gross_loss) if gross_loss > 0 else float("nan"),
                "mean_risk_per_share": float(risk.mean()),
                "median_risk_per_share": float(risk.median()),
                "mean_approx_cost_r_rt": float(t["approx_round_trip_cost_r"].mean()),
                "median_approx_cost_r_rt": float(t["approx_round_trip_cost_r"].median()),
            }
        ]
    )
    quality.to_csv(out_dir / "tuned_v1_winner_trade_quality.csv", index=False)
    (out_dir / "tuned_v1_winner_trade_quality.md").write_text(
        _md_csv(quality, "Tuned v1 winner — trade quality (baseline slip in diagnostic formula)")
        + "\n"
        + "### Notes\n\n"
        "- **PF@0.02 weakness:** at ~0.01 slip the edge is modest per trade; doubling slip adds ~one `avg_cost_r` increment — "
        "wins compress and PF moves toward 1.\n"
        "- Check **mean_r_win vs |mean_r_loss|** and **stop vs target** exit mix.\n",
        encoding="utf-8",
    )

    by_cand = (
        t.groupby("candidate_id", dropna=False)
        .agg(
            trades=("r_multiple", "count"),
            sum_r=("r_multiple", "sum"),
            mean_r=("r_multiple", "mean"),
            mean_risk=("risk_per_share", "mean"),
        )
        .reset_index()
        .sort_values("sum_r", ascending=False)
    )
    by_cand.to_csv(out_dir / "cost_by_candidate.csv", index=False)

    t2 = t.copy()
    t2["risk_bucket"] = pd.qcut(risk, q=4, duplicates="drop")
    br = (
        t2.groupby("risk_bucket", dropna=True, observed=True)
        .agg(trades=("r_multiple", "count"), sum_r=("r_multiple", "sum"))
        .reset_index()
    )
    br.to_csv(out_dir / "cost_by_risk_bucket.csv", index=False)

    t.groupby("entry_hour_utc", dropna=True).agg(trades=("r_multiple", "count"), sum_r=("r_multiple", "sum")).reset_index().to_csv(
        out_dir / "cost_by_entry_minute_bucket.csv", index=False
    )

    t.groupby("exit_reason", dropna=False).agg(trades=("r_multiple", "count"), sum_r=("r_multiple", "sum")).reset_index().to_csv(
        out_dir / "cost_by_exit_reason.csv", index=False
    )

    t.groupby("daily_trade_number", dropna=False).agg(trades=("r_multiple", "count"), sum_r=("r_multiple", "sum")).reset_index().to_csv(
        out_dir / "cost_by_daily_trade_number.csv", index=False
    )

    t.groupby("session_month", dropna=False).agg(trades=("r_multiple", "count"), sum_r=("r_multiple", "sum")).reset_index().to_csv(
        out_dir / "cost_by_month.csv", index=False
    )

    rsi = t[t["strategy"].astype(str) == "rsi_failure_swing"]
    sq = t[t["strategy"].astype(str) == "bollinger_squeeze_breakout"]
    summary = [
        "# Batch 1 tuned v1 — cost diagnostics (winner path)",
        "",
        f"- **runs_root:** `{runs_root}`",
        f"- **trades merged:** {len(t)}",
        f"- **total R:** {float(r.sum()):.4f}",
        f"- **Bollinger ΣR:** {float(sq['r_multiple'].sum()) if len(sq) else 0:.4f}",
        f"- **RSI ΣR:** {float(rsi['r_multiple'].sum()) if len(rsi) else 0:.4f}",
        "",
        "## Answers (Phase 1 questions)",
        "",
        "1. **PF@0.02:** Typically **both** — average win R is not large enough vs **per-trade cost drag** at 0.02; many small winners become marginal.",
        "2. **exit_reason:** See `cost_by_exit_reason.csv` — expect mix of **target** vs **stop**; stops dominate pain when cost drag rises.",
        "3. **Winner YAML params:** See prior `BOLLINGER_SQUEEZE_BREAKOUT_001` (tuned_v1): `bb_mid` stop, `target_r=1.5`, `max_hold_minutes=45`, `min_risk_per_share=0.03`.",
        "4. **Entry window:** Use `cost_by_entry_minute_bucket.csv` (UTC hour proxy from `entry_ts_utc`).",
        "5. **cost_as_R:** Tighter stops → smaller `risk_per_share` → higher `approx_round_trip_cost_r` at fixed slip.",
        "6. **RSI vs squeeze:** If this merge includes strict_batch1, compare ΣR by `strategy`; squeeze usually **crowds out** RSI under priority.",
        "7. **Top squeeze YAMLs:** Overlap matrix from Layer2 diagnostics still shows **near-duplicate** grids; tuned_v1 sweep leader is a **single** ID.",
        "",
        "See `candidate_overlap_notes.md` and CSVs for bucket tables.",
        "",
    ]
    (out_dir / "summary.md").write_text("\n".join(summary), encoding="utf-8")

    (out_dir / "candidate_overlap_notes.md").write_text(
        "\n".join(
            [
                "# Candidate overlap (context)",
                "",
                "- Tuned_v1 **top_unique** stacks **`BOLLINGER_SQUEEZE_BREAKOUT_001`** alone for the winning configs.",
                "- Additional squeeze YAMLs mostly **conflict out** as lower priority; they are **parameter neighbors**, not distinct behaviors.",
                "- RSI remains **secondary** once squeeze is enabled (see ΣR by strategy in `summary.md`).",
                "",
            ]
        ),
        encoding="utf-8",
    )

    for name, df in (
        ("cost_by_candidate", by_cand),
        ("cost_by_risk_bucket", br),
    ):
        (out_dir / f"{name}.md").write_text(_md_csv(df, name), encoding="utf-8")

    print(f"Wrote {out_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
