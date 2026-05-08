# Mini-WFO selection audit (train-only)

This audit explains why the frozen system was selected **using train only**.

## Selected system (train-selected)

- candidate_set: **failed_gap**
- candidate_ids_json: `["MINIWFO_FAILED_ORB_001", "MINIWFO_GAP_ACCEPTANCE_FAILURE_001"]`
- train_trades: 787 train_total_r: 48.191527493664616 train_pf_r: 1.1536881398902417 train_maxDD_r: -14.75256316585986

## Systems considered (behavior-unique table → eligibility)

 unique_rank  candidate_set  top_per_strategy  max_trades_per_day  daily_max_loss_r  cooldown_after_loss_minutes   priority_policy                                                                                                               candidate_ids_json  train_trades  train_total_r  train_profit_factor_r  train_max_drawdown_r train_slip_0_02_total_r  eligible        rejection_reasons
          -1       gap_only                 1                   1              -1.5                            0 metadata_priority                                                                                           ["MINIWFO_GAP_ACCEPTANCE_FAILURE_001"]           320      41.051306               1.282005             -7.029883                    None     False missing_cost_stress_0_02
          -1 prior_day_only                 2                   2              -1.5                            0 metadata_priority                                                         ["MINIWFO_PRIOR_DAY_LEVEL_TRAP_001", "MINIWFO_PRIOR_DAY_LEVEL_TRAP_002"]           304       9.703063               1.054773            -18.097555                    None     False missing_cost_stress_0_02
          -1 prior_day_only                 1                   1              -1.5                            0 metadata_priority                                                                                             ["MINIWFO_PRIOR_DAY_LEVEL_TRAP_001"]           297       5.946638               1.034164            -17.319742                    None     False missing_cost_stress_0_02
          -1 prior_day_only                 2                   2              -1.5                           15 metadata_priority                                                         ["MINIWFO_PRIOR_DAY_LEVEL_TRAP_001", "MINIWFO_PRIOR_DAY_LEVEL_TRAP_002"]           301       7.337720               1.041670            -18.333827                    None     False missing_cost_stress_0_02
          -1     failed_gap                 1                   1              -1.5                            0 metadata_priority                                                                 ["MINIWFO_FAILED_ORB_001", "MINIWFO_GAP_ACCEPTANCE_FAILURE_001"]           787      48.191527               1.153688            -14.752563                    None     False missing_cost_stress_0_02
          -1     failed_gap                 2                   1              -1.5                            0 metadata_priority ["MINIWFO_FAILED_ORB_001", "MINIWFO_FAILED_ORB_002", "MINIWFO_GAP_ACCEPTANCE_FAILURE_001", "MINIWFO_GAP_ACCEPTANCE_FAILURE_002"]           788      48.173880               1.153623            -14.752563                    None     False missing_cost_stress_0_02

## Key question

Did mini-WFO select a narrow candidate_set because it was truly best on train, or because filters eliminated broader systems?

- behavior_unique_rows_available: **6**
- eligible_rows_after_filters: **0**

