"""
Fixed-profile out-of-window (OOW) validation — research CLI.

Subcommands:
  inspect-data   — scan local QQQ parquet partitions; write data_availability.*
  postprocess    — aggregate combiner runs under <output-root>/local_runs/<profile>/<window>/run_*/
  print-commands — emit example combiner run lines (no execution)
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.research.fixed_profile_oow_lib import (
    decide_label,
    default_windows,
    discover_runs,
    exit_slip_scenarios_table,
    insample_expected_rows,
    metrics_from_trades,
    regime_summary_from_trades,
    rth_sessions_in_range,
    sanity_pass,
    scan_qqq_parquet_months,
    score_transfer_rows,
    unknown_summary_from_trades,
)


def cmd_inspect_data(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Scan QQQ parquet availability.")
    p.add_argument("--output-root", required=True)
    p.add_argument("--symbol", default="QQQ")
    p.add_argument("--data-dir", default="data/raw/ibkr")
    args = p.parse_args(argv)
    out = Path(args.output_root)
    if not out.is_absolute():
        out = Path.cwd() / out
    out.mkdir(parents=True, exist_ok=True)
    first_m, last_m, detail = scan_qqq_parquet_months(symbol=args.symbol, data_dir=args.data_dir)
    first_d = str(pd.Timestamp(first_m).date()) if first_m else None
    last_d = str(pd.Timestamp(last_m).date()) if last_m else None
    wins = default_windows(first_d, last_d)
    rows = []
    for w in wins:
        n_sess = 0
        if first_d and last_d:
            n_sess = rth_sessions_in_range(symbol=args.symbol, start=w.start, end=w.end, data_dir=args.data_dir)
        rows.append(
            {
                "symbol": args.symbol,
                "asset": "equity",
                "window_id": w.window_id,
                "window_start": w.start,
                "window_end": w.end,
                "window_label": w.label,
                "rth_sessions_in_window": n_sess,
                "data_first_available": first_d or "",
                "data_last_available": last_d or "",
            }
        )
    pd.DataFrame(rows).to_csv(out / "data_availability.csv", index=False)
    if not detail.empty:
        detail.to_csv(out / "data_availability_by_year.csv", index=False)
    lines = [
        "# QQQ data availability (local parquet)",
        "",
        f"- **Symbol:** {args.symbol}",
        f"- **First month partition:** `{first_m or 'NONE'}`",
        f"- **Last month partition:** `{last_m or 'NONE'}`",
        f"- **Inferred first date:** `{first_d or 'UNKNOWN'}`",
        f"- **Inferred last date:** `{last_d or 'UNKNOWN'}`",
        "",
        "## Selected validation windows (clipped to data when possible)",
        "",
    ]
    for r in rows:
        lines.append(
            f"- **{r['window_id']}** ({r['window_label']}): `{r['window_start']}` → `{r['window_end']}` — **{r['rth_sessions_in_window']}** RTH sessions"
        )
    lines += [
        "",
        "If partitions are missing, install local `data/raw/ibkr/equity/bars_1min/symbol=QQQ/year=*/month=*/data.parquet` before running combiner replays.",
        "",
    ]
    (out / "data_availability.md").write_text("\n".join(lines), encoding="utf-8")
    return 0


def cmd_postprocess(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Postprocess fixed-profile OOW combiner runs.")
    p.add_argument("--output-root", required=True)
    p.add_argument("--runs-subdir", default="local_runs", help="Under output-root")
    p.add_argument("--taxonomy", default="src/research/results/trade_quality_router_v1/setup_taxonomy_v1.csv")
    p.add_argument(
        "--vwap-analysis-dir",
        default="src/research/results/trade_quality_router_v1/analysis/vwap_baseline_global_l2",
    )
    p.add_argument(
        "--indicator-analysis-dir",
        default="src/research/results/trade_quality_router_v1/analysis/indicator_completion_mtp1",
    )
    args = p.parse_args(argv)
    out = Path(args.output_root)
    if not out.is_absolute():
        out = Path.cwd() / out
    tax = Path(args.taxonomy)
    if not tax.is_absolute():
        tax = Path.cwd() / tax
    vwap_ad = Path(args.vwap_analysis_dir)
    if not vwap_ad.is_absolute():
        vwap_ad = Path.cwd() / vwap_ad
    ind_ad = Path(args.indicator_analysis_dir)
    if not ind_ad.is_absolute():
        ind_ad = Path.cwd() / ind_ad

    tqh = importlib.import_module("src.research.trade_quality_helpers")

    runs_root = out / args.runs_subdir
    discovered = discover_runs(runs_root)
    metrics_rows: list[dict] = []
    slip_parts: list[pd.DataFrame] = []
    q_rows: list[dict] = []
    regime_parts: list[pd.DataFrame] = []
    unknown_parts: list[pd.DataFrame] = []
    tn_parts: list[pd.DataFrame] = []

    ref_df = insample_expected_rows()
    ref_map = {r["profile_id"]: r for _, r in ref_df.iterrows()}

    for profile_id, window_id, run_dir in discovered:
        mpath = run_dir / "metrics.json"
        tpath = run_dir / "trades.csv"
        status = "OK"
        mjson: dict | None = None
        if mpath.is_file():
            mjson = json.loads(mpath.read_text(encoding="utf-8"))
        trades = pd.read_csv(tpath) if tpath.is_file() else pd.DataFrame()
        if trades.empty:
            status = "NOT_RUN"
        met = metrics_from_trades(trades, metrics_json=mjson)
        row = {
            "profile_id": profile_id,
            "window_id": window_id,
            "run_dir": str(run_dir.relative_to(out)) if run_dir.is_relative_to(out) else str(run_dir),
            "status": status,
            **met,
            "start": (mjson or {}).get("start", ""),
            "end": (mjson or {}).get("end", ""),
        }
        if window_id == "insample_ref" and profile_id in ref_map:
            rr = ref_map[profile_id]
            row["sanity_pass"] = sanity_pass(met, rr) if status == "OK" else False
        else:
            row["sanity_pass"] = ""
        metrics_rows.append(row)

        if not trades.empty:
            label = f"{profile_id}__{window_id}"
            slip_parts.append(exit_slip_scenarios_table(trades, label))
            if profile_id.startswith("vwap"):
                q_rows.extend(
                    score_transfer_rows(
                        trades,
                        taxonomy=tax,
                        analysis_dir=vwap_ad,
                        train_start="2023-01-01",
                        train_end="2024-12-31",
                        test_label=label,
                    )
                )
            elif profile_id.startswith("indicator"):
                q_rows.extend(
                    score_transfer_rows(
                        trades,
                        taxonomy=tax,
                        analysis_dir=ind_ad,
                        train_start="2023-01-01",
                        train_end="2024-12-31",
                        test_label=label,
                    )
                )
            rg = regime_summary_from_trades(trades)
            if not rg.empty:
                rg.insert(0, "window_id", window_id)
                rg.insert(0, "profile_id", profile_id)
                regime_parts.append(rg)
            uk = unknown_summary_from_trades(trades)
            if not uk.empty:
                uk.insert(0, "window_id", window_id)
                uk.insert(0, "profile_id", profile_id)
                unknown_parts.append(uk)
            tdf = trades.copy()
            if "session_date" in tdf.columns and "entry_ts_utc" in tdf.columns:
                tdf = tqh.add_prior_trade_columns(tdf)
            if "entry_trade_number_of_day" in tdf.columns:
                y = pd.to_datetime(tdf["session_date"].astype(str), errors="coerce").dt.year
                tdf["_y"] = y
                agg = tdf.groupby(["_y", "entry_trade_number_of_day"], dropna=False)["r_multiple"].sum().reset_index()
                agg.insert(0, "window_id", window_id)
                agg.insert(0, "profile_id", profile_id)
                tn_parts.append(agg)

    (out / "oow").mkdir(parents=True, exist_ok=True)
    (out / "insample_sanity").mkdir(parents=True, exist_ok=True)
    (out / "exit_slip").mkdir(parents=True, exist_ok=True)
    (out / "quality_score_transfer").mkdir(parents=True, exist_ok=True)
    (out / "regime_stability").mkdir(parents=True, exist_ok=True)
    (out / "trade_number").mkdir(parents=True, exist_ok=True)

    mdf = pd.DataFrame(metrics_rows)
    if not mdf.empty:
        mdf.to_csv(out / "oow" / "fixed_profile_oow_metrics.csv", index=False)
    else:
        mdf = pd.DataFrame(
            columns=[
                "profile_id",
                "window_id",
                "run_dir",
                "status",
                "trades",
                "sessions",
                "total_r",
                "avg_r",
                "median_r",
                "pf_r",
                "win_rate",
                "max_dd_r",
                "target_count",
                "stop_count",
                "eod_count",
                "max_hold_count",
                "trades_per_day",
                "trade_1_total_r",
                "trade_2_total_r",
                "trade_3_total_r",
                "start",
                "end",
                "sanity_pass",
            ]
        )
        mdf.to_csv(out / "oow" / "fixed_profile_oow_metrics.csv", index=False)
    if slip_parts:
        pd.concat(slip_parts, ignore_index=True).to_csv(out / "exit_slip" / "oow_exit_slip_scenario_comparison.csv", index=False)
    if regime_parts:
        pd.concat(regime_parts, ignore_index=True).to_csv(out / "regime_stability" / "regime_by_window.csv", index=False)
    if unknown_parts:
        pd.concat(unknown_parts, ignore_index=True).to_csv(out / "regime_stability" / "unknown_by_window.csv", index=False)
    if tn_parts:
        all_tn = pd.concat(tn_parts, ignore_index=True)
        all_tn.to_csv(out / "trade_number" / "trade_number_oow_metrics.csv", index=False)
        vw = all_tn.loc[all_tn["profile_id"].str.startswith("vwap")]
        ind = all_tn.loc[all_tn["profile_id"].str.startswith("indicator")]
        if not vw.empty:
            vw.to_csv(out / "trade_number" / "vwap_trade_number_oow.csv", index=False)
        if not ind.empty:
            ind.to_csv(out / "trade_number" / "indicator_trade_number_oow.csv", index=False)

    ins_rows = []
    for _, r in ref_df.iterrows():
        pid = r["profile_id"]
        sub = mdf[(mdf["profile_id"] == pid) & (mdf["window_id"] == "insample_ref")]
        if sub.empty:
            ins_rows.append({**r.to_dict(), "actual_trades": "", "actual_total_r": "", "sanity_pass": False, "status": "NOT_RUN"})
        else:
            a = sub.iloc[0].to_dict()
            ins_rows.append(
                {
                    **r.to_dict(),
                    "actual_trades": a.get("trades"),
                    "actual_total_r": a.get("total_r"),
                    "sanity_pass": a.get("sanity_pass", False),
                    "status": a.get("status"),
                }
            )
    pd.DataFrame(ins_rows).to_csv(out / "insample_sanity" / "insample_sanity_metrics.csv", index=False)
    (out / "insample_sanity" / "insample_sanity_summary.md").write_text(
        "\n".join(
            [
                "# In-sample sanity (2023–2024)",
                "",
                "Compare `actual_*` to reference economics in `insample_sanity_metrics.csv`.",
                "Tolerance: ~8% trades and ~3R total_r (see `sanity_pass` column).",
                "",
                "If all rows show `NOT_RUN`, execute combiner replays under `local_runs/<profile>/insample_ref/` then re-run `postprocess`.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    if slip_parts:
        (out / "exit_slip" / "oow_exit_slip_summary.md").write_text(
            "\n".join(
                [
                    "# OOW exit / slip overlay",
                    "",
                    "Scenarios in `oow_exit_slip_scenario_comparison.csv`: **published**, **symmetric_stress** (0.02 both legs), **target_limit_stress**, **symmetric_extreme** (0.03 warning tier).",
                    "Research overlay only — combiner simulator unchanged.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    else:
        (out / "exit_slip" / "oow_exit_slip_summary.md").write_text(
            "# OOW exit / slip overlay\n\nNo local runs yet — run combiner then `postprocess`.\n", encoding="utf-8"
        )
    if q_rows:
        qdf = pd.DataFrame(q_rows)
        qdf.to_csv(out / "quality_score_transfer" / "vwap_indicator_score_transfer.csv", index=False)
        vw_q = qdf.loc[qdf["test_label"].str.startswith("vwap", na=False)]
        ind_q = qdf.loc[qdf["test_label"].str.startswith("indicator", na=False)]
        if not vw_q.empty:
            vw_q.to_csv(out / "quality_score_transfer" / "vwap_score_transfer.csv", index=False)
        if not ind_q.empty:
            ind_q.to_csv(out / "quality_score_transfer" / "indicator_score_transfer.csv", index=False)
    (out / "quality_score_transfer" / "quality_score_transfer_summary.md").write_text(
        "\n".join(
            [
                "# Quality score transfer (OOW)",
                "",
                "Train thresholds on **2023–2024** session dates only; apply to other dates in the same trade file.",
                "**Requires** `entry_regime_label` on trades — use `enrich_combiner_trades.py` on each `trades.csv` if missing.",
                "",
                "Outputs: `vwap_score_transfer.csv`, `indicator_score_transfer.csv` (split from combined when present).",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (out / "trade_number" / "trade_number_oow_summary.md").write_text(
        "\n".join(
            [
                "# Trade-number stability (OOW)",
                "",
                "See `trade_number_oow_metrics.csv`, `vwap_trade_number_oow.csv`, `indicator_trade_number_oow.csv` when runs exist.",
                "Trade numbers are derived via `add_prior_trade_columns` when not present in raw `trades.csv`.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (out / "regime_stability" / "regime_stability_summary.md").write_text(
        "\n".join(
            [
                "# Regime / unknown stability",
                "",
                "`regime_by_window.csv` requires enriched `entry_regime_label` on trades.",
                "`unknown_by_window.csv` uses `prepare_unknown_frame` on enriched rows.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    dec = decide_label(metrics_rows)
    (out / "fixed_profile_oow_decision.md").write_text(
        "\n".join(
            [
                "# Fixed-profile OOW — decision",
                "",
                f"**Decision:** `{dec}`",
                "",
                "## Rationale",
                "",
                "- Automated label uses only rows with `status=OK` on **early_oow** + **late_oow** for primary profiles (`vwap_mtp2`, `vwap_mtp1`, `indicator_mtp1`).",
                "- If no combiner runs are present under `local_runs/`, decision defaults to **`NEED_MORE_FIXED_PROFILE_OOW`**.",
                "- Interpret human-in-the-loop using `oow/fixed_profile_oow_metrics.csv`, exit-slip tables, and trade-number CSVs.",
                "",
                "## Explicit non-runs",
                "",
                "- mini-WFO; full rolling WFO; live/paper; SPY; Global L1 rerun; broad Global L2 grid",
                "- Strategy / feature / selected-candidate YAML edits; hard regime filter; combiner `regime_router`",
                "- Parameter optimization on OOW windows; OOW-driven candidate selection",
                "",
                "## Recommended next step",
                "",
                f"Execute: **`{dec}`** (see `fixed_profile_oow_v1_summary.md` section 15 for narrative).",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (out / "oow" / "fixed_profile_oow_summary.md").write_text(
        "# Fixed-profile OOW — metrics summary\n\n"
        "Per-profile/window table: `fixed_profile_oow_metrics.csv`.\n\n"
        "Full narrative: `../fixed_profile_oow_v1_summary.md`.\n",
        encoding="utf-8",
    )
    return 0


def cmd_print_commands(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Print example combiner commands.")
    p.add_argument("--output-root", default="src/research/results/fixed_profile_oow_v1")
    args = p.parse_args(argv)
    root = Path(args.output_root)
    cr = "src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates"
    profiles = [
        ("vwap_mtp2", "configs/layer2_fixed_vwap_mtp2.yaml", "vwap_core"),
        ("vwap_mtp1", "configs/layer2_fixed_vwap_mtp1.yaml", "vwap_core"),
        ("indicator_mtp1", "configs/layer2_fixed_indicator_mtp1.yaml", "indicator_completion_core"),
        ("indicator_mtp2", "configs/layer2_fixed_indicator_mtp2.yaml", "indicator_completion_core"),
        ("indicator_mtp3", "configs/layer2_fixed_indicator_mtp3.yaml", "indicator_completion_core"),
    ]
    windows = [
        ("early_oow", "2020-01-01", "2022-12-31"),
        ("insample_ref", "2023-01-01", "2024-12-31"),
        ("late_oow", "2025-01-01", "2026-04-30"),
        ("full_available", "2020-01-01", "2026-04-30"),
    ]
    lines = [
        "# Example combiner runs (do not use `--use-signal-cache` on unsafe OneDrive roots)",
        "",
        "Adjust `--end` to your latest available QQQ date after running `inspect-data`.",
        "",
    ]
    for pid, cfg, cset in profiles:
        for wid, st, en in windows:
            lines.append(
                f"python -m src.combiner.run --candidate-root {cr} \\\n"
                f"  --config {root / cfg} --asset equity --symbol QQQ \\\n"
                f"  --start {st} --end {en} --candidate-set {cset} \\\n"
                f"  --output-root {root / 'local_runs' / pid / wid}"
            )
            lines.append("")
    print("\n".join(lines))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Fixed-profile OOW validation")
    sub = p.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("inspect-data")
    p1.add_argument("--output-root", required=True)
    p1.add_argument("--symbol", default="QQQ")
    p1.add_argument("--data-dir", default="data/raw/ibkr")
    p1.set_defaults(_fn="inspect-data")
    p2 = sub.add_parser("postprocess")
    p2.add_argument("--output-root", required=True)
    p2.add_argument("--runs-subdir", default="local_runs")
    p2.add_argument("--taxonomy", default="src/research/results/trade_quality_router_v1/setup_taxonomy_v1.csv")
    p2.add_argument("--vwap-analysis-dir", default="src/research/results/trade_quality_router_v1/analysis/vwap_baseline_global_l2")
    p2.add_argument("--indicator-analysis-dir", default="src/research/results/trade_quality_router_v1/analysis/indicator_completion_mtp1")
    p2.set_defaults(_fn="postprocess")
    p3 = sub.add_parser("print-commands")
    p3.add_argument("--output-root", default="src/research/results/fixed_profile_oow_v1")
    p3.set_defaults(_fn="print-commands")
    args = p.parse_args(argv)
    if args._fn == "inspect-data":
        return cmd_inspect_data(
            ["--output-root", args.output_root, "--symbol", args.symbol, "--data-dir", args.data_dir]
        )
    if args._fn == "postprocess":
        return cmd_postprocess(
            [
                "--output-root",
                args.output_root,
                "--runs-subdir",
                args.runs_subdir,
                "--taxonomy",
                args.taxonomy,
                "--vwap-analysis-dir",
                args.vwap_analysis_dir,
                "--indicator-analysis-dir",
                args.indicator_analysis_dir,
            ]
        )
    if args._fn == "print-commands":
        return cmd_print_commands(["--output-root", args.output_root])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
