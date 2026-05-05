# Behavior-unique combiner systems

Deduplication uses **actual trade sequences** (`behavior_hash_from_trades`), not YAML alone.

- Config rows inspected: **100**
- Rows with `trades.csv` loaded: **15**
- Behavior-unique systems: **1**
- Rows with weak hash quality (missing id/entry/exit columns): **0**
- Missing detailed trades (no matched `top_runs` folder): **85**

## Top 10 behavior-unique

 behavior_rank  source_rank  config_rank                                                    behavior_hash behavior_hash_quality candidate_set  top_per_strategy  max_trades_per_day  daily_max_loss_r  cooldown_after_loss_minutes   priority_policy                                                           candidate_ids_json  trades   total_r  total_net_pnl  profit_factor  profit_factor_r  max_drawdown_r  avg_bars_held  avg_cost_r  median_cost_r  p90_cost_r  pct_trades_cost_r_gt_0_50  active_days  positive_day_rate  avg_daily_r  worst_day_r                                                        trades_by_strategy_json                                                                                                        r_by_strategy_json                                                                   trades_by_candidate_json                                                                                                                   r_by_candidate_json trades_by_daily_trade_number_json r_by_daily_trade_number_json profit_factor_r_by_daily_trade_number_json
             1            1            1 ee89177ab0c66fde1642dccf47b69f77d873fc801f8cc7adf133b971d4ab4919                strong   trap_family                 1                   1              -1.5                            0 metadata_priority ["FAILED_ORB_001", "GAP_ACCEPTANCE_FAILURE_001", "PRIOR_DAY_LEVEL_TRAP_001"]     523 30.180974          50.44       1.180079         1.115185      -17.218395      21.126195    0.023952       0.020833    0.041667                        0.0          523           0.470363     0.057707    -1.041667 {"failed_orb": 338, "gap_acceptance_failure": 121, "prior_day_level_trap": 64} {"failed_orb": 21.94467773181089, "gap_acceptance_failure": 1.9519137981414223, "prior_day_level_trap": 6.28438222856056} {"FAILED_ORB_001": 338, "GAP_ACCEPTANCE_FAILURE_001": 121, "PRIOR_DAY_LEVEL_TRAP_001": 64} {"FAILED_ORB_001": 21.94467773181089, "GAP_ACCEPTANCE_FAILURE_001": 1.9519137981414223, "PRIOR_DAY_LEVEL_TRAP_001": 6.28438222856056}                        {"1": 523}    {"1": 30.180973758512877}                  {"1": 1.1151850015014908}
