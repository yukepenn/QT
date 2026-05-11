# Mini-WFO selection audit (train-only)

This audit explains why the frozen system was selected **using train only**.

## Selected system (train-selected)

- candidate_set: **gap_only**
- candidate_ids_json: `["MINIWFO_GAP_ACCEPTANCE_FAILURE_001"]`
- train_trades: 129 train_total_r: 20.00108438327635 train_pf_r: 1.3385580372273052 train_maxDD_r: -6.023748222814444

## Systems considered (behavior-unique table → eligibility)

 unique_rank candidate_set  top_per_strategy  max_trades_per_day  daily_max_loss_r  cooldown_after_loss_minutes   priority_policy                     candidate_ids_json  train_trades  train_total_r  train_profit_factor_r  train_max_drawdown_r train_slip_0_02_total_r  eligible        rejection_reasons
          -1      gap_only                 1                   1              -1.5                            0 metadata_priority ["MINIWFO_GAP_ACCEPTANCE_FAILURE_001"]           129      20.001084               1.338558             -6.023748                    None     False missing_cost_stress_0_02

## Key question

Did mini-WFO select a narrow candidate_set because it was truly best on train, or because filters eliminated broader systems?

- behavior_unique_rows_available: **1**
- eligible_rows_after_filters: **0**

