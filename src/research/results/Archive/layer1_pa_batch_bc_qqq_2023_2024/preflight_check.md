# Preflight — PA Batch B/C Layer 1

Generated from `preflight_check.csv` (loader + YAML validation + `grid_size` + feature_key smoke).

## Summary

| Strategy | supports_fast | default OK | focused OK | raw_grid_size | metadata family |
|----------|---------------|------------|------------|---------------|-----------------|
| pa_broad_channel_zone | True | ok | ok | 288 | pa_broad_channel |
| pa_climax_reversal | True | ok | ok | 288 | pa_climax_reversal |
| pa_second_entry_pullback | True | ok | ok | 288 | pa_second_entry |
| pa_wedge_reversal | True | ok | ok | 288 | pa_wedge_reversal |
| pa_buy_sell_close_trend | True | ok | ok | 432 | pa_close_trend_continuation |
| pa_generic_breakout_pullback | True | ok | ok | 432 | pa_breakout_pullback |

- **`required_features`:** no LOOKAHEAD in contracts (enforced by loader).
- **Focused YAML:** all six `*_focused.yaml` present under `src/strategies/testing_parameters/`.
- **Feature builder:** `build_features_from_config` smoke on QQQ-like Jan 2025 slice for `pa_broad_channel_zone` default config — OK.

## Outcome

**Proceed to full sweeps** — all grids ≤ 1500; no YAML reduction required for this run.
