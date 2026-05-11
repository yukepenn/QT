# ORACLE / LOOKAHEAD DIAGNOSTIC ONLY

**NOT SELECTABLE.** This is a diagnostic that evaluates train-derived candidate systems on the held-out test window.

- evaluated_top_n: **1**
- test_window: **2025-01-01 → 2026-04-30**

                 rank_type candidate_set  top_per_strategy  max_trades_per_day  daily_max_loss_r  cooldown   priority_policy                          candidate_ids  train_total_r  train_pf_r  train_maxdd_r  train_0_02_total_r  test_total_r  test_pf_r  test_maxdd_r  test_0_02_total_r                                           interpretation
            selected_train      gap_only               1.0                 1.0              -1.5       0.0 metadata_priority ["MINIWFO_GAP_ACCEPTANCE_FAILURE_001"]            NaN         NaN            NaN                 NaN     20.001084   1.338558     -6.023748                NaN ORACLE (LOOKAHEAD): evaluated on test; never selectable.
  oracle_best_test_total_r      gap_only               1.0                 1.0              -1.5       0.0 metadata_priority ["MINIWFO_GAP_ACCEPTANCE_FAILURE_001"]            NaN         NaN            NaN           15.696617      1.306924        NaN    -12.263664          -1.164571 ORACLE (LOOKAHEAD): evaluated on test; never selectable.
     oracle_best_test_pf_r           NaN               NaN                 NaN               NaN       NaN               NaN                                    NaN            NaN         NaN            NaN                 NaN           NaN        NaN           NaN                NaN                                                      NaN
oracle_best_test_cost_0_02           NaN               NaN                 NaN               NaN       NaN               NaN                                    NaN            NaN         NaN            NaN                 NaN           NaN        NaN           NaN                NaN                                                      NaN

