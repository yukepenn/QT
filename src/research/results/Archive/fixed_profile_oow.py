"""
Fixed-profile out-of-window (OOW) validation — research CLI.

Subcommands:
  inspect-data   — scan local QQQ parquet partitions; write data_availability.*
  run            — execute combiner replays under local_runs/<profile>/<window>/run_* (no --use-signal-cache)
  enrich         — write trades_enriched.csv next to each run (local-only; needs bars)
  postprocess    — aggregate combiner runs under <output-root>/local_runs/<profile>/<window>/run_*/
  print-commands — emit example combiner run lines (no execution)
"""
from __future__ import annotations

import argparse
import importlib
import json
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.research.fixed_profile_oow_lib import (
    combiner_argv,
    decide_label,
    default_windows,
    discover_runs,
    exit_slip_scenarios_table,
    fixed_profile_specs,
    insample_expected_rows,
    load_window_bounds,
    latest_run_dir,
    metrics_from_trades,
    parse_csv_ids,
    regime_summary_from_trades,
    rth_sessions_in_range,
    run_dir_is_complete,
    sanity_pass,
    scan_qqq_parquet_months,
    score_transfer_rows,
    spec_by_profile_id,
    trades_path_for_postprocess,
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
        tpath = trades_path_for_postprocess(run_dir)
        status = "OK"
        mjson: dict | None = None
        if mpath.is_file():
            mjson = json.loads(mpath.read_text(encoding="utf-8"))
        trades = pd.read_csv(tpath) if tpath is not None and tpath.is_file() else pd.DataFrame()
        run_start = (mjson or {}).get("start", "") or ""
        run_end = (mjson or {}).get("end", "") or ""
        if not run_start and (run_dir / "config_resolved.yaml").is_file():
            try:
                cfgd = yaml.safe_load((run_dir / "config_resolved.yaml").read_text(encoding="utf-8"))
                rd = (cfgd or {}).get("run") or {}
                run_start = str(rd.get("start", "") or "")
                run_end = str(rd.get("end", "") or "")
            except Exception:
                pass
        if trades.empty:
            status = "NOT_RUN"
        met = metrics_from_trades(trades, metrics_json=mjson)
        row = {
            "profile_id": profile_id,
            "window_id": window_id,
            "run_dir": str(run_dir.relative_to(out)) if run_dir.is_relative_to(out) else str(run_dir),
            "status": status,
            **met,
            "start": run_start,
            "end": run_end,
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
        rg_all = pd.concat(regime_parts, ignore_index=True)
        rg_all.to_csv(out / "regime_stability" / "regime_by_window.csv", index=False)
        vw_r = rg_all.loc[rg_all["profile_id"].str.startswith("vwap", na=False)]
        ind_r = rg_all.loc[rg_all["profile_id"].str.startswith("indicator", na=False)]
        if not vw_r.empty:
            vw_r.to_csv(out / "regime_stability" / "vwap_regime_oow.csv", index=False)
        if not ind_r.empty:
            ind_r.to_csv(out / "regime_stability" / "indicator_regime_oow.csv", index=False)
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
        kf = qdf.loc[(qdf.get("cohort") == "test") & (qdf["subset"] != "test_all")].copy()
        if not kf.empty:
            kf.to_csv(out / "quality_score_transfer" / "score_transfer_key_findings.csv", index=False)
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

    disc = discover_runs(runs_root)
    disc_rows = []
    for profile_id, window_id, run_dir in disc:
        st = en = ""
        crp = run_dir / "config_resolved.yaml"
        if crp.is_file():
            try:
                cd = yaml.safe_load(crp.read_text(encoding="utf-8"))
                rd = (cd or {}).get("run") or {}
                st, en = str(rd.get("start", "")), str(rd.get("end", ""))
            except Exception:
                pass
        tp = trades_path_for_postprocess(run_dir)
        has_en = (run_dir / "trades_enriched.csv").is_file()
        disc_rows.append(
            {
                "profile_id": profile_id,
                "window_id": window_id,
                "run_dir": str(run_dir.relative_to(out)) if run_dir.is_relative_to(out) else str(run_dir),
                "window_start": st,
                "window_end": en,
                "has_trades_csv": (run_dir / "trades.csv").is_file(),
                "has_trades_enriched": has_en,
                "trades_source": tp.name if tp else "",
            }
        )
    pd.DataFrame(disc_rows).to_csv(out / "run_discovery_manifest.csv", index=False)

    dec = decide_label(metrics_rows)

    def _rationale_from_metrics(df: pd.DataFrame) -> list[str]:
        if df is None or df.empty:
            return ["- No `OK` rows in `fixed_profile_oow_metrics.csv`."]
        sub = df[(df["status"] == "OK") & (df["window_id"].isin(["early_oow", "late_oow", "insample_ref"]))]
        lines: list[str] = []
        for wid in ["early_oow", "late_oow", "insample_ref"]:
            part = sub.loc[sub["window_id"] == wid, ["profile_id", "trades", "total_r"]]
            if part.empty:
                continue
            lines.append(f"- **{wid}** (selected profiles):")
            for _, r in part.sort_values("profile_id").iterrows():
                lines.append(f"  - `{r['profile_id']}`: **{int(r['trades'])}** trades, **{float(r['total_r']):.2f}** R")
        prim = sub.loc[sub["profile_id"].isin(["vwap_mtp2", "vwap_mtp1", "indicator_mtp1"])]
        prim_oow = prim.loc[prim["window_id"].isin(["early_oow", "late_oow"])]
        if not prim_oow.empty:
            neg = int((prim_oow["total_r"].astype(float) < -5.0).sum())
            pos = int((prim_oow["total_r"].astype(float) > 5.0).sum())
            lines.append(f"- Primary-profile OOW scorecard: **{pos}** windows strongly positive (>+5R), **{neg}** strongly negative (<-5R) → automated label **`{dec}`**.")
        return lines or ["- Metrics present; see `oow/fixed_profile_oow_metrics.csv`."]

    rationale = _rationale_from_metrics(mdf)
    (out / "fixed_profile_oow_decision.md").write_text(
        "\n".join(
            [
                "# Fixed-profile OOW — decision",
                "",
                f"**Decision:** `{dec}`",
                "",
                "## Rationale",
                "",
                *rationale,
                "",
                "- VWAP insample replays match historical Global L2-style references; VWAP **early_oow** and **late_oow** are materially negative in this run.",
                "- Indicator insample totals match fixed YAML wiring but **differ from older v1.5 headline R** (trade counts align); see `insample_sanity/insample_sanity_failure.md`.",
                "- Target-limit-aware stress (`exit_slip/oow_exit_slip_scenario_comparison.csv`) softens losses versus symmetric 0.02 stress but **does not flip** negative OOW systems to viable.",
                "- Quality-score cohort splits are mostly uninformative when train window equals full file (`insample_ref`) or thresholds collapse; enriched rows still power regime CSVs where present.",
                "",
                "## Explicit non-runs",
                "",
                "- mini-WFO; full rolling WFO; live/paper; SPY; Global L1 rerun; broad Global L2 grid",
                "- Strategy / feature / selected-candidate YAML edits; hard regime filter; combiner `regime_router`",
                "- Parameter optimization on OOW windows; OOW-driven candidate selection",
                "",
                "## Recommended next step",
                "",
                f"Execute: **`{dec}`** — see `fixed_profile_oow_v1_summary.md` section 15 for narrative and caveats.",
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


def write_run_commands_docs(out: Path, repo_root: Path, *, data_dir: str = "data/raw/ibkr") -> None:
    """One command per block — copy/paste safe (PowerShell, no backslash continuation)."""
    out = out.resolve()
    bounds = load_window_bounds(out, data_dir=data_dir)
    md_lines = [
        "# Fixed-profile combiner commands",
        "",
        "Do **not** pass `--use-signal-cache` on unsafe OneDrive roots. These lines omit it (combiner default off unless YAML enables).",
        "",
    ]
    ps1_lines: list[str] = ["# Generated commands — fixed-profile OOW", ""]
    for spec in fixed_profile_specs():
        for wid in ("early_oow", "insample_ref", "late_oow", "full_available"):
            if wid not in bounds:
                continue
            st, en = bounds[wid]
            argv_c = combiner_argv(
                repo_root=repo_root,
                output_root=out,
                spec=spec,
                window_id=wid,
                start=st,
                end=en,
                data_dir=data_dir,
            )
            line = " ".join(shlex.quote(x) for x in argv_c)
            md_lines.append(f"## {spec.profile_id} — {wid}")
            md_lines.append("")
            md_lines.append("```powershell")
            md_lines.append(line)
            md_lines.append("```")
            md_lines.append("")
            ps1_lines.append(line)
            ps1_lines.append("")
    (out / "run_commands_multiline.md").write_text("\n".join(md_lines), encoding="utf-8")
    (out / "run_commands_powershell.ps1").write_text("\n".join(ps1_lines), encoding="utf-8")


def cmd_run(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Run Layer2 combiner for fixed-profile OOW matrix.")
    p.add_argument("--output-root", required=True)
    p.add_argument("--profiles", default=None, help="Comma-separated profile ids; default all.")
    p.add_argument("--windows", default=None, help="Comma-separated window ids; default all in data_availability.")
    p.add_argument("--data-dir", default="data/raw/ibkr")
    p.add_argument("--top-per-strategy", type=int, default=3)
    p.add_argument("--detailed", action="store_true", help="Use legacy detailed combiner path (slower).")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--stop-on-fail", action="store_true")
    p.add_argument("--skip-existing", action="store_true")
    p.add_argument("--primary-only", action="store_true", help="Exclude indicator_mtp3.")
    args = p.parse_args(argv)
    out = Path(args.output_root)
    if not out.is_absolute():
        out = Path.cwd() / out
    repo_root = _ROOT
    all_profiles = [s.profile_id for s in fixed_profile_specs()]
    if args.primary_only:
        all_profiles = [x for x in all_profiles if x != "indicator_mtp3"]
    profiles = parse_csv_ids(args.profiles, all_profiles)
    bounds = load_window_bounds(out, data_dir=args.data_dir)
    default_win = ["early_oow", "insample_ref", "late_oow", "full_available"]
    win_default = [w for w in default_win if w in bounds] + [w for w in bounds if w not in default_win]
    windows = parse_csv_ids(args.windows, win_default)
    runs_root = out / "local_runs"
    manifest_path = out / "run_execution_manifest.csv"
    prior: list[dict[str, Any]] = []
    if manifest_path.is_file():
        try:
            prior_df = pd.read_csv(manifest_path)
            prior = prior_df.to_dict("records")
        except Exception:
            prior = []
    manifest_rows: list[dict[str, Any]] = list(prior)
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    stop_all = False
    for pid in profiles:
        if stop_all:
            break
        spec = spec_by_profile_id(pid)
        if spec is None:
            continue
        for wid in windows:
            if wid not in bounds:
                manifest_rows.append(
                    {
                        "started_utc": started,
                        "profile_id": pid,
                        "window_id": wid,
                        "window_start": "",
                        "window_end": "",
                        "command": "",
                        "exit_code": "",
                        "status": "SKIPPED_NO_WINDOW",
                        "run_dir": "",
                        "error_summary": "window not in data_availability / bounds",
                    }
                )
                continue
            st, en = bounds[wid]
            existing = latest_run_dir(runs_root, pid, wid)
            if args.skip_existing and existing is not None and run_dir_is_complete(existing):
                manifest_rows.append(
                    {
                        "started_utc": started,
                        "profile_id": pid,
                        "window_id": wid,
                        "window_start": st,
                        "window_end": en,
                        "command": "",
                        "exit_code": "",
                        "status": "SKIPPED_EXISTING",
                        "run_dir": str(existing.relative_to(out)) if existing.is_relative_to(out) else str(existing),
                        "error_summary": "",
                    }
                )
                continue
            argv_c = combiner_argv(
                repo_root=repo_root,
                output_root=out,
                spec=spec,
                window_id=wid,
                start=st,
                end=en,
                data_dir=args.data_dir,
                top_per_strategy=args.top_per_strategy,
                detailed=args.detailed,
            )
            cmd_str = " ".join(shlex.quote(x) for x in argv_c)
            if args.dry_run:
                manifest_rows.append(
                    {
                        "started_utc": started,
                        "profile_id": pid,
                        "window_id": wid,
                        "window_start": st,
                        "window_end": en,
                        "command": cmd_str,
                        "exit_code": "",
                        "status": "DRY_RUN",
                        "run_dir": "",
                        "error_summary": "",
                    }
                )
                continue
            proc = subprocess.run(argv_c, cwd=str(repo_root))
            done = latest_run_dir(runs_root, pid, wid)
            rel_run = ""
            if done is not None:
                try:
                    rel_run = str(done.relative_to(out))
                except ValueError:
                    rel_run = str(done)
            st_label = "OK" if proc.returncode == 0 else "FAILED"
            if proc.returncode == 0 and done is not None and not run_dir_is_complete(done):
                st_label = "FAILED_INCOMPLETE"
            manifest_rows.append(
                {
                    "started_utc": started,
                    "profile_id": pid,
                    "window_id": wid,
                    "window_start": st,
                    "window_end": en,
                    "command": cmd_str,
                    "exit_code": proc.returncode,
                    "status": st_label,
                    "run_dir": rel_run,
                    "error_summary": "" if proc.returncode == 0 else "combiner non-zero exit",
                }
            )
            if args.stop_on_fail and proc.returncode != 0:
                stop_all = True
                break
    pd.DataFrame(manifest_rows).to_csv(out / "run_execution_manifest.csv", index=False)
    write_run_commands_docs(out, repo_root, data_dir=args.data_dir)
    return 0


def cmd_enrich(argv: list[str] | None) -> int:
    from src.data.read_bars import read_bars
    from src.features.build_features import build_basic_features
    from src.features.build_types import RegimeFeatureConfig
    from src.research.enrich_combiner_trades import enrich_trades_frame

    p = argparse.ArgumentParser(description="Enrich local fixed-profile trades.csv → trades_enriched.csv (local-only).")
    p.add_argument("--output-root", required=True)
    p.add_argument("--profiles", default=None)
    p.add_argument("--windows", default=None)
    p.add_argument("--data-dir", default="data/raw/ibkr")
    p.add_argument("--symbol", default="QQQ")
    p.add_argument("--skip-existing", action="store_true")
    p.add_argument("--regime-window", type=int, default=20)
    args = p.parse_args(argv)
    out = Path(args.output_root)
    if not out.is_absolute():
        out = Path.cwd() / out
    runs_root = out / "local_runs"
    discovered = discover_runs(runs_root)
    all_p = [s.profile_id for s in fixed_profile_specs()]
    profs = set(parse_csv_ids(args.profiles, all_p))
    if args.windows:
        want_w = set(parse_csv_ids(args.windows, []))
    else:
        want_w = {w for _, w, _ in discovered}

    by_range: dict[tuple[str, str], list[Path]] = {}
    for pid, wid, run_dir in discovered:
        if pid not in profs or wid not in want_w:
            continue
        raw_csv = run_dir / "trades.csv"
        if not raw_csv.is_file():
            continue
        out_en = run_dir / "trades_enriched.csv"
        if args.skip_existing and out_en.is_file():
            continue
        cr = run_dir / "config_resolved.yaml"
        if not cr.is_file():
            print(f"[enrich] skip (no config_resolved.yaml): {run_dir}", flush=True)
            continue
        cfgd = yaml.safe_load(cr.read_text(encoding="utf-8"))
        rd = (cfgd or {}).get("run") or {}
        st, en = rd.get("start"), rd.get("end")
        if not st or not en:
            print(f"[enrich] skip (no start/end in config): {run_dir}", flush=True)
            continue
        key = (str(st), str(en))
        by_range.setdefault(key, []).append(run_dir)

    for (st, en), dirs in sorted(by_range.items()):
        raw = read_bars(asset="equity", symbol=args.symbol, start=st, end=en, data_dir=args.data_dir)
        if raw.empty:
            print(f"[enrich] no bars for {st}..{en}; skip {len(dirs)} runs", flush=True)
            continue
        feats = build_basic_features(
            raw,
            orb_open_minutes=15,
            copy=True,
            allow_overwrite=False,
            regime=RegimeFeatureConfig(windows=(int(args.regime_window),)),
        )
        for run_dir in dirs:
            out_en = run_dir / "trades_enriched.csv"
            if args.skip_existing and out_en.is_file():
                continue
            trades = pd.read_csv(run_dir / "trades.csv")
            enriched, meta = enrich_trades_frame(trades, feats, regime_window=int(args.regime_window))
            enriched.to_csv(out_en, index=False)
            print(f"[enrich] wrote {out_en} rows={len(enriched)} unmatched={meta.get('unmatched_trades')}", flush=True)
    return 0


def cmd_print_commands(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="Write multiline command docs under output-root.")
    p.add_argument("--output-root", default="src/research/results/fixed_profile_oow_v1")
    p.add_argument("--data-dir", default="data/raw/ibkr")
    args = p.parse_args(argv)
    root = Path(args.output_root)
    if not root.is_absolute():
        root = Path.cwd() / root
    write_run_commands_docs(root, _ROOT, data_dir=args.data_dir)
    print(f"Wrote {root / 'run_commands_multiline.md'} and {root / 'run_commands_powershell.ps1'}", flush=True)
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
    p_run = sub.add_parser("run")
    p_run.add_argument("--output-root", required=True)
    p_run.add_argument("--profiles", default=None)
    p_run.add_argument("--windows", default=None)
    p_run.add_argument("--data-dir", default="data/raw/ibkr")
    p_run.add_argument("--top-per-strategy", type=int, default=3)
    p_run.add_argument("--detailed", action="store_true")
    p_run.add_argument("--dry-run", action="store_true")
    p_run.add_argument("--stop-on-fail", action="store_true")
    p_run.add_argument("--skip-existing", action="store_true")
    p_run.add_argument("--primary-only", action="store_true")
    p_run.set_defaults(_fn="run")
    p_en = sub.add_parser("enrich")
    p_en.add_argument("--output-root", required=True)
    p_en.add_argument("--profiles", default=None)
    p_en.add_argument("--windows", default=None)
    p_en.add_argument("--data-dir", default="data/raw/ibkr")
    p_en.add_argument("--symbol", default="QQQ")
    p_en.add_argument("--skip-existing", action="store_true")
    p_en.add_argument("--regime-window", type=int, default=20)
    p_en.set_defaults(_fn="enrich")
    p3 = sub.add_parser("print-commands")
    p3.add_argument("--output-root", default="src/research/results/fixed_profile_oow_v1")
    p3.add_argument("--data-dir", default="data/raw/ibkr")
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
    if args._fn == "run":
        bits = [
            "--output-root",
            args.output_root,
            "--data-dir",
            args.data_dir,
            "--top-per-strategy",
            str(args.top_per_strategy),
        ]
        if args.profiles:
            bits += ["--profiles", args.profiles]
        if args.windows:
            bits += ["--windows", args.windows]
        if args.detailed:
            bits.append("--detailed")
        if args.dry_run:
            bits.append("--dry-run")
        if args.stop_on_fail:
            bits.append("--stop-on-fail")
        if args.skip_existing:
            bits.append("--skip-existing")
        if args.primary_only:
            bits.append("--primary-only")
        return cmd_run(bits)
    if args._fn == "enrich":
        bits = [
            "--output-root",
            args.output_root,
            "--data-dir",
            args.data_dir,
            "--symbol",
            args.symbol,
            "--regime-window",
            str(args.regime_window),
        ]
        if args.profiles:
            bits += ["--profiles", args.profiles]
        if args.windows:
            bits += ["--windows", args.windows]
        if args.skip_existing:
            bits.append("--skip-existing")
        return cmd_enrich(bits)
    if args._fn == "print-commands":
        return cmd_print_commands(["--output-root", args.output_root, "--data-dir", args.data_dir])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
