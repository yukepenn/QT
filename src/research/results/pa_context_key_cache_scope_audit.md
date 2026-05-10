# PA `context_key` cache scope audit (2026-05-10)

## Principle

`context_key(config)` must change **only** when `prepare_signal_context(df, config)` would load different numpy columns or reshape context arrays. Thresholds, entry windows, risk modes, and `finalize_long_signals_df` parameters belong in **`normalized_param_key`** (and/or feature build / `feature_key`), not in `context_key`.

## Summary table

| Strategy | Previous `context_key` fields (conceptual) | Kept | Removed | `normalized_param_key` covers removed? | Notes / stale params |
|----------|---------------------------------------------|------|---------|----------------------------------------|------------------------|
| `pa_buy_sell_close_trend` | tag, `pa_range_window`, `pa_regime_window`, `body_pct_min`, `trend_score_min`, `require_vwap_side`, `atr_column` | tag, `pa_range_window`, `pa_regime_window`, `atr_column` | body/trend/VWAP bool thresholds | Yes | `trend_score_{regw}` column uses regime window in prepare |
| `pa_climax_reversal` | tag, range, regime, climax/bear/VWAP distance mins, `atr_column` | tag, `pa_range_window`, `atr_column` | regime + signal thresholds | Yes | **`prepare` does not use `pa_regime_window`** (only `pa_range_window` columns) |
| `pa_trading_range_bls_hs` | tag, range, regime, `trading_range_score_min`, `confirm_mode`, `atr_column` | tag, `pa_range_window`, `pa_regime_window`, `atr_column` | TR score min, confirm mode | Yes | Regime used for `range_efficiency_*` / `vwap_cross_count_*` column choice |
| `pa_failed_range_breakout_trap` | tag, range, `fail_window_bars`, `require_tr_regime`, `atr_column` | tag, `pa_range_window`, `atr_column` | fail window, TR regime flag | Yes | **`fail_window_bars` not referenced in signal generation** (validated only; stale for behavior) |
| `pa_tight_channel_pullback` | tag, `pa_regime_window`, `tight_bull_score_min`, `require_vwap_side`, `atr_column` | tag, `pa_regime_window`, `atr_column` | score min, VWAP bool | Yes | Uses **`pa_regime_window`** as rolling-window selector (not `pa_range_window`) |
| `pa_mtr_reversal` | tag, `pa_range_window`, `bear_channel_score_min`, `atr_column` | tag, `pa_range_window`, `atr_column` | bear min | Yes | |
| `pa_broad_channel_zone` | tag, range, regime, broad min, VWAP context bool, `block_climax`, `atr_column` | tag, `pa_range_window`, `atr_column` | regime + thresholds | Yes | **`prepare` does not use `pa_regime_window`** |
| `pa_second_entry_pullback` | tag, range, regime, `context_score_min`, `require_trend_context`, `atr_column` | tag, `pa_range_window`, `atr_column` | regime + thresholds | Yes | **`prepare` does not use `pa_regime_window`** |
| `pa_wedge_reversal` | tag, range, regime, wedge/bear mins, `atr_column` | tag, `pa_range_window`, `atr_column` | regime + thresholds | Yes | **`prepare` does not use `pa_regime_window`** |
| `pa_generic_breakout_pullback` | tag, range, regime, `recent_breakout_lookback`, `pullback_test_atr`, `atr_column` | tag, `pa_range_window`, `pa_regime_window`, `atr_column` | lookback, pullback test | Yes | Overlap column uses `pa_regime_window`; lookback/test are post-load filters |

## Expected cache benefit

Layer 1 / Layer 2 precompute reuse **`(strategy, feature_key, context_key)`** buckets. Removing threshold axes collapses many sweep combos into one prepared context per distinct **feature column set** + **ATR column**, improving CPU and memory when grids vary thresholds with fixed PA windows.

## Non-goals (this change)

- No edits to `generate_signal_arrays_from_context` logic.
- No `normalized_param_key` changes except audit confirmation (no missing signal fields found).
- No reruns of Layer 1 / Layer 2 / WFO.
