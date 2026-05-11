# Behavior-unique combiner systems

Deduplication uses **actual trade sequences** (`behavior_hash_from_trades`), not YAML alone.

- Config rows inspected: **30**
- Rows with `trades.csv` loaded: **20**
- Behavior-unique systems: **1**
- Rows with weak hash quality (missing id/entry/exit columns): **0**
- Missing detailed trades (no matched `top_runs` folder): **10**

## Top 10 behavior-unique

 behavior_rank  source_rank  config_rank                                                    behavior_hash behavior_hash_quality candidate_set  top_per_strategy  max_trades_per_day  daily_max_loss_r  cooldown_after_loss_minutes   priority_policy           candidate_ids_json  trades   total_r  total_net_pnl  profit_factor  profit_factor_r  max_drawdown_r  avg_bars_held  avg_cost_r  median_cost_r  p90_cost_r  pct_trades_cost_r_gt_0_50  active_days  positive_day_rate  avg_daily_r  worst_day_r       trades_by_strategy_json                           r_by_strategy_json          trades_by_candidate_json                              r_by_candidate_json trades_by_daily_trade_number_json r_by_daily_trade_number_json profit_factor_r_by_daily_trade_number_json
             1            1            1 5c1cc4eff14cd9e2c64f8f2a3879c203f68380dc59d38b9feba5e836da3586b5                strong      cci_only                 1                   1              -1.5                            0 metadata_priority ["CCI_EXTREME_SNAPBACK_001"]     122 19.344269       8.495125        1.57068         1.386121       -5.878177       5.729508    0.074697        0.07016    0.118115                        0.0          122           0.598361      0.15856    -1.076482 {"cci_extreme_snapback": 122} {"cci_extreme_snapback": 19.344268641472244} {"CCI_EXTREME_SNAPBACK_001": 122} {"CCI_EXTREME_SNAPBACK_001": 19.344268641472244}                        {"1": 122}     {"1": 19.34426864147225}                  {"1": 1.3861209533934085}
