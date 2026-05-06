# Behavior-unique combiner systems

Deduplication uses **actual trade sequences** (`behavior_hash_from_trades`), not YAML alone.

- Config rows inspected: **100**
- Rows with `trades.csv` loaded: **15**
- Behavior-unique systems: **1**
- Rows with weak hash quality (missing id/entry/exit columns): **0**
- Missing detailed trades (no matched `top_runs` folder): **85**

## Top 10 behavior-unique

 behavior_rank  source_rank  config_rank                                                    behavior_hash behavior_hash_quality  candidate_set  top_per_strategy  max_trades_per_day  daily_max_loss_r  cooldown_after_loss_minutes   priority_policy                               candidate_ids_json  trades   total_r  total_net_pnl  profit_factor  profit_factor_r  max_drawdown_r  avg_bars_held  avg_cost_r  median_cost_r  p90_cost_r  pct_trades_cost_r_gt_0_50  active_days  positive_day_rate  avg_daily_r  worst_day_r                            trades_by_strategy_json                                                              r_by_strategy_json                                   trades_by_candidate_json                                                                     r_by_candidate_json trades_by_daily_trade_number_json r_by_daily_trade_number_json profit_factor_r_by_daily_trade_number_json
             1            1            1 f8341b5e83b91cc94b89c4a34a43fb80c96484023b945b3afcdd3617231f1c69                strong opening_family                 1                   1              -1.5                            0 metadata_priority ["FAILED_ORB_001", "GAP_ACCEPTANCE_FAILURE_001"]     986 42.320726        68.7675       1.133141         1.088823      -18.994331      21.553753    0.023986       0.020833    0.041667                        0.0          986           0.471602     0.042922         -1.2 {"failed_orb": 698, "gap_acceptance_failure": 288} {"failed_orb": 27.28809680200782, "gap_acceptance_failure": 15.032629657264234} {"FAILED_ORB_001": 698, "GAP_ACCEPTANCE_FAILURE_001": 288} {"FAILED_ORB_001": 27.28809680200782, "GAP_ACCEPTANCE_FAILURE_001": 15.032629657264234}                        {"1": 986}     {"1": 42.32072645927205}                  {"1": 1.0888232831655345}
