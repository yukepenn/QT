# alignment_best_config_summary

**config_id:** `cfg_0005`

## Switches

- **start_bar_policy:** `entry_bar`
- **entry_price_source:** `bar_open_plus_slip`
- **exit_price_source:** `simulated_bar_price`
- **slippage_policy:** `none`
- **risk_policy:** `abs_entry_minus_stop`
- **same_bar_policy:** `stop_first`
- **forced_exit_policy:** `max_hold`
- **target_policy:** `panel_target_price`

## Headline metrics (all trades in run)

| config_id | start_bar_policy | entry_price_source | exit_price_source | slippage_policy | risk_policy | same_bar_policy | forced_exit_policy | target_policy | trades | mean_abs_r_diff | median_abs_r_diff | p90_abs_r_diff | max_abs_r_diff | total_r_original | total_r_replay | total_r_diff | sign_match_pct | exit_reason_match_pct | ambiguous_count | ambiguous_pct | label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cfg_0005 | entry_bar | bar_open_plus_slip | simulated_bar_price | none | abs_entry_minus_stop | stop_first | max_hold | panel_target_price | 1 | 0.39999999999997726 | 0.39999999999997726 | 0.39999999999997726 | 0.39999999999997726 | 0.5 | 0.10000000000002274 | -0.39999999999997726 | 100.0 | 100.0 | 0 | 0.0 | ALIGNMENT_FAIL |

**Alignment label:** `ALIGNMENT_FAIL`
