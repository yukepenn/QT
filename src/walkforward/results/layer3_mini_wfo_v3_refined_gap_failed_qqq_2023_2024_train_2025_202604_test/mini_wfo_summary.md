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
            failed_orb             5     12.408621 1.330594         182 -10.538288
gap_acceptance_failure             5      9.674573 1.252352          89  -6.574430


## 5. Train Layer 2 selection

 behavior_rank       candidate_set  top_per_strategy  max_trades_per_day  trades   total_r  profit_factor_r  max_drawdown_r
             1 refined_failed_only                 1                   1     181 12.408621         1.134934      -10.538288
             2 refined_failed_only                 3                   1     182 11.390981         1.122509      -10.538288
             3    refined_gap_only                 1                   1      89  9.674573         1.281443       -6.574430


## 6. Frozen system

- **candidate_set:** refined_failed_only
- **candidate_ids:** ["MINIWFO_FAILED_ORB_001"]
- **top_per_strategy:** 1; **max_trades_per_day:** 1
- **daily_max_loss_r:** -1.5; **cooldown_after_loss_minutes:** 0
- **priority_policy:** metadata_priority
- **Train-window metrics:** trades=181 total_r=12.408621380938571 PF_R=1.1349336264003334 maxDD_r=-10.538288407357072


## 7. Test result

| metric | value |
|---|---:|
| trades | 139 |
| total_r | 5.058063616601594 |
| profit_factor | 1.2874619342644293 |
| profit_factor_r | 1.0696313920607203 |
| max_drawdown_r | -17.775699618367298 |
| avg_cost_r | 0.016348363263093652 |
| median_cost_r | 0.015503875968992685 |
| slip_0.02_total_r | 3.692108750735296 |
| slip_0.03_total_r | 0.7670357625588573 |


### Daily trade-number profile

 daily_trade_number  trades  total_r
                  1     139 5.058064

## 8. Monthly stability

 period  trades   total_r  profit_factor_r  max_drawdown_r
2025-01       9  3.777505         2.025182       -3.684716
2025-02       5 -0.049286         0.983765       -3.035863
2025-03       7  2.071763         1.684318       -1.016129
2025-04      10  5.536763         2.620681       -2.011378
2025-05       9 -1.582275         0.738821       -4.566748
2025-06       5  2.849284         3.810781       -1.013699
2025-07       8 -5.964467         0.157122       -5.964467
2025-08       7 -2.187811         0.566858       -5.051027
2025-09      10  2.173339         1.537273       -2.027819
2025-10      13 -2.508355         0.644408       -3.774461
2025-11       7 -2.289471         0.442491       -3.782935
2025-12       9 -2.521580         0.552840       -4.015592
2026-01       9 -2.501985         0.586845       -4.477355
2026-02       7  2.279537         2.131070       -1.010526
2026-03      11  2.152051         1.405165       -2.010760
2026-04      13  3.823052         1.631977       -2.016903

- **Largest |monthly total_r|:** 2025-07 (concentration ratio max|R|/sum|R| ≈ 0.13 if defined).


## 9. Comparison to fixed smoke

                                                                          system           source_type          selected_using             test_window  trades   total_r       PF               PF_R  maxDD_r slip_0_02_total_r  slip_0_03_total_r                                                      interpretation
                                                    trap_recent_top1 (smoke ref) fixed_smoke_reference recent_window_in_sample 2025-01-01 — 2026-04-30     323 69.057000 1.516000           >1 (ref) -12.0820       (see smoke)        (see smoke) High headline R; selected on recent window — not causal train→test.
                                           opening_pair_full_history (smoke ref) fixed_smoke_reference       full_history_pair 2025-01-01 — 2026-04-30     204  7.547000 1.146000           >1 (ref) -18.8880       (see smoke)        (see smoke)     Lower R; broader selection context — use as sanity anchor only.
qqq_mini_wfo_v3_refined_gap_failed_2023_2024_train_2025_202604_test_frozen_rank1       mini_wfo_frozen    train_2023_2024_only 2025-01-01 — 2026-04-30     139  5.058064 1.287462 1.0696313920607203 -17.7757 3.692108750735296 0.7670357625588573              Causal path: Layer 1+2 on train only, frozen for test.


## 10. Decision

**PASS**

## 11. Recommendation


---

### Automated classification

- Decision: **PASS**
- Key test metrics (aggregated): {
  "trades": 139,
  "win_rate": 0.4460431654676259,
  "total_net_pnl": 27.375000000001307,
  "avg_net_pnl": 0.19694244604317487,
  "total_r": 5.058063616601594,
  "avg_r": 0.03638894688202586,
  "profit_factor": 1.2874619342644293,
  "max_drawdown_pnl": -13.619999999999322,
  "max_drawdown_r": -17.775699618367298,
  "avg_bars_held": 20.72661870503597,
  "stop_count": 69,
  "target_count": 43,
  "eod_count": 0,
  "end_of_data_count": 0,
  "max_hold_count": 27,
  "profit_factor_r": 1.0696313920607203,
  "median_r": -0.6647398843930434,
  "p25_r": -1.0083683473389278,
  "p75_r": 1.490291262135931,
  "worst_trade_r": -1.0192307692307525,
  "best_trade_r": 1.4981617647058894,
  "std_r": 1.1370792092597075,
  "active_days": 139,
  "positive_day_rate": 0.4460431654676259,
  "avg_daily_r": 0.03638894688202586,
  "median_daily_r": -0.6647398843930434,
  "worst_day_r": -1.0192307692307525,
  "best_day_r": 1.4981617647058894,
  "daily_profit_factor_r": 1.0696313920607203,
  "avg_daily_trade_count": 1.0,
  "max_daily_trade_count": 1,
  "estimated_round_trip_cost_per_share": 0.02,
  "avg_risk_per_share": 1.4734532374100666,
  "median_risk_per_share": 1.2899999999999636,
  "p10_risk_per_share": 0.7300000000000182,
  "p25_risk_per_share": 1.0249999999999773,
  "avg_cost_r": 0.016348363263093652,
  "median_cost_r": 0.015503875968992685,
  "p90_cost_r": 0.02739726027397192,
  "pct_trades_cost_r_gt_0_25": 0.0,
  "pct_trades_cost_r_gt_0_50": 0.0,
  "pct_trades_cost_r_gt_1_00": 0.0,
  "end_of_session_count": 0,
  "trades_by_strategy_json": "{\"failed_orb\": 139}",
  "pnl_by_strategy_json": "{\"failed_orb\": 27.375000000001307}",
  "r_by_strategy_json": "{\"failed_orb\": 5.058063616601595}",
  "trades_by_family_json": "{\"opening_reversal\": 139}",
  "pnl_by_family_json": "{\"opening_reversal\": 27.375000000001307}",
  "r_by_family_json": "{\"opening_reversal\": 5.058063616601595}",
  "trades_by_candidate_json": "{\"MINIWFO_FAILED_ORB_001\": 139}",
  "pnl_by_candidate_json": "{\"MINIWFO_FAILED_ORB_001\": 27.375000000001307}",
  "r_by_candidate_json": "{\"MINIWFO_FAILED_ORB_001\": 5.058063616601595}",
  "rejected_by_reason_json": "{}",
  "candidate_signals": 0,
  "rejected_signals": 0,
  "selected_signals": 0,
  "selection_rate": 1.0,
  "combiner_score": 0.26933528125739825,
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
  "trades_by_daily_trade_number_json": "{\"1\": 139}",
  "r_by_daily_trade_number_json": "{\"1\": 5.058063616601594}",
  "pnl_by_daily_trade_number_json": "{\"1\": 27.375000000001307}",
  "profit_factor_r_by_daily_trade_number_json": "{\"1\": 1.0696313920607203}",
  "avg_r_by_daily_trade_number_json": "{\"1\": 0.03638894688202586}",
  "win_rate_by_daily_trade_number_json": "{\"1\": 0.4460431654676259}"
}

### Recommendation

Proceed toward **full Layer 3 WFO v1** with a **reduced grid** aligned to this family.
