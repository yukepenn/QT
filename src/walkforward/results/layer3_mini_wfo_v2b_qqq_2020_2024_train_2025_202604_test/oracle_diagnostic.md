# ORACLE / LOOKAHEAD DIAGNOSTIC ONLY

**NOT SELECTABLE.** This is a diagnostic that evaluates train-derived candidate systems on the held-out test window.

- evaluated_top_n: **6**
- test_window: **2025-01-01 → 2026-04-30**

                 rank_type  candidate_set  top_per_strategy  max_trades_per_day  daily_max_loss_r  cooldown   priority_policy                                                            candidate_ids  train_total_r  train_pf_r  train_maxdd_r  train_0_02_total_r  test_total_r  test_pf_r  test_maxdd_r  test_0_02_total_r                                           interpretation
            selected_train     failed_gap               1.0                 1.0              -1.5       0.0 metadata_priority         ["MINIWFO_FAILED_ORB_001", "MINIWFO_GAP_ACCEPTANCE_FAILURE_001"]            NaN         NaN            NaN                 NaN     48.191527   1.153688    -14.752563                NaN ORACLE (LOOKAHEAD): evaluated on test; never selectable.
  oracle_best_test_total_r prior_day_only               2.0                 2.0              -1.5       0.0 metadata_priority ["MINIWFO_PRIOR_DAY_LEVEL_TRAP_001", "MINIWFO_PRIOR_DAY_LEVEL_TRAP_002"]            NaN         NaN            NaN           34.184445      5.300391        NaN     -7.495699           4.317455 ORACLE (LOOKAHEAD): evaluated on test; never selectable.
     oracle_best_test_pf_r            NaN               NaN                 NaN               NaN       NaN               NaN                                                                      NaN            NaN         NaN            NaN                 NaN           NaN        NaN           NaN                NaN                                                      NaN
oracle_best_test_cost_0_02 prior_day_only               2.0                 2.0              -1.5       0.0 metadata_priority ["MINIWFO_PRIOR_DAY_LEVEL_TRAP_001", "MINIWFO_PRIOR_DAY_LEVEL_TRAP_002"]            NaN         NaN            NaN           34.184445      4.317455        NaN     -7.847839           4.317455 ORACLE (LOOKAHEAD): evaluated on test; never selectable.

