# Fixed robust-profile definitions (v1)

These are **locked profiles** derived from robust-core diagnostic v1 evidence. They are **not** “best per window” picks.

| profile_id | candidate_set | candidate_ids | max_trades_per_day | daily_max_loss_r | priority_policy | purpose |
| --- | --- | --- | --- | --- | --- | --- |
| pa_only_mtp1_meta | pa_only_core | PA_BUY_SELL_CLOSE_TREND_003 | 1 | -1.5 | metadata_priority | cleanest PA-only baseline |
| pa_only_mtp2_meta | pa_only_core | PA_BUY_SELL_CLOSE_TREND_003 | 2 | -1.5 | metadata_priority | mtp=2 sensitivity for PA-only |
| pa_gap_mtp2_meta | pa_gap_core | PA_BUY_SELL_CLOSE_TREND_003, GAP_ACCEPTANCE_FAILURE_001 | 2 | -1.5 | metadata_priority | leading combined profile candidate |
| primary_mtp2_meta | primary_representative_core | PA_BUY_SELL_CLOSE_TREND_003, GAP_ACCEPTANCE_FAILURE_001, CCI_EXTREME_SNAPBACK_003 | 2 | -1.5 | metadata_priority | primary core baseline (tests CCI inclusion) |
| pa_gap_mtp1_meta | pa_gap_core | PA_BUY_SELL_CLOSE_TREND_003, GAP_ACCEPTANCE_FAILURE_001 | 1 | -1.5 | metadata_priority | optional mtp=1 sensitivity |

Source-of-truth CSV: `fixed_profile_definitions.csv`.

