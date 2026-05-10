# Grid review — PA Batch B/C tuned v1 (QQQ 2023–2024)

Tag: `layer1_pa_batch_bc_tuned_qqq_2023_2024_v1`  
Root: `src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v1/`

All tuned grids:

- Pass `strategy.validate_config` for all combos (no unsupported keys).
- Are sized to avoid caps (**raw_grid_size ≤ 1500** per strategy).
- Keep `supports_fast=True`.

| strategy | tuned_yaml | raw_grid_size | capped | notes |
|----------|-----------|--------------|--------|-------|
| pa_broad_channel_zone | `pa_broad_channel_zone_tuned_v1.yaml` | 864 | false | baseline was zero-trade |
| pa_climax_reversal | `pa_climax_reversal_tuned_v1.yaml` | 1296 | false | tighten quality (baseline PF < 1) |
| pa_second_entry_pullback | `pa_second_entry_pullback_tuned_v1.yaml` | 1152 | false | increase trade count (baseline max 8) |
| pa_wedge_reversal | `pa_wedge_reversal_tuned_v1.yaml` | 432 | false | tighten wedge proxy (baseline PF < 1) |
| pa_buy_sell_close_trend | `pa_buy_sell_close_trend_tuned_v1.yaml` | 324 | false | reduce hold-time / cost fragility |
| pa_generic_breakout_pullback | `pa_generic_breakout_pullback_tuned_v1.yaml` | 1024 | false | baseline was zero-trade |

