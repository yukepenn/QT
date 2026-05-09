# Behavior-unique combiner systems

Deduplication uses **actual trade sequences** (`behavior_hash_from_trades`), not YAML alone.

- Config rows inspected: **30**
- Rows with `trades.csv` loaded: **15**
- Behavior-unique systems: **1**
- Rows with weak hash quality (missing id/entry/exit columns): **0**
- Missing detailed trades (no matched `top_runs` folder): **15**

## Top 10 behavior-unique

 behavior_rank  source_rank  config_rank                                                    behavior_hash behavior_hash_quality       candidate_set  top_per_strategy  max_trades_per_day  daily_max_loss_r  cooldown_after_loss_minutes   priority_policy                                                                                                                                                         candidate_ids_json  trades   total_r  total_net_pnl  profit_factor  profit_factor_r  max_drawdown_r  avg_bars_held  avg_cost_r  median_cost_r  p90_cost_r  pct_trades_cost_r_gt_0_50  active_days  positive_day_rate  avg_daily_r  worst_day_r             trades_by_strategy_json                                r_by_strategy_json                                                       trades_by_candidate_json                                                                                        r_by_candidate_json trades_by_daily_trade_number_json r_by_daily_trade_number_json profit_factor_r_by_daily_trade_number_json
             1            1            1 8814798463e5434cbc6bf47ab17eb065b87bdd6ec1631f079d03bedad98f5435                strong volatility_breakout                 5                   1              -1.5                            0 metadata_priority ["BOLLINGER_SQUEEZE_BREAKOUT_001", "BOLLINGER_SQUEEZE_BREAKOUT_002", "BOLLINGER_SQUEEZE_BREAKOUT_003", "BOLLINGER_SQUEEZE_BREAKOUT_004", "BOLLINGER_SQUEEZE_BREAKOUT_005"]     488 34.557513      12.901167       1.146303          1.13513      -12.460417       7.981557    0.074663       0.064586       0.125                        0.0          488           0.493852     0.070815    -1.142857 {"bollinger_squeeze_breakout": 488} {"bollinger_squeeze_breakout": 34.55751287392331} {"BOLLINGER_SQUEEZE_BREAKOUT_001": 266, "BOLLINGER_SQUEEZE_BREAKOUT_005": 222} {"BOLLINGER_SQUEEZE_BREAKOUT_001": 4.74797191958438, "BOLLINGER_SQUEEZE_BREAKOUT_005": 29.809540954338928}                        {"1": 488}     {"1": 34.55751287392331}                  {"1": 1.1351302189258927}
