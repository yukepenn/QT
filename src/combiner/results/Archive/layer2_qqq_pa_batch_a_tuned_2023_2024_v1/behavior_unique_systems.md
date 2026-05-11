# Behavior-unique combiner systems

Deduplication uses **actual trade sequences** (`behavior_hash_from_trades`), not YAML alone.

- Config rows inspected: **30**
- Rows with `trades.csv` loaded: **20**
- Behavior-unique systems: **2**
- Rows with weak hash quality (missing id/entry/exit columns): **0**
- Missing detailed trades (no matched `top_runs` folder): **10**

## Top 10 behavior-unique

 behavior_rank  source_rank  config_rank                                                    behavior_hash behavior_hash_quality        candidate_set  top_per_strategy  max_trades_per_day  daily_max_loss_r  cooldown_after_loss_minutes   priority_policy                    candidate_ids_json  trades   total_r  total_net_pnl  profit_factor  profit_factor_r  max_drawdown_r  avg_bars_held  avg_cost_r  median_cost_r  p90_cost_r  pct_trades_cost_r_gt_0_50  active_days  positive_day_rate  avg_daily_r  worst_day_r                trades_by_strategy_json                                   r_by_strategy_json                   trades_by_candidate_json                                      r_by_candidate_json trades_by_daily_trade_number_json r_by_daily_trade_number_json profit_factor_r_by_daily_trade_number_json
             1            1            1 4c9caf240f5b46e6aab1020842c1f4a191f28597a3543ef5681b8f1f3563f67a                strong     pa_trading_range                 1                   1              -1.5                            0 metadata_priority       ["PA_TRADING_RANGE_BLS_HS_001"]      63 25.573435       2.395343       1.469832         1.476480      -22.172181       3.000000    0.235638       0.233577    0.331542                   0.000000           63           0.238095     0.405928    -1.217273        {"pa_trading_range_bls_hs": 63}      {"pa_trading_range_bls_hs": 25.573435226211014}        {"PA_TRADING_RANGE_BLS_HS_001": 63}      {"PA_TRADING_RANGE_BLS_HS_001": 25.573435226211014}                         {"1": 63}     {"1": 25.57343522621101}                   {"1": 1.476480497339458}
             2           17           17 9ff66925036a11e97a4c67b68b0461f939e04606a803849f025ded36ceb7818c                strong pa_failed_range_trap                 1                   1              -1.5                            0 metadata_priority ["PA_FAILED_RANGE_BREAKOUT_TRAP_001"]     220 12.877416       5.477500       1.205766         1.109798      -16.955949       3.509091    0.116778       0.090909    0.222222                   0.004545          220           0.495455     0.058534    -1.250000 {"pa_failed_range_breakout_trap": 220} {"pa_failed_range_breakout_trap": 12.87741647593284} {"PA_FAILED_RANGE_BREAKOUT_TRAP_001": 220} {"PA_FAILED_RANGE_BREAKOUT_TRAP_001": 12.87741647593284}                        {"1": 220}     {"1": 12.87741647593284}                   {"1": 1.109797962034779}
