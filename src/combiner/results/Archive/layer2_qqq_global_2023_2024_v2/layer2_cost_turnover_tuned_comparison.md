# Layer 2 tuned diagnostic comparison

**Runs (local, no signal-cache):** QQQ **2023-01-01 — 2024-12-31**, slip **0.01**, candidate root l2_core (**66** YAMLs).

| Track | Config | Combos | Sweep folder | Notes |
|-------|--------|--------|--------------|--------|
| A lower_turnover_vwap | `layer2_sweep_qqq_global_2023_2024_v2_lower_turnover_vwap.yaml` | 72 | `.../lower_turnover_vwap/sweep_20260511_012226/` | `max_trades_per_day=1`, cooldown/no_new grid |
| B family_diverse | `layer2_sweep_qqq_global_2023_2024_v2_family_diverse.yaml` | 64 | `.../family_diverse/sweep_20260511_012648/` | no VWAP buckets in grid |
| D non_vwap | `layer2_sweep_qqq_global_2023_2024_v2_non_vwap.yaml` | 80 | `.../non_vwap/sweep_20260511_013054/` | includes `non_vwap_strict_l2_core` |

**Total:** **216** combiner rows. Heavy **`sweep_*` / `top_runs/` / `cost_stress/*.csv`** under `layer2_qqq_global_2023_2024_v2_cost_turnover/` are **local-only** (not committed).

Best **combiner_score** row per result root (post-dedupe `top_unique`), with **cost stress** joined on the same `combo_id` (**0.01 / 0.02 / 0.03** incremental slip ladder).

                        label  combo_id             candidate_set                                                                                                                          candidate_ids_json  n_strategies_distinct  trades  total_r_0.01  profit_factor_0.01  max_drawdown_r_0.01  total_r_0.02  profit_factor_0.02  total_r_0.03  profit_factor_0.03  r_ret_01_to_02  r_ret_01_to_03  combiner_score  cost_adjusted_objective    decision_label
original_global_l2_top_unique       303                 vwap_core                                                                                      ["VWAP_RECLAIM_REJECT_001", "VWAP_TREND_PULLBACK_001"]                      2     337     42.203127            1.210320           -10.498071     10.558805            1.085086    -23.661208            0.969771        0.250190       -0.560651        1.320974                -0.460821 THIN_BUT_POSITIVE
          lower_turnover_vwap         1                 vwap_core                                                                                      ["VWAP_RECLAIM_REJECT_001", "VWAP_TREND_PULLBACK_001"]                      2     294     36.706513            1.231361           -15.518719     11.853404            1.116754    -20.740576            0.991452        0.322924       -0.565038        1.169087                -0.309342 THIN_BUT_POSITIVE
               family_diverse        17 indicator_completion_core ["CCI_EXTREME_SNAPBACK_001", "MACD_MOMENTUM_TURN_001", "RSI_FAILURE_SWING_001", "STOCHASTIC_OVERSOLD_CROSS_001", "SUPERTREND_ATR_FLIP_001"]                      5     502     43.545647            1.257425           -11.750381     10.987730            1.148956    -18.392329            1.053651        0.252327       -0.422369        0.349221                 0.792354 THIN_BUT_POSITIVE
                     non_vwap        33 indicator_completion_core ["CCI_EXTREME_SNAPBACK_001", "MACD_MOMENTUM_TURN_001", "RSI_FAILURE_SWING_001", "STOCHASTIC_OVERSOLD_CROSS_001", "SUPERTREND_ATR_FLIP_001"]                      5     502     43.545647            1.257425           -11.750381     10.987730            1.148956    -18.392329            1.053651        0.252327       -0.422369        0.349221                 0.792354 THIN_BUT_POSITIVE
