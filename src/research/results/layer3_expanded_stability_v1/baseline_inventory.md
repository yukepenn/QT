# baseline_inventory

- git_tip_at_run: `f4741a9557d65e54d6a47e62819ea822289bfb0a`
- design_decision: `RUN_LAYER3_EXPANDED_STABILITY` (from design bundle)
- execution: expanded stability v1 postprocess

## Source files inspected
- `NEXT_HANDOFF.md`, `PROJECT_STATUS.md` (repo)
- `src/research/results/layer3_expanded_stability_design_v1/**` (gates, labels design)
- `src/research/results/layer3_fixed_profile_smoke_complete_v1/complete_*` summaries

## Profiles included
- `pa_only_mtp1_meta`, `pa_gap_mtp2_meta`, `primary_mtp2_meta`, `pa_gap_mtp1_meta`, `pa_only_mtp2_meta`

## Profiles excluded from default
- `pa_gap_mtp1_meta`, `pa_only_mtp2_meta` (ablation / reference only)

## Weak periods planned
- 2025Q1, 2022Q4, 2023Q3 (CLI weak-period anchors)

## Market context inputs
- Local QQQ parquet under `data/raw/ibkr/equity/bars_1min/symbol=QQQ/...` when present

## Detailed local replay
- Default: **skipped** (`--skip-detailed-replay`); period-sliced exit/candidate attribution may be marked `REQUIRES_LOCAL_DETAILED_REPLAY`.

## Generated outputs
- `CHATGPT_REVIEW_BUNDLE.md`, `SOURCE_MAP.csv`, `baseline_inventory.md`, `candidate_contribution_stability.csv`, `candidate_contribution_stability.md`, `chatgpt_key_metrics.csv`, `cost_stress_by_period.csv`, `cost_stress_by_period.md`, `drawdown_duration_summary.csv`, `dry_run_validation.csv`, `dry_run_validation.md`, `exit_mechanics_summary.csv`, `exit_mechanics_summary.md`, `expanded_stability_gate_results.csv`, `expanded_stability_gate_results.md`, `expanded_stability_profile_labels.csv`, `expanded_stability_risk_flags.csv`, `expanded_stability_risk_flags.md`, `layer3_expanded_stability_artifact_validation.csv`, `layer3_expanded_stability_artifact_validation.md`, `layer3_expanded_stability_decision.md`, `layer3_expanded_stability_key_findings.csv`, `layer3_expanded_stability_summary.md`, `market_context_labels.csv`, `market_context_labels.md`, `market_context_missing_inputs.csv`, `market_context_monthly.csv`, `market_context_quarterly.csv`, `profile_monthly_stability.csv`, `profile_monthly_stability.md`, `profile_quarterly_stability.csv`, `profile_quarterly_stability.md`, `regime_context_summary.csv`, `rolling_3month_summary.csv`, `rolling_3month_summary.md`, `run_execution_manifest.csv`, `run_execution_manifest_sanitized.csv`, `run_plan.csv`, `weak_period_candidate_contribution.csv`, `weak_period_context.csv`, `weak_period_exit_reason.csv`, `weak_period_interpretation.md`, `weak_period_profile_pnl.csv`

- decision: `PROCEED_TO_PRE_WFO_STABILITY_DESIGN`
