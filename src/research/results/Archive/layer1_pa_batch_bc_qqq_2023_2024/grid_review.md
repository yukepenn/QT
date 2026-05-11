# Grid review — PA Batch B/C Layer 1

## Policy

- Maximum **raw** grid size before YAML reduction: **1500** combinations.
- **No** silent `--max-combos` cap when raw size is within policy.

## Grids

| Strategy | Raw size | Capped? | Notes |
|----------|----------|---------|--------|
| pa_broad_channel_zone | 288 | no | Full focused grid |
| pa_climax_reversal | 288 | no | Full focused grid |
| pa_second_entry_pullback | 288 | no | Full focused grid |
| pa_wedge_reversal | 288 | no | Full focused grid |
| pa_buy_sell_close_trend | 432 | no | Full focused grid |
| pa_generic_breakout_pullback | 432 | no | Full focused grid |

All strategies: **full grid** run. Duplicate parameter keys are skipped inside `sweep.py` (`normalized_param_key`); `result_rows` in the manifest may be **less than** raw grid size.
