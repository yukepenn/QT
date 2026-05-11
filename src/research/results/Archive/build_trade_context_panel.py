"""
Build aggregated trade-context panel outputs from curated Layer3 summaries (research-only).

Does not read or commit row-level trades. Use --aggregate-only (default).
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pandas as pd


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "UNKNOWN"


def _parse_list(s: str) -> list[str]:
    return [x.strip() for x in str(s).split(",") if x.strip()]


def run_build(
    *,
    complete_smoke_root: Path,
    expanded_stability_root: Path,
    output_root: Path,
    profiles: list[str],
    windows: list[str],
    aggregate_only: bool = True,
    allow_local_detailed_inputs: str = "false",
) -> int:
    smoke = Path(complete_smoke_root)
    exp = Path(expanded_stability_root)
    out = Path(output_root)
    out.mkdir(parents=True, exist_ok=True)

    win = pd.read_csv(smoke / "complete_profile_window_summary.csv")
    cand = pd.read_csv(smoke / "complete_candidate_contribution.csv")
    exr = pd.read_csv(smoke / "complete_exit_reason_summary.csv")
    tnum = pd.read_csv(smoke / "complete_trade_number_summary.csv")
    monthly = pd.read_csv(smoke / "complete_monthly_summary.csv")
    quarterly = pd.read_csv(smoke / "complete_quarterly_summary.csv")

    win = win[win["profile_id"].isin(profiles) & win["window"].isin(windows)]
    cand = cand[cand["profile_id"].isin(profiles) & cand["window"].isin(windows)]
    exr = exr[exr["profile_id"].isin(profiles) & exr["window"].isin(windows)]
    tnum = tnum[tnum["profile_id"].isin(profiles) & tnum["window"].isin(windows)]
    monthly = monthly[monthly["profile_id"].isin(profiles) & monthly["window"].isin(windows)]
    quarterly = quarterly[quarterly["profile_id"].isin(profiles) & quarterly["window"].isin(windows)]

    avail_rows = [
        {
            "field_group": "window_metrics",
            "field_name": "total_r",
            "source_csv": "complete_profile_window_summary.csv",
            "aggregation": "profile x window",
            "status": "AVAILABLE",
        },
        {
            "field_group": "window_metrics",
            "field_name": "trade_1_total_r / trade_2_total_r",
            "source_csv": "complete_profile_window_summary.csv",
            "aggregation": "profile x window",
            "status": "AVAILABLE",
        },
        {
            "field_group": "candidate",
            "field_name": "candidate_id total_r share",
            "source_csv": "complete_candidate_contribution.csv",
            "aggregation": "profile x window x candidate",
            "status": "AVAILABLE",
        },
        {
            "field_group": "exit",
            "field_name": "exit_reason share",
            "source_csv": "complete_exit_reason_summary.csv",
            "aggregation": "profile x window x exit_reason",
            "status": "AVAILABLE",
        },
        {
            "field_group": "trade_number",
            "field_name": "trade_number_of_day total_r",
            "source_csv": "complete_trade_number_summary.csv",
            "aggregation": "profile x window x trade_number",
            "status": "AVAILABLE",
        },
        {
            "field_group": "temporal",
            "field_name": "monthly total_r",
            "source_csv": "complete_monthly_summary.csv",
            "aggregation": "profile x window x month",
            "status": "AVAILABLE",
        },
        {
            "field_group": "temporal",
            "field_name": "quarterly total_r",
            "source_csv": "complete_quarterly_summary.csv",
            "aggregation": "profile x window x quarter",
            "status": "AVAILABLE",
        },
    ]
    pd.DataFrame(avail_rows).to_csv(out / "trade_context_available_fields.csv", index=False)

    missing_rows = [
        {
            "column_name": "trade_id",
            "required_or_optional": "required",
            "reason": "row-level trades not in curated smoke CSVs",
            "remediation": "REQUIRES_LOCAL_DETAILED_REPLAY: load local Layer3 run trades.csv per profile/window",
        },
        {
            "column_name": "entry_ts_utc / exit_ts_utc / bars_held / risk_per_share",
            "required_or_optional": "required",
            "reason": "not in complete_* summaries",
            "remediation": "REQUIRES_LOCAL_DETAILED_REPLAY",
        },
        {
            "column_name": "pa_regime_label_* / pa_trade_mode_* / trend_score_* / vwap_cross_count_*",
            "required_or_optional": "optional",
            "reason": "need bar-level merge at entry from FeatureStore / enriched trades",
            "remediation": "REQUIRES_LOCAL_DETAILED_REPLAY or offline enrich step (not committed)",
        },
        {
            "column_name": "market_context_label (trade-level)",
            "required_or_optional": "optional",
            "reason": "expanded stability has quarterly/monthly QQQ labels; trade-level needs session join",
            "remediation": "join session_date to market_context_monthly.csv in local pipeline",
        },
    ]
    pd.DataFrame(missing_rows).to_csv(out / "trade_context_missing_inputs.csv", index=False)

    fa = win[win["window"] == "full_available"][["profile_id", "total_r", "trades", "max_drawdown_r"]].rename(
        columns={"total_r": "full_total_r", "trades": "full_trades", "max_drawdown_r": "full_max_dd_r"}
    )
    by_profile = win.groupby("profile_id", as_index=False).agg(
        sum_total_r_window=("total_r", "sum"),
        mean_total_r_window=("total_r", "mean"),
        sum_trades=("trades", "sum"),
    )
    by_profile = by_profile.merge(fa, on="profile_id", how="left")
    by_profile.to_csv(out / "trade_context_panel_aggregated_by_profile.csv", index=False)

    win.to_csv(out / "trade_context_panel_aggregated_by_window.csv", index=False)
    monthly.to_csv(out / "trade_context_panel_aggregated_by_period.csv", index=False)
    exr.to_csv(out / "trade_context_panel_aggregated_by_exit_reason.csv", index=False)
    tnum.to_csv(out / "trade_context_panel_aggregated_by_trade_number.csv", index=False)

    mctx_path = exp / "market_context_labels.csv"
    if mctx_path.is_file():
        pd.read_csv(mctx_path).to_csv(out / "trade_context_panel_aggregated_by_market_context.csv", index=False)
    else:
        pd.DataFrame([{"note": "market_context_labels.csv missing", "status": "SKIPPED"}]).to_csv(
            out / "trade_context_panel_aggregated_by_market_context.csv", index=False
        )

    manifest = pd.DataFrame(
        [
            {
                "phase": "build_trade_context_panel",
                "git_tip": _git_head(),
                "complete_smoke_root": str(smoke.as_posix()),
                "expanded_stability_root": str(exp.as_posix()),
                "output_root": str(out.as_posix()),
                "aggregate_only": str(bool(aggregate_only)),
                "allow_local_detailed_inputs": str(allow_local_detailed_inputs).lower(),
                "row_level_panel_committed": "no",
                "notes": "Aggregates only; row-level trade_context_panel.csv intentionally not produced for git",
            }
        ]
    )
    manifest.to_csv(out / "trade_context_build_manifest.csv", index=False)

    summary_lines = [
        "# trade_context_panel_summary",
        "",
        "## Policy",
        "- **Champion v0** summaries only; **no** row-level trade tape committed.",
        "- See `trade_context_missing_inputs.csv` for columns that need **local-only** replay + enrich.",
        "",
        "## Outputs",
        "- `trade_context_available_fields.csv` — fields derivable from curated `complete_*` tables.",
        "- `trade_context_panel_aggregated_by_*.csv` — window / period / exit / trade# / market-context (if present).",
        "",
        "## Future local-only command draft (not executed here)",
        "```text",
        "python -m src.research.fixed_profile_oow postprocess --runs-root <local_layer3_runs_root> --profiles ...",
        "# then offline merge trades with FeatureStore columns into trade_context_panel row-level (local disk only)",
        "```",
        "",
    ]
    (out / "trade_context_panel_summary.md").write_text("\n".join(summary_lines), encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build trade-context panel aggregates (no row-level commit).")
    p.add_argument("--complete-smoke-root", required=True)
    p.add_argument("--expanded-stability-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--profiles", default="pa_only_mtp1_meta,pa_gap_mtp2_meta,primary_mtp2_meta")
    p.add_argument("--windows", default="early_oow,insample_ref,late_oow,full_available")
    p.add_argument("--aggregate-only", action="store_true", default=True)
    p.add_argument("--allow-local-detailed-inputs", type=str, default="false")
    args = p.parse_args(argv)
    return run_build(
        complete_smoke_root=Path(args.complete_smoke_root),
        expanded_stability_root=Path(args.expanded_stability_root),
        output_root=Path(args.output_root),
        profiles=_parse_list(args.profiles),
        windows=_parse_list(args.windows),
        aggregate_only=bool(args.aggregate_only),
        allow_local_detailed_inputs=str(args.allow_local_detailed_inputs),
    )


if __name__ == "__main__":
    raise SystemExit(main())
