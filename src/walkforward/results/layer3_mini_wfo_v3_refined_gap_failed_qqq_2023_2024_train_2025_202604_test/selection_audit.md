# Mini-WFO selection audit (train-only)

This audit explains why the frozen system was selected **using train only**.

## Selected system (train-selected)

- candidate_set: **refined_failed_only**
- candidate_ids_json: `["MINIWFO_FAILED_ORB_001"]`
- train_trades: 181 train_total_r: 12.408621380938571 train_pf_r: 1.1349336264003334 train_maxDD_r: -10.538288407357072

## Systems considered (behavior-unique table → eligibility)

 unique_rank       candidate_set  top_per_strategy  max_trades_per_day  daily_max_loss_r  cooldown_after_loss_minutes   priority_policy                                                             candidate_ids_json  train_trades  train_total_r  train_profit_factor_r  train_max_drawdown_r train_slip_0_02_total_r  eligible        rejection_reasons
          -1 refined_failed_only                 1                   1              -1.5                            0 metadata_priority                                                     ["MINIWFO_FAILED_ORB_001"]           181      12.408621               1.134934            -10.538288                    None     False missing_cost_stress_0_02
          -1 refined_failed_only                 3                   1              -1.5                            0 metadata_priority ["MINIWFO_FAILED_ORB_001", "MINIWFO_FAILED_ORB_002", "MINIWFO_FAILED_ORB_003"]           182      11.390981               1.122509            -10.538288                    None     False missing_cost_stress_0_02
          -1    refined_gap_only                 1                   1              -1.5                            0 metadata_priority                                         ["MINIWFO_GAP_ACCEPTANCE_FAILURE_001"]            89       9.674573               1.281443             -6.574430                    None     False missing_cost_stress_0_02

## Key question

Did mini-WFO select a narrow candidate_set because it was truly best on train, or because filters eliminated broader systems?

- behavior_unique_rows_available: **3**
- eligible_rows_after_filters: **0**

