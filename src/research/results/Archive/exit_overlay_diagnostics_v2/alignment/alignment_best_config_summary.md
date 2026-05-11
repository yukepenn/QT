# alignment_best_config_summary

**config_id:** `cfg_0015`

## Switches

- **start_bar_policy:** `entry_bar`
- **entry_price_source:** `bar_open_plus_slip`
- **exit_price_source:** `panel_exit_price_when_original`
- **slippage_policy:** `apply_like_combiner`
- **risk_policy:** `abs_entry_minus_stop`
- **same_bar_policy:** `stop_first`
- **forced_exit_policy:** `panel_exit_idx`
- **target_policy:** `panel_target_price`
- **max_hold_priority:** `intrabar_first`

## Headline metrics (all trades in run)

| config_id | start_bar_policy | entry_price_source | exit_price_source | slippage_policy | risk_policy | same_bar_policy | forced_exit_policy | target_policy | max_hold_priority | trades | mean_abs_r_diff | median_abs_r_diff | p90_abs_r_diff | max_abs_r_diff | total_r_original | total_r_replay | total_r_diff | sign_match_pct | exit_reason_match_pct | ambiguous_count | ambiguous_pct | label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cfg_0015 | entry_bar | bar_open_plus_slip | panel_exit_price_when_original | apply_like_combiner | abs_entry_minus_stop | stop_first | panel_exit_idx | panel_target_price | intrabar_first | 10628 | 0.03495439676644034 | 0.0 | 3.430589146091734e-14 | 1.8535502958579866 | 744.950005896781 | 797.3531451038355 | 52.40313920705445 | 98.83327060594655 | 95.44599171998495 | 8 | 0.07527286413248024 | ALIGNMENT_FAIL |

**Alignment label:** `ALIGNMENT_FAIL`
