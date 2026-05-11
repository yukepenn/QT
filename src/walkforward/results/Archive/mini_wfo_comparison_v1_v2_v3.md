# Mini-WFO comparison (v1 / v2A / v2B)

                                                                    run_id train_start  train_end test_start   test_end                                                                                                                         strategies_used selected_candidate_set                                    selected_candidate_ids  train_total_r  train_pf_r  train_maxdd_r  train_0_02_total_r  test_trades  test_total_r  test_pf  test_pf_r  test_maxdd_r  test_0_02_total_r  test_0_03_total_r worst_month  worst_month_r  positive_month_ratio  monthly_concentration_ratio decision                  warnings
                   layer3_mini_wfo_qqq_2023_2024_train_2025_202604_test_v1  2023-01-01 2024-12-31 2025-01-01 2026-04-30                                                                                  failed_orb,gap_acceptance_failure,prior_day_level_trap               gap_only                        MINIWFO_GAP_ACCEPTANCE_FAILURE_001      20.001084    1.338558      -6.023748           15.696617           89      1.306924 1.202031   1.028720    -12.263664          -1.164571          -2.307094     2025-12      -9.083297                0.6875                     0.319425  CAUTION                          
                  layer3_mini_wfo_v2a_qqq_2023_2024_train_2025_202604_test  2023-01-01 2024-12-31 2025-01-01 2026-04-30 failed_orb,gap_acceptance_failure,prior_day_level_trap,orb_retest_continuation,orb_continuation,vwap_reclaim_reject,vwap_trend_pullback               gap_only                        MINIWFO_GAP_ACCEPTANCE_FAILURE_001      20.001084    1.338558      -6.023748           15.696617           89      1.306924 1.202031   1.028720    -12.263664          -1.164571          -2.307094     2025-12      -9.083297                0.6875                     0.319425  CAUTION                          
                  layer3_mini_wfo_v2b_qqq_2020_2024_train_2025_202604_test  2020-01-01 2024-12-31 2025-01-01 2026-04-30 failed_orb,gap_acceptance_failure,prior_day_level_trap,orb_retest_continuation,orb_continuation,vwap_reclaim_reject,vwap_trend_pullback             failed_gap MINIWFO_FAILED_ORB_001,MINIWFO_GAP_ACCEPTANCE_FAILURE_001      48.191527    1.153688     -14.752563           34.184445          205     -5.920676 1.006718   0.936197    -22.880289          -8.343194         -11.139718     2025-12      -8.534961                0.4375                     0.202577     FAIL top_behavior_set=gap_only
layer3_mini_wfo_v3_refined_gap_failed_qqq_2023_2024_train_2025_202604_test  2023-01-01 2024-12-31 2025-01-01 2026-04-30                                                                                                       gap_acceptance_failure,failed_orb    refined_failed_only                                    MINIWFO_FAILED_ORB_001      12.408621    1.134934     -10.538288            8.060839          139      5.058064 1.287462   1.069631    -17.775700           3.692109           0.767036     2025-07      -5.964467                0.5000                     0.134734     PASS                          

## Summary

- **layer3_mini_wfo_qqq_2023_2024_train_2025_202604_test_v1**: set=`gap_only` test_total_r=1.3069 PF_R=1.0287 slip0.02=-1.1646 decision=CAUTION
- **layer3_mini_wfo_v2a_qqq_2023_2024_train_2025_202604_test**: set=`gap_only` test_total_r=1.3069 PF_R=1.0287 slip0.02=-1.1646 decision=CAUTION
- **layer3_mini_wfo_v2b_qqq_2020_2024_train_2025_202604_test**: set=`failed_gap` test_total_r=-5.9207 PF_R=0.9362 slip0.02=-8.3432 decision=FAIL (warnings: top_behavior_set=gap_only)
- **layer3_mini_wfo_v3_refined_gap_failed_qqq_2023_2024_train_2025_202604_test**: set=`refined_failed_only` test_total_r=5.0581 PF_R=1.0696 slip0.02=3.6921 decision=PASS

## Interpretation

- v2A did **not** improve robustness vs v1 (it still selects `gap_only`).
- v2B selected `failed_gap` but failed forward (PF_R < 1 and negative R).
- If all variants are cost-fragile or negative, full WFO remains **blocked**; next step is strategy-family refinement.

## Interpretation prompts

1. Did broader opening/trap (v2A) improve robustness vs v1?
2. Did longer training (v2B) improve robustness vs v1?
3. Did the selected candidate_set change?
4. Did any variant survive 0.02 slippage on test?

