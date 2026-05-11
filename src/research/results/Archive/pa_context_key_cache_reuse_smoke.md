# PA `context_key` cache reuse — lightweight smoke (2026-05-10)

## Method

For each strategy + tuned testing YAML below:

1. Load default `parameters/<strategy>.yaml`.
2. Expand the testing `grid` and merge each combo with the YAML `fixed:` block (dotted keys via `apply_overrides`).
3. Count **raw** grid rows vs **unique** `strategy.context_key(cfg)` tuples.

No sweep execution, no Parquet reads, no committed sweep artifacts.

## Results

| Strategy | YAML | Raw combos | Unique `context_key` |
|----------|------|------------|----------------------|
| `pa_buy_sell_close_trend` | `pa_buy_sell_close_trend_tuned_v2.yaml` | 576 | 1 |
| `pa_climax_reversal` | `pa_climax_reversal_tuned_v2.yaml` | 576 | 1 |
| `pa_trading_range_bls_hs` | `pa_trading_range_bls_hs_tuned_v1.yaml` | 576 | 1 |
| `pa_failed_range_breakout_trap` | `pa_failed_range_breakout_trap_tuned_v1.yaml` | 576 | 1 |
| `pa_generic_breakout_pullback` | `pa_generic_breakout_pullback_tuned_v2.yaml` | 576 | 1 |
| `pa_broad_channel_zone` | `pa_broad_channel_zone_tuned_v2.yaml` | 972 | 1 |

## Interpretation

These tuned grids **fix** `features.pa_range_window` / `features.pa_regime_window` (where applicable) and `signal.atr_column`, so **unique `context_key` count is already 1** for the full Cartesian product: every combo differs only in thresholds / risk / hold columns that belong in **`normalized_param_key`**, not context shape.

**After** narrowing `context_key`, the same metric stays 1 here, but sweeps that **vary PA windows or ATR column** across combos will see **fewer** unique context buckets than before (previously, threshold axes artificially inflated `context_key` cardinality even when prepared arrays were identical).

## Signal behavior

No intentional signal logic edits in this work; parity script + unit tests guard regressions.
