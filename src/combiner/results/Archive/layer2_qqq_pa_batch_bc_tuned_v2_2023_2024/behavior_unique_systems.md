# Behavior-unique combiner systems

Deduplication uses **actual trade sequences** (`behavior_hash_from_trades`), not YAML alone.

- Config rows inspected: **30**
- Rows with `trades.csv` loaded: **15**
- Behavior-unique systems: **1**
- Rows with weak hash quality (missing id/entry/exit columns): **0**
- Missing detailed trades (no matched `top_runs` folder): **15**

## Top 10 behavior-unique

 behavior_rank  source_rank  config_rank                                                    behavior_hash behavior_hash_quality candidate_set  top_per_strategy  max_trades_per_day  daily_max_loss_r  cooldown_after_loss_minutes   priority_policy         candidate_ids_json  trades  total_r  total_net_pnl  profit_factor  profit_factor_r  max_drawdown_r  avg_bars_held  avg_cost_r  median_cost_r  p90_cost_r  pct_trades_cost_r_gt_0_50  active_days  positive_day_rate  avg_daily_r  worst_day_r    trades_by_strategy_json                        r_by_strategy_json       trades_by_candidate_json                           r_by_candidate_json trades_by_daily_trade_number_json r_by_daily_trade_number_json profit_factor_r_by_daily_trade_number_json
             1            1            1 106026d563bbe525f50b7e6d9d7d19611ca53192c033f7402c83517645cfe888                strong     pa_climax                 1                   1              -1.5                            0 metadata_priority ["PA_CLIMAX_REVERSAL_001"]      51 6.226636         3.7375       1.373377         1.206673       -6.290149       9.333333    0.071594       0.060606    0.133333                        0.0           51           0.431373     0.122091         -1.1 {"pa_climax_reversal": 51} {"pa_climax_reversal": 6.226635904737264} {"PA_CLIMAX_REVERSAL_001": 51} {"PA_CLIMAX_REVERSAL_001": 6.226635904737264}                         {"1": 51}     {"1": 6.226635904737265}                  {"1": 1.2066725728096157}
