# Behavior-unique combiner systems

Deduplication uses **actual trade sequences** (`behavior_hash_from_trades`), not YAML alone.

- Config rows inspected: **30**
- Rows with `trades.csv` loaded: **15**
- Behavior-unique systems: **1**
- Rows with weak hash quality (missing id/entry/exit columns): **0**
- Missing detailed trades (no matched `top_runs` folder): **15**

## Top 10 behavior-unique

 behavior_rank  source_rank  config_rank                                                    behavior_hash behavior_hash_quality candidate_set  top_per_strategy  max_trades_per_day  daily_max_loss_r  cooldown_after_loss_minutes   priority_policy                 candidate_ids_json  trades  total_r  total_net_pnl  profit_factor  profit_factor_r  max_drawdown_r  avg_bars_held  avg_cost_r  median_cost_r  p90_cost_r  pct_trades_cost_r_gt_0_50  active_days  positive_day_rate  avg_daily_r  worst_day_r    trades_by_strategy_json                        r_by_strategy_json               trades_by_candidate_json                                   r_by_candidate_json trades_by_daily_trade_number_json r_by_daily_trade_number_json profit_factor_r_by_daily_trade_number_json
             1            1            1 82a06845b4875f38f23972f0eaf2390646450cb890c0850f350ccbfac6b22baf                strong     pa_climax                 1                   1              -1.5                            0 metadata_priority ["PA_CLIMAX_REVERSAL_DIVERSE_001"]      50  5.91044         3.5335       1.358004          1.20345       -6.290149           8.66    0.069949       0.060606    0.125833                        0.0           50               0.44     0.118209         -1.1 {"pa_climax_reversal": 50} {"pa_climax_reversal": 5.910439715605148} {"PA_CLIMAX_REVERSAL_DIVERSE_001": 50} {"PA_CLIMAX_REVERSAL_DIVERSE_001": 5.910439715605148}                         {"1": 50}     {"1": 5.910439715605149}                  {"1": 1.2034497782076203}
