# PA `normalized_param_key` audit (Batch A/B/C)

Layer 1 sweep dedupe uses `normalized_param_key`. These fields were **added** so configs that change **final signal arrays** (including entry window, thinning, min risk, ATR-buffer stops) do not silently collapse:

| Strategy | Added / emphasized fields |
|----------|---------------------------|
| All PA strategies above | `signal.entry_start_minute`, `signal.entry_end_minute`, `risk.atr_buffer_mult`, `risk.max_trades_per_day`, `risk.min_risk_per_share` (via `nz`) |
| `pa_mtr_reversal` | `signal.wedge_push_min` (was missing vs array generation) |
| `pa_tight_channel_pullback` | `signal.block_climax`, `signal.climax_score_max` |
| `pa_broad_channel_zone` | `signal.zone_max_frac` (buy-zone depth in rolling range; default `1/3` preserves legacy lower-third gate) |

## Impact on prior Layer 1 artifacts

Any PA Layer 1 sweep **before** this fix may have **skipped distinct combos** that differed only on omitted keys (especially entry minutes and risk thinning). Treat historical PA Layer 1 CSV roots as **directional**, not bitwise-complete dedupe, until selectively rerun.

## Tests

`tests/test_strategy_normalized_param_keys.py` mutates curated fields per strategy and asserts the key changes.
