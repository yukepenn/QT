# Layer 3 Mini-WFO v1 — QQQ 2023–2024 Train / 2025–2026 Test

## 1. Purpose

Single causal mini-WFO: train-only selection, one held-out test. Not full WFO; not live-ready.

## 2. Train/test split

- Train: **2020-01-01** → **2024-12-31**
- Test: **2025-01-01** → **2026-04-30**

## 3. Strategies included

**Primary:** failed_orb, gap_acceptance_failure.
**Diagnostic:** prior_day_level_trap (optional set only).
**Excluded:** ORB_RETEST, ORB_CONTINUATION, VWAP — prior diagnosis flagged opening/trap/VWAP paths as noisy or unstable vs the gap/failed_orb core.

## 4. Train Layer 1 candidate summary

              strategy  n_candidates  best_total_r  best_pf  max_trades  worst_mdd
            failed_orb             5     43.626165 1.166759         665 -13.797964
gap_acceptance_failure             5     41.051306 1.320917         320  -7.029883
  prior_day_level_trap             2      5.946638 1.045680         297 -19.766166
   vwap_reclaim_reject             5     25.270472 1.074913         472 -28.535829
   vwap_trend_pullback             1      0.228088 1.086576         368 -19.968626


## 5. Train Layer 2 selection

 behavior_rank  candidate_set  top_per_strategy  max_trades_per_day  trades   total_r  profit_factor_r  max_drawdown_r
             1       gap_only                 1                   1     320 41.051306         1.282005       -7.029883
             2 prior_day_only                 2                   2     304  9.703063         1.054773      -18.097555
             3 prior_day_only                 1                   1     297  5.946638         1.034164      -17.319742
             4 prior_day_only                 2                   2     301  7.337720         1.041670      -18.333827
             5     failed_gap                 1                   1     787 48.191527         1.153688      -14.752563
             6     failed_gap                 2                   1     788 48.173880         1.153623      -14.752563


## 6. Frozen system

- **candidate_set:** failed_gap
- **candidate_ids:** ["MINIWFO_FAILED_ORB_001", "MINIWFO_GAP_ACCEPTANCE_FAILURE_001"]
- **top_per_strategy:** 1; **max_trades_per_day:** 1
- **daily_max_loss_r:** -1.5; **cooldown_after_loss_minutes:** 0
- **priority_policy:** metadata_priority
- **Train-window metrics:** trades=787 total_r=48.191527493664616 PF_R=1.1536881398902417 maxDD_r=-14.75256316585986


## 7. Test result

| metric | value |
|---|---:|
| trades | 205 |
| total_r | -5.920676276219462 |
| profit_factor | 1.006717747683554 |
| profit_factor_r | 0.9361974384912417 |
| max_drawdown_r | -22.8802889418765 |
| avg_cost_r | 0.017234913855869095 |
| median_cost_r | 0.01526717557251972 |
| slip_0.02_total_r | -8.343193543207246 |
| slip_0.03_total_r | -11.139718355529835 |


### Daily trade-number profile

 daily_trade_number  trades   total_r
                  1     205 -5.920676

## 8. Monthly stability

 period  trades   total_r  profit_factor_r  max_drawdown_r
2025-01      14  2.098032         1.385685       -3.021280
2025-02      11 -0.698059         0.884976       -3.651645
2025-03      13  5.090344         2.552829       -2.022096
2025-04      14  4.124486         1.794072       -3.185976
2025-05      15 -2.021122         0.749773       -5.834043
2025-06      14  0.924383         1.204472       -2.018487
2025-07      10 -1.693890         0.620235       -2.505249
2025-08      13  0.092486         1.026300       -3.418358
2025-09      13  5.350661         3.003620       -1.516949
2025-10      14  0.425285         1.072750       -2.372757
2025-11      11 -1.339850         0.778892       -4.046087
2025-12      10 -8.534961         0.005142       -8.534961
2026-01      12 -3.867228         0.476563       -4.539265
2026-02      12 -3.397997         0.526187       -5.154901
2026-03      15 -0.465291         0.937689       -3.016099
2026-04      14 -2.007955         0.715552       -4.033998

- **Largest |monthly total_r|:** 2025-12 (concentration ratio max|R|/sum|R| ≈ 0.20 if defined).


## 9. Comparison to fixed smoke

                                                        system           source_type          selected_using             test_window  trades   total_r       PF               PF_R    maxDD_r  slip_0_02_total_r   slip_0_03_total_r                                                      interpretation
                                  trap_recent_top1 (smoke ref) fixed_smoke_reference recent_window_in_sample 2025-01-01 — 2026-04-30     323 69.057000 1.516000           >1 (ref) -12.082000        (see smoke)         (see smoke) High headline R; selected on recent window — not causal train→test.
                         opening_pair_full_history (smoke ref) fixed_smoke_reference       full_history_pair 2025-01-01 — 2026-04-30     204  7.547000 1.146000           >1 (ref) -18.888000        (see smoke)         (see smoke)     Lower R; broader selection context — use as sanity anchor only.
qqq_mini_wfo_v2b_2020_2024_train_2025_202604_test_frozen_rank1       mini_wfo_frozen    train_2023_2024_only 2025-01-01 — 2026-04-30     205 -5.920676 1.006718 0.9361974384912417 -22.880289 -8.343193543207246 -11.139718355529835              Causal path: Layer 1+2 on train only, frozen for test.


## 10. Decision

**FAIL**

## 11. Recommendation


---

### Automated classification

- Decision: **FAIL**
- Key test metrics (aggregated): {
  "trades": 205,
  "win_rate": 0.4926829268292683,
  "total_net_pnl": 0.9425000000026102,
  "avg_net_pnl": 0.004597560975622489,
  "total_r": -5.920676276219462,
  "avg_r": -0.028881347688875424,
  "profit_factor": 1.006717747683554,
  "max_drawdown_pnl": -37.112499999999386,
  "max_drawdown_r": -22.8802889418765,
  "avg_bars_held": 17.497560975609755,
  "stop_count": 86,
  "target_count": 51,
  "eod_count": 0,
  "end_of_data_count": 0,
  "max_hold_count": 68,
  "profit_factor_r": 0.9361974384912417,
  "median_r": -0.10679611650476006,
  "p25_r": -1.0064516129032202,
  "p75_r": 0.9769230769231846,
  "worst_trade_r": -1.027027027027002,
  "best_trade_r": 1.2481617647058867,
  "std_r": 0.9449869816788893,
  "active_days": 205,
  "positive_day_rate": 0.4926829268292683,
  "avg_daily_r": -0.028881347688875424,
  "median_daily_r": -0.10679611650476006,
  "worst_day_r": -1.027027027027002,
  "best_day_r": 1.2481617647058867,
  "daily_profit_factor_r": 0.9361974384912417,
  "avg_daily_trade_count": 1.0,
  "max_daily_trade_count": 1,
  "estimated_round_trip_cost_per_share": 0.02,
  "avg_risk_per_share": 1.5922926829268216,
  "median_risk_per_share": 1.3099999999999454,
  "p10_risk_per_share": 0.6599999999999682,
  "p25_risk_per_share": 0.9699999999999136,
  "avg_cost_r": 0.017234913855869095,
  "median_cost_r": 0.01526717557251972,
  "p90_cost_r": 0.030303030303031765,
  "pct_trades_cost_r_gt_0_25": 0.0,
  "pct_trades_cost_r_gt_0_50": 0.0,
  "pct_trades_cost_r_gt_1_00": 0.0,
  "end_of_session_count": 0,
  "trades_by_strategy_json": "{\"failed_orb\": 145, \"gap_acceptance_failure\": 60}",
  "pnl_by_strategy_json": "{\"failed_orb\": 7.987500000001717, \"gap_acceptance_failure\": -7.044999999999106}",
  "r_by_strategy_json": "{\"failed_orb\": -0.42334491887759573, \"gap_acceptance_failure\": -5.497331357341867}",
  "trades_by_family_json": "{\"gap_behavior\": 60, \"opening_reversal\": 145}",
  "pnl_by_family_json": "{\"gap_behavior\": -7.044999999999106, \"opening_reversal\": 7.987500000001717}",
  "r_by_family_json": "{\"gap_behavior\": -5.497331357341867, \"opening_reversal\": -0.42334491887759573}",
  "trades_by_candidate_json": "{\"MINIWFO_FAILED_ORB_001\": 145, \"MINIWFO_GAP_ACCEPTANCE_FAILURE_001\": 60}",
  "pnl_by_candidate_json": "{\"MINIWFO_FAILED_ORB_001\": 7.987500000001717, \"MINIWFO_GAP_ACCEPTANCE_FAILURE_001\": -7.044999999999106}",
  "r_by_candidate_json": "{\"MINIWFO_FAILED_ORB_001\": -0.42334491887759573, \"MINIWFO_GAP_ACCEPTANCE_FAILURE_001\": -5.497331357341867}",
  "rejected_by_reason_json": "{\"existing_position\": 24, \"lower_priority_conflict\": 14, \"wrong_time_window\": 4}",
  "candidate_signals": 0,
  "rejected_signals": 42,
  "selected_signals": 0,
  "selection_rate": 0.8299595141700404,
  "combiner_score": -1.1459986256916428,
  "low_trade_count": false,
  "wrong_time_window_rejections": 4,
  "existing_position_rejections": 24,
  "daily_loss_limit_rejections": 0,
  "max_trades_rejections": 0,
  "max_trades_reached_rejections": 0,
  "cooldown_rejections": 0,
  "cooldown_after_loss_rejections": 0,
  "no_new_after_rejections": 0,
  "risk_too_small_rejections": 0,
  "lower_priority_rejections": 14,
  "last_bar_no_entry_rejections": 0,
  "session_boundary_no_entry_rejections": 0,
  "disabled_candidate_rejections": 0,
  "opposite_direction_conflict_rejections": 0,
  "invalid_stop_side_rejections": 0,
  "invalid_target_side_rejections": 0,
  "invalid_target_r_rejections": 0,
  "invalid_price_nan_rejections": 0,
  "trades_by_daily_trade_number_json": "{\"1\": 205}",
  "r_by_daily_trade_number_json": "{\"1\": -5.920676276219462}",
  "pnl_by_daily_trade_number_json": "{\"1\": 0.9425000000026102}",
  "profit_factor_r_by_daily_trade_number_json": "{\"1\": 0.9361974384912417}",
  "avg_r_by_daily_trade_number_json": "{\"1\": -0.028881347688875424}",
  "win_rate_by_daily_trade_number_json": "{\"1\": 0.4926829268292683}"
}

### Recommendation

Return to **Layer 1 family / diagnosis** before expanding scope.
