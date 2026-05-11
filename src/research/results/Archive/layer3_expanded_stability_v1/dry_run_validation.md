# dry_run_validation

- trading_rerun: **no**
- skip_detailed_replay: **True**
- profiles: `pa_only_mtp1_meta,pa_gap_mtp2_meta,primary_mtp2_meta,pa_gap_mtp1_meta,pa_only_mtp2_meta`
- weak_periods: `2025Q1,2022Q4,2023Q3`

## Checks
                                                    check  status
                       smoke:complete_monthly_summary.csv      OK
                     smoke:complete_quarterly_summary.csv      OK
                smoke:complete_profile_window_summary.csv      OK
                  smoke:complete_exit_slip_comparison.csv      OK
                smoke:complete_candidate_contribution.csv      OK
                   smoke:complete_exit_reason_summary.csv      OK
                design:expanded_stability_gate_design.csv      OK
                     planned_output:baseline_inventory.md PLANNED
                              planned_output:run_plan.csv PLANNED
                planned_output:run_execution_manifest.csv PLANNED
      planned_output:run_execution_manifest_sanitized.csv PLANNED
                    planned_output:dry_run_validation.csv PLANNED
                     planned_output:dry_run_validation.md PLANNED
             planned_output:profile_monthly_stability.csv PLANNED
           planned_output:profile_quarterly_stability.csv PLANNED
                planned_output:rolling_3month_summary.csv PLANNED
                planned_output:market_context_monthly.csv PLANNED
              planned_output:market_context_quarterly.csv PLANNED
                 planned_output:market_context_labels.csv PLANNED
                   planned_output:weak_period_context.csv PLANNED
               planned_output:weak_period_profile_pnl.csv PLANNED
               planned_output:weak_period_exit_reason.csv PLANNED
    planned_output:weak_period_candidate_contribution.csv PLANNED
             planned_output:weak_period_interpretation.md PLANNED
                 planned_output:cost_stress_by_period.csv PLANNED
                planned_output:exit_mechanics_summary.csv PLANNED
      planned_output:candidate_contribution_stability.csv PLANNED
       planned_output:expanded_stability_gate_results.csv PLANNED
         planned_output:expanded_stability_risk_flags.csv PLANNED
     planned_output:layer3_expanded_stability_decision.md PLANNED
      planned_output:layer3_expanded_stability_summary.md PLANNED
planned_output:layer3_expanded_stability_key_findings.csv PLANNED
                  planned_output:CHATGPT_REVIEW_BUNDLE.md PLANNED
                            planned_output:SOURCE_MAP.csv PLANNED
                   planned_output:chatgpt_key_metrics.csv PLANNED
