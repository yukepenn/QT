# Behavior-unique combiner systems

Deduplication uses **actual trade sequences** (`behavior_hash_from_trades`), not YAML alone.

- Config rows inspected: **50**
- Rows with `trades.csv` loaded: **50**
- Behavior-unique systems: **1**
- Rows with weak hash quality (missing id/entry/exit columns): **0**
- Missing detailed trades (no matched `top_runs` folder): **0**

## Top 10 behavior-unique

 behavior_rank  source_rank  config_rank                                                    behavior_hash behavior_hash_quality candidate_set  top_per_strategy  max_trades_per_day  daily_max_loss_r  cooldown_after_loss_minutes   priority_policy                     candidate_ids_json  trades   total_r  total_net_pnl  profit_factor  profit_factor_r  max_drawdown_r  avg_bars_held  avg_cost_r  median_cost_r  p90_cost_r  pct_trades_cost_r_gt_0_50  active_days  positive_day_rate  avg_daily_r  worst_day_r         trades_by_strategy_json                            r_by_strategy_json                    trades_by_candidate_json                                       r_by_candidate_json trades_by_daily_trade_number_json r_by_daily_trade_number_json profit_factor_r_by_daily_trade_number_json
             1            1            1 829d8646f5ab0c2513ebf8d68275367b76e029446a05f9fdf1f7f0e39270545b                strong      gap_only                 1                   1              -1.5                            0 metadata_priority ["MINIWFO_GAP_ACCEPTANCE_FAILURE_001"]     129 20.001084        34.8275        1.57757         1.338558       -6.023748       28.20155    0.022874       0.020619    0.040333                        0.0          129           0.527132     0.155047     -1.02381 {"gap_acceptance_failure": 129} {"gap_acceptance_failure": 20.00108438327635} {"MINIWFO_GAP_ACCEPTANCE_FAILURE_001": 129} {"MINIWFO_GAP_ACCEPTANCE_FAILURE_001": 20.00108438327635}                        {"1": 129}     {"1": 20.00108438327635}                  {"1": 1.3385580372273052}
