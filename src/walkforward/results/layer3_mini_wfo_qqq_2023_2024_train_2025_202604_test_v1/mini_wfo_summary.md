# Layer 3 Mini-WFO v1 — QQQ 2023–2024 Train / 2025–2026 Test

## 1. Purpose

Single causal mini-WFO: train-only selection, one held-out test. Not full WFO; not live-ready.

## 2. Train/test split

- Train: **2023-01-01** → **2024-12-31**
- Test: **2025-01-01** → **2026-04-30**

## 3. Strategies included

**Primary:** failed_orb, gap_acceptance_failure.
**Diagnostic:** prior_day_level_trap (optional set only).
**Excluded:** ORB_RETEST, ORB_CONTINUATION, VWAP — prior diagnosis flagged opening/trap/VWAP paths as noisy or unstable vs the gap/failed_orb core.

## 4. Train Layer 1 candidate summary

              strategy  n_candidates  best_total_r  best_pf  max_trades  worst_mdd
            failed_orb             5      9.007045 1.170188         223  -8.275178
gap_acceptance_failure             5     20.001084 1.577570         129  -6.023748
  prior_day_level_trap             1     10.837863 1.039267         134 -13.417503


## 5. Train Layer 2 selection

 behavior_rank candidate_set  top_per_strategy  max_trades_per_day  trades   total_r  profit_factor_r  max_drawdown_r
             1      gap_only                 1                   1     129 20.001084         1.338558       -6.023748


## 6. Frozen system

- **candidate_set:** gap_only
- **candidate_ids:** ["MINIWFO_GAP_ACCEPTANCE_FAILURE_001"]
- **top_per_strategy:** 1; **max_trades_per_day:** 1
- **daily_max_loss_r:** -1.5; **cooldown_after_loss_minutes:** 0
- **priority_policy:** metadata_priority
- **Train-window metrics:** trades=129 total_r=20.00108438327635 PF_R=1.3385580372273052 maxDD_r=-6.023748222814444


## 7. Test result

| metric | value |
|---|---:|
| trades | 89 |
| total_r | 1.306923882982659 |
| profit_factor | 1.2020314701738017 |
| profit_factor_r | 1.028720272070243 |
| max_drawdown_r | -12.263663716159586 |
| avg_cost_r | 0.014100786098342526 |
| median_cost_r | 0.010695187165775374 |
| slip_0.02_total_r | -1.1645705643308029 |
| slip_0.03_total_r | -2.3070942797701623 |


### Daily trade-number profile

 daily_trade_number  trades  total_r
                  1      89 1.306924

## 8. Monthly stability

 period  trades   total_r  profit_factor_r  max_drawdown_r
2025-01       4  0.688129         1.683959       -1.006098
2025-02       4  0.476353         1.236622       -2.013141
2025-03       7  1.960943         1.649498       -2.014289
2025-04       8  0.336952         1.083875       -2.769165
2025-05       7  0.891036         1.293122       -2.020586
2025-06       4 -1.778930         0.411203       -2.018487
2025-07       3 -0.791298         0.611102       -2.034719
2025-08       4 -0.360395         0.822332       -2.028475
2025-09       3  2.326050        17.018025       -0.145215
2025-10       3  1.486907         2.479359       -1.005102
2025-11       6 -1.550835         0.616288       -3.035986
2025-12       9 -9.083297         0.000000       -9.083297
2026-01       5  1.080577         1.538417       -1.003597
2026-02       6  0.302503         1.100503       -2.003724
2026-03      12  3.196609         1.635645       -2.010934
2026-04       4  2.125620         3.116763       -1.004184

- **Largest |monthly total_r|:** 2025-12 (concentration ratio max|R|/sum|R| ≈ 0.32 if defined).


## 9. Comparison to fixed smoke

                                                       system           source_type          selected_using             test_window  trades   total_r       PF              PF_R    maxDD_r   slip_0_02_total_r   slip_0_03_total_r                                                      interpretation
                                 trap_recent_top1 (smoke ref) fixed_smoke_reference recent_window_in_sample 2025-01-01 — 2026-04-30     323 69.057000 1.516000          >1 (ref) -12.082000         (see smoke)         (see smoke) High headline R; selected on recent window — not causal train→test.
                        opening_pair_full_history (smoke ref) fixed_smoke_reference       full_history_pair 2025-01-01 — 2026-04-30     204  7.547000 1.146000          >1 (ref) -18.888000         (see smoke)         (see smoke)     Lower R; broader selection context — use as sanity anchor only.
qqq_mini_wfo_2023_2024_train_2025_202604_test_v1_frozen_rank1       mini_wfo_frozen    train_2023_2024_only 2025-01-01 — 2026-04-30      89  1.306924 1.202031 1.028720272070243 -12.263664 -1.1645705643308029 -2.3070942797701623              Causal path: Layer 1+2 on train only, frozen for test.


## 10. Decision

**CAUTION**

## 11. Recommendation


---

### Automated classification

- Decision: **CAUTION**
- Key test metrics (aggregated): {
  "trades": 89,
  "win_rate": 0.48314606741573035,
  "total_net_pnl": 17.205000000000723,
  "avg_net_pnl": 0.19331460674158116,
  "total_r": 1.306923882982659,
  "avg_r": 0.014684538011041113,
  "profit_factor": 1.2020314701738017,
  "max_drawdown_pnl": -24.822499999999877,
  "max_drawdown_r": -12.263663716159586,
  "avg_bars_held": 30.95505617977528,
  "stop_count": 45,
  "target_count": 34,
  "eod_count": 0,
  "end_of_data_count": 0,
  "max_hold_count": 10,
  "profit_factor_r": 1.028720272070243,
  "median_r": -1.0015313935681456,
  "p25_r": -1.005681818181813,
  "p75_r": 1.2434210526315848,
  "worst_trade_r": -1.027027027027002,
  "best_trade_r": 1.2481617647058867,
  "std_r": 1.0658804541873779,
  "active_days": 89,
  "positive_day_rate": 0.48314606741573035,
  "avg_daily_r": 0.014684538011041113,
  "median_daily_r": -1.0015313935681456,
  "worst_day_r": -1.027027027027002,
  "best_day_r": 1.2481617647058867,
  "daily_profit_factor_r": 1.028720272070243,
  "avg_daily_trade_count": 1.0,
  "max_daily_trade_count": 1,
  "estimated_round_trip_cost_per_share": 0.02,
  "avg_risk_per_share": 2.093820224719088,
  "median_risk_per_share": 1.8700000000000045,
  "p10_risk_per_share": 0.6439999999999828,
  "p25_risk_per_share": 1.2999999999999545,
  "avg_cost_r": 0.014100786098342526,
  "median_cost_r": 0.010695187165775374,
  "p90_cost_r": 0.031138975966562867,
  "pct_trades_cost_r_gt_0_25": 0.0,
  "pct_trades_cost_r_gt_0_50": 0.0,
  "pct_trades_cost_r_gt_1_00": 0.0,
  "end_of_session_count": 0,
  "trades_by_strategy_json": "{\"gap_acceptance_failure\": 89}",
  "pnl_by_strategy_json": "{\"gap_acceptance_failure\": 17.205000000000723}",
  "r_by_strategy_json": "{\"gap_acceptance_failure\": 1.3069238829826615}",
  "trades_by_family_json": "{\"gap_behavior\": 89}",
  "pnl_by_family_json": "{\"gap_behavior\": 17.205000000000723}",
  "r_by_family_json": "{\"gap_behavior\": 1.3069238829826615}",
  "trades_by_candidate_json": "{\"MINIWFO_GAP_ACCEPTANCE_FAILURE_001\": 89}",
  "pnl_by_candidate_json": "{\"MINIWFO_GAP_ACCEPTANCE_FAILURE_001\": 17.205000000000723}",
  "r_by_candidate_json": "{\"MINIWFO_GAP_ACCEPTANCE_FAILURE_001\": 1.3069238829826615}",
  "rejected_by_reason_json": "{}",
  "candidate_signals": 0,
  "rejected_signals": 0,
  "selected_signals": 0,
  "selection_rate": 1.0,
  "combiner_score": 0.622770360753979,
  "low_trade_count": false,
  "wrong_time_window_rejections": 0,
  "existing_position_rejections": 0,
  "daily_loss_limit_rejections": 0,
  "max_trades_rejections": 0,
  "max_trades_reached_rejections": 0,
  "cooldown_rejections": 0,
  "cooldown_after_loss_rejections": 0,
  "no_new_after_rejections": 0,
  "risk_too_small_rejections": 0,
  "lower_priority_rejections": 0,
  "last_bar_no_entry_rejections": 0,
  "session_boundary_no_entry_rejections": 0,
  "disabled_candidate_rejections": 0,
  "opposite_direction_conflict_rejections": 0,
  "invalid_stop_side_rejections": 0,
  "invalid_target_side_rejections": 0,
  "invalid_target_r_rejections": 0,
  "invalid_price_nan_rejections": 0,
  "trades_by_daily_trade_number_json": "{\"1\": 89}",
  "r_by_daily_trade_number_json": "{\"1\": 1.306923882982659}",
  "pnl_by_daily_trade_number_json": "{\"1\": 17.205000000000723}",
  "profit_factor_r_by_daily_trade_number_json": "{\"1\": 1.028720272070243}",
  "avg_r_by_daily_trade_number_json": "{\"1\": 0.014684538011041113}",
  "win_rate_by_daily_trade_number_json": "{\"1\": 0.48314606741573035}"
}

### Recommendation

Run **one more mini-WFO** or refine the strategy family before full WFO.
