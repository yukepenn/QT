"""Diagnostics for the gap_acceptance_failure + failed_orb family (Layer 3).

This module is diagnostics-only:
- It re-runs frozen mini-WFO systems over a small date window (e.g. Dec 2025)
  to regenerate compact trades locally.
- It writes curated group summaries under src/research/results/.

No strategy logic changes, no full WFO.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.combiner.run import run_combiner_fixed_config
from src.data.read_bars import read_bars
from src.features.build_features import build_basic_features
from src.research.trade_enrichment import enrich_trades_with_context


@dataclass(frozen=True)
class RunSpec:
    run_id: str
    root: Path
    frozen_yaml: dict[str, Any]


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    return doc if isinstance(doc, dict) else {}


def _safe_mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _bucket_entry_minute(entry_ts_utc: pd.Series) -> pd.Series:
    """Bucket entry minute since 09:30 ET into coarse groups."""
    ts = pd.to_datetime(entry_ts_utc, utc=True, errors="coerce")
    try:
        ts_et = ts.dt.tz_convert("America/New_York")
    except Exception:
        # If tz conversion fails, fall back to UTC "as if" ET; still deterministic.
        ts_et = ts
    mins = ts_et.dt.hour.mul(60).add(ts_et.dt.minute).sub(9 * 60 + 30)
    out = pd.Series(index=mins.index, dtype="object")
    out[mins < 15] = "0-15"
    out[(mins >= 15) & (mins < 30)] = "15-30"
    out[(mins >= 30) & (mins < 60)] = "30-60"
    out[(mins >= 60) & (mins < 120)] = "60-120"
    out[mins >= 120] = "120+"
    out[mins.isna()] = "unknown"
    return out


def _bucket_risk(risk_per_share: pd.Series) -> pd.Series:
    x = pd.to_numeric(risk_per_share, errors="coerce")
    out = pd.Series(index=x.index, dtype="object")
    out[x < 0.03] = "<0.03"
    out[(x >= 0.03) & (x < 0.05)] = "0.03-0.05"
    out[(x >= 0.05) & (x < 0.10)] = "0.05-0.10"
    out[x >= 0.10] = ">0.10"
    out[x.isna()] = "unknown"
    return out


def _profit_factor_r(r_multiple: pd.Series) -> float | None:
    r = pd.to_numeric(r_multiple, errors="coerce").dropna()
    if len(r) == 0:
        return None
    pos = float(r[r > 0].sum())
    neg = float((-r[r < 0]).sum())
    if neg <= 1e-12:
        return None
    return pos / neg


def _group_summary(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if group_col not in df.columns:
        return pd.DataFrame([{"group": "MISSING_COLUMN", "reason": f"missing {group_col}"}])

    g = df.groupby(group_col, dropna=False)
    r = pd.to_numeric(df.get("r_multiple"), errors="coerce")
    out = g.agg(
        trades=("r_multiple", "count"),
        total_r=("r_multiple", lambda s: float(pd.to_numeric(s, errors="coerce").sum())),
        avg_r=("r_multiple", lambda s: float(pd.to_numeric(s, errors="coerce").mean()) if len(s) else 0.0),
        win_rate=("r_multiple", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean()) if len(s) else 0.0),
        max_loss_r=("r_multiple", lambda s: float(pd.to_numeric(s, errors="coerce").min()) if len(s) else 0.0),
    ).reset_index()
    out = out.rename(columns={group_col: "group"})

    # Derived stats that need full group series.
    pf_rows: list[float | None] = []
    for name, sub in g:
        pf_rows.append(_profit_factor_r(sub["r_multiple"]) if "r_multiple" in sub.columns else None)
    out["profit_factor_r"] = pf_rows

    # Optional columns.
    for col in ("bars_held",):
        if col in df.columns:
            out[f"avg_{col}"] = [float(pd.to_numeric(sub[col], errors="coerce").mean()) for _, sub in g]
        else:
            out[f"avg_{col}"] = None

    for col in ("exit_reason",):
        if col in df.columns:
            out[f"{col}_unique"] = [int(sub[col].nunique(dropna=False)) for _, sub in g]
        else:
            out[f"{col}_unique"] = None

    return out.sort_values(["total_r", "trades"], ascending=[True, False], na_position="last").reset_index(drop=True)


def _load_runs(roots: list[Path]) -> list[RunSpec]:
    runs: list[RunSpec] = []
    for r in roots:
        rr = r.resolve()
        frozen_path = rr / "frozen_system" / "selected_frozen_system.yaml"
        frozen = _read_yaml(frozen_path)
        runs.append(RunSpec(run_id=rr.name, root=rr, frozen_yaml=frozen))
    return runs


def _regen_compact_trades(
    run: RunSpec,
    *,
    symbol: str,
    asset: str,
    start: str,
    end: str,
    output_dir: Path,
) -> Path | None:
    frozen = run.frozen_yaml
    combiner_yaml = frozen.get("combiner") or {}
    candidate_root = Path(str(frozen.get("candidate_root") or ""))
    candidate_ids = list(frozen.get("candidate_ids") or [])
    if not combiner_yaml or not candidate_root or not candidate_ids:
        return None

    _safe_mkdir(output_dir)
    out = run_combiner_fixed_config(
        combiner_yaml,
        candidate_root=candidate_root,
        candidate_set=None,
        candidate_ids=candidate_ids,
        top_per_strategy=1,
        asset=asset,
        symbol=symbol,
        start=start,
        end=end,
        output_dir=output_dir,
        detailed=False,
        save_compact_trades=True,
        save_full_signal_logs=False,
        save_rejected_signals=False,
        save_monthly_breakdown=False,
        save_equity=False,
        stress_slippages=None,
        tag=f"diag_{run.run_id}",
    )
    return out.get("trades_path")


def _write_df(path: Path, df: pd.DataFrame) -> None:
    _safe_mkdir(path.parent)
    df.to_csv(path, index=False)


def _write_md(path: Path, title: str, sections: list[tuple[str, pd.DataFrame]]) -> None:
    lines: list[str] = [f"# {title}", ""]
    for h, df in sections:
        lines.extend([f"## {h}", ""])
        try:
            lines.append(df.to_markdown(index=False))
        except Exception:
            lines.append(df.to_string(index=False))
        lines.append("")
    _safe_mkdir(path.parent)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_window_trades(
    run: RunSpec,
    *,
    symbol: str,
    asset: str,
    start: str,
    end: str,
    output_dir: Path,
) -> pd.DataFrame:
    """Regenerate compact trades for an arbitrary window and return as DataFrame."""
    p = _regen_compact_trades(run, symbol=symbol, asset=asset, start=start, end=end, output_dir=output_dir)
    if not p or not Path(p).is_file():
        return pd.DataFrame()
    df = pd.read_csv(p)
    df.insert(0, "run_id", run.run_id)
    return df


def _infer_train_test_windows(run: RunSpec) -> tuple[tuple[str, str] | None, tuple[str, str] | None]:
    """Best-effort: use selection_audit.json if present; else None."""
    audit = _read_yaml(run.root / "selection_audit.json") if False else None
    _ = audit
    sel = json.loads((run.root / "selection_audit.json").read_text(encoding="utf-8")) if (run.root / "selection_audit.json").is_file() else {}
    tr = sel.get("train_window") or {}
    te = sel.get("test_window") or {}
    t1 = (str(tr.get("start")), str(tr.get("end"))) if tr.get("start") and tr.get("end") else None
    t2 = (str(te.get("start")), str(te.get("end"))) if te.get("start") and te.get("end") else None
    return t1, t2


def _stack_groupings(
    df: pd.DataFrame, *, run_id: str, window: str, strategy_filter: str
) -> pd.DataFrame:
    """Return a long-form table across a few groupings for one strategy and window."""
    if df.empty or "strategy" not in df.columns:
        return pd.DataFrame()
    sub = df[df["strategy"] == strategy_filter].copy()
    if sub.empty:
        return pd.DataFrame()

    if "entry_ts_utc" in sub.columns:
        sub["entry_minute_bucket"] = _bucket_entry_minute(sub["entry_ts_utc"])
    else:
        sub["entry_minute_bucket"] = "MISSING_COLUMN"
    if "risk_per_share" in sub.columns:
        sub["risk_bucket"] = _bucket_risk(sub["risk_per_share"])
    else:
        sub["risk_bucket"] = "MISSING_COLUMN"

    out_parts: list[pd.DataFrame] = []
    for grouping in ("exit_reason", "entry_minute_bucket", "risk_bucket"):
        gdf = _group_summary(sub, grouping)
        gdf.insert(0, "window", window)
        gdf.insert(0, "grouping", grouping)
        gdf.insert(0, "strategy", strategy_filter)
        gdf.insert(0, "run_id", run_id)
        out_parts.append(gdf)
    return pd.concat(out_parts, ignore_index=True) if out_parts else pd.DataFrame()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gap/Failed family diagnostics (Dec 2025).")
    p.add_argument("--symbol", default="QQQ")
    p.add_argument("--asset", default="equity")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--roots", nargs="+", required=True)
    p.add_argument("--output-root", required=True)
    args = p.parse_args(argv)

    symbol = str(args.symbol).upper()
    if symbol != "QQQ":
        raise SystemExit("Only QQQ supported for this diagnostic.")

    out_root = Path(args.output_root)
    if not out_root.is_absolute():
        out_root = Path.cwd() / out_root
    _safe_mkdir(out_root)

    runs = _load_runs([Path(x) for x in args.roots])

    # Build features once for the requested window (used for enrichment).
    bars = read_bars(
        asset=str(args.asset),
        symbol=symbol,
        start=str(args.start),
        end=str(args.end),
        data_dir="data/raw/ibkr",
    )
    feats = build_basic_features(bars, orb_open_minutes=15, copy=True, allow_overwrite=False) if len(bars) else pd.DataFrame()

    all_trades: list[pd.DataFrame] = []
    per_run_rows: list[dict[str, Any]] = []

    for run in runs:
        run_out = out_root / "_runs" / run.run_id
        trades_path = _regen_compact_trades(
            run,
            symbol=symbol,
            asset=str(args.asset),
            start=str(args.start),
            end=str(args.end),
            output_dir=run_out,
        )
        if not trades_path or not Path(trades_path).is_file():
            per_run_rows.append({"run_id": run.run_id, "status": "missing_trades"})
            continue

        df = pd.read_csv(trades_path)
        df.insert(0, "run_id", run.run_id)
        if len(feats):
            df = enrich_trades_with_context(df, feats, timestamp_col="entry_ts_utc", idx_col="entry_idx", tolerance="2min")
        all_trades.append(df)

        per_run_rows.append(
            {
                "run_id": run.run_id,
                "trades": int(len(df)),
                "total_r": float(pd.to_numeric(df.get("r_multiple"), errors="coerce").sum()),
                "profit_factor_r": _profit_factor_r(df.get("r_multiple")),
                "worst_trade_r": float(pd.to_numeric(df.get("r_multiple"), errors="coerce").min())
                if "r_multiple" in df.columns and len(df)
                else None,
            }
        )

    df_all = pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame()

    # Add computed buckets.
    if len(df_all):
        if "entry_ts_utc" in df_all.columns:
            df_all["entry_minute_bucket"] = _bucket_entry_minute(df_all["entry_ts_utc"])
        else:
            df_all["entry_minute_bucket"] = "MISSING_COLUMN"

        if "risk_per_share" in df_all.columns:
            df_all["risk_bucket"] = _bucket_risk(df_all["risk_per_share"])
        else:
            df_all["risk_bucket"] = "MISSING_COLUMN"

    # Summary outputs.
    summary = pd.DataFrame(per_run_rows)
    _write_df(out_root / "dec2025_loss_cluster_summary.csv", summary)

    sections: list[tuple[str, pd.DataFrame]] = [("Per-run summary", summary)]

    if len(df_all):
        by_strategy = _group_summary(df_all, "strategy")
        by_exit = _group_summary(df_all, "exit_reason")
        by_day = _group_summary(df_all, "session_date")
        by_entry = _group_summary(df_all, "entry_minute_bucket")
        by_risk = _group_summary(df_all, "risk_bucket")
        by_gap_dir = _group_summary(df_all, "gap_direction")
        by_gap_size = _group_summary(df_all, "gap_size_bucket")
        by_vwap_side = _group_summary(df_all, "vwap_side_at_entry")
        by_orb_ctx = _group_summary(df_all, "orb_context")

        _write_df(out_root / "dec2025_by_strategy.csv", by_strategy)
        _write_df(out_root / "dec2025_by_exit_reason.csv", by_exit)
        _write_df(out_root / "dec2025_by_day.csv", by_day)
        _write_df(out_root / "dec2025_by_entry_minute_bucket.csv", by_entry)
        _write_df(out_root / "dec2025_by_risk_bucket.csv", by_risk)
        _write_df(out_root / "dec2025_by_gap_direction.csv", by_gap_dir)
        _write_df(out_root / "dec2025_by_gap_size_bucket.csv", by_gap_size)
        _write_df(out_root / "dec2025_by_vwap_side.csv", by_vwap_side)
        _write_df(out_root / "dec2025_by_orb_context.csv", by_orb_ctx)

        # Stop/target mode isn't represented in compact trades; keep explicit placeholder.
        _write_df(
            out_root / "dec2025_by_stop_target_mode.csv",
            pd.DataFrame([{"group": "MISSING_COLUMN", "reason": "stop/target mode not present in compact trades"}]),
        )

        sections.extend(
            [
                ("By strategy", by_strategy.head(50)),
                ("By exit_reason", by_exit.head(50)),
                ("By day", by_day.head(50)),
                ("By entry minute bucket", by_entry.head(50)),
                ("By risk bucket", by_risk.head(50)),
                ("By gap direction", by_gap_dir.head(50)),
                ("By gap size bucket", by_gap_size.head(50)),
                ("By VWAP side", by_vwap_side.head(50)),
                ("By ORB context", by_orb_ctx.head(50)),
            ]
        )

        # Small sample trade detail only (<=200 rows).
        if len(df_all) <= 200:
            _write_df(out_root / "dec2025_trade_detail_sample.csv", df_all)

    _write_md(out_root / "dec2025_loss_cluster_summary.md", "Dec 2025 loss cluster summary", sections)

    # Gap/fail strategy diagnostics across each run's train + test windows (small, curated).
    gap_rows: list[pd.DataFrame] = []
    fail_rows: list[pd.DataFrame] = []
    for run in runs:
        train_w, test_w = _infer_train_test_windows(run)
        for label, w in (("train", train_w), ("test", test_w)):
            if not w:
                continue
            s0, e0 = w
            dfw = _run_window_trades(
                run,
                symbol=symbol,
                asset=str(args.asset),
                start=s0,
                end=e0,
                output_dir=out_root / "_windows" / run.run_id / label,
            )
            if dfw.empty:
                continue
            # Enrich using features built for this window (per-window build to avoid lookahead).
            bars_w = read_bars(
                asset=str(args.asset),
                symbol=symbol,
                start=s0,
                end=e0,
                data_dir="data/raw/ibkr",
            )
            feats_w = build_basic_features(bars_w, orb_open_minutes=15, copy=True, allow_overwrite=False) if len(bars_w) else pd.DataFrame()
            if len(feats_w):
                dfw = enrich_trades_with_context(dfw, feats_w, timestamp_col="entry_ts_utc", idx_col="entry_idx", tolerance="2min")
            gap_rows.append(_stack_groupings(dfw, run_id=run.run_id, window=label, strategy_filter="gap_acceptance_failure"))
            fail_rows.append(_stack_groupings(dfw, run_id=run.run_id, window=label, strategy_filter="failed_orb"))

    gap_df = pd.concat([x for x in gap_rows if x is not None and len(x)], ignore_index=True) if gap_rows else pd.DataFrame()
    fail_df = pd.concat([x for x in fail_rows if x is not None and len(x)], ignore_index=True) if fail_rows else pd.DataFrame()

    if len(gap_df):
        _write_df(out_root / "gap_acceptance_diagnostic.csv", gap_df)
        _write_md(
            out_root / "gap_acceptance_diagnostic.md",
            "Gap acceptance diagnostic (train/test windows)",
            [("Top loss buckets (first 60 rows)", gap_df.head(60))],
        )
    else:
        _write_df(out_root / "gap_acceptance_diagnostic.csv", pd.DataFrame([{"status": "no_gap_trades"}]))
        _write_md(out_root / "gap_acceptance_diagnostic.md", "Gap acceptance diagnostic (train/test windows)", [("Status", pd.DataFrame([{"status": "no_gap_trades"}]))])

    if len(fail_df):
        _write_df(out_root / "failed_orb_diagnostic.csv", fail_df)
        _write_md(
            out_root / "failed_orb_diagnostic.md",
            "Failed ORB diagnostic (train/test windows)",
            [("Top loss buckets (first 60 rows)", fail_df.head(60))],
        )
    else:
        _write_df(out_root / "failed_orb_diagnostic.csv", pd.DataFrame([{"status": "no_failed_orb_trades"}]))
        _write_md(out_root / "failed_orb_diagnostic.md", "Failed ORB diagnostic (train/test windows)", [("Status", pd.DataFrame([{"status": "no_failed_orb_trades"}]))])

    # Dump metadata for traceability.
    meta = {
        "symbol": symbol,
        "asset": str(args.asset),
        "start": str(args.start),
        "end": str(args.end),
        "roots": [r.root.as_posix() for r in runs],
    }
    (out_root / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

