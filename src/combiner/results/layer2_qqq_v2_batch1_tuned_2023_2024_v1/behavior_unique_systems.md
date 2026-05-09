# Behavior-unique combiner systems

Deduplication uses **actual trade sequences** (`behavior_hash_from_trades`), not YAML alone.

- Config rows inspected: **30**
- Rows with `trades.csv` loaded: **15**
- Behavior-unique systems: **1**
- Rows with weak hash quality (missing id/entry/exit columns): **0**
- Missing detailed trades (no matched `top_runs` folder): **15**

## Top 10 behavior-unique

 behavior_rank  source_rank  config_rank                                                    behavior_hash behavior_hash_quality             candidate_set  top_per_strategy  max_trades_per_day  daily_max_loss_r  cooldown_after_loss_minutes   priority_policy                 candidate_ids_json  trades   total_r  total_net_pnl  profit_factor  profit_factor_r  max_drawdown_r  avg_bars_held  avg_cost_r  median_cost_r  p90_cost_r  pct_trades_cost_r_gt_0_50  active_days  positive_day_rate  avg_daily_r  worst_day_r             trades_by_strategy_json                                 r_by_strategy_json                trades_by_candidate_json                                    r_by_candidate_json trades_by_daily_trade_number_json r_by_daily_trade_number_json profit_factor_r_by_daily_trade_number_json
             1            1            1 e34e63d2b3f0acb4a98cf6e98967616b1884ca0942c9cfc6262ffc2175343ee1                strong volatility_breakout_tuned                 1                   1              -1.5                            0 metadata_priority ["BOLLINGER_SQUEEZE_BREAKOUT_001"]     376 35.417506       9.750333        1.11293         1.174711      -16.817294       15.06383    0.056792       0.053908    0.086456                        0.0          376           0.457447     0.094195    -1.087719 {"bollinger_squeeze_breakout": 376} {"bollinger_squeeze_breakout": 35.417505918706176} {"BOLLINGER_SQUEEZE_BREAKOUT_001": 376} {"BOLLINGER_SQUEEZE_BREAKOUT_001": 35.417505918706176}                        {"1": 376}    {"1": 35.417505918706176}                  {"1": 1.1747111176057774}
