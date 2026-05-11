# Commit C plan — strategy `validate_config`, context keys, YAML cleanup

- **Baseline HEAD (pre-C implementation)**: `a049a1148d7e1f1aca67b018342932f0ae4acd2f` (Commit B: feature key / no-lookahead)
- **Goal**: Honest, cache-safe strategy plugins: shared validation module, `BaseStrategy.validate_config()`, wired into engine/sweep/combiner/research paths, `context_key` aligned with `prepare_signal_context`, remove fake YAML axes.

## Strategy files inspected

All ten plugins under `src/strategies/strategy/*.py` plus `base.py`, `loader.py`.

## Config fields (per strategy, high level)

| Strategy | Notable signal/risk/features |
|----------|-------------------------------|
| `orb_continuation` | side, daily_signal_mode, ORB width gates, stop_mode orb_mid/orb_opposite, target fixed_r |
| `failed_orb` | side, fail_window_bars, confirm_mode, stop failed_extreme/swing_buffered, target modes, atr_column |
| `orb_retest_continuation` | max_retest_bars, retest_tolerance_atr, stop retest_low/orb_mid, atr_column (long-only) |
| `gap_acceptance_failure` | mode gap_acceptance/gap_failure, confirm, stop modes, opening_hold_minutes, atr_column (long-only) |
| `prior_day_level_trap` | fail_window_bars, level_buffer_atr, level_type (MVP: prior_day_low only), atr_column |
| `vwap_reclaim_reject` | min_bars_wrong_side (+ derived rolling window W), confirm, stop modes, atr_column (long-only) |
| `vwap_trend_pullback` | trend_window (feature column selection), confirm, stop modes, atr_column (long-only) |
| `vwap_reversal` | extension_band, confirm_mode, slope_filter_mode, swing_lookback, stop/target modes |
| `afternoon_continuation` | morning_end_minute, entry vs morning anchor, stop modes, atr_column; **midday_window removed** |
| `midday_compression_breakout` | compression_window, max_range_atr, stop modes, atr_column (long-only) |

## Context params (cache-driving)

Updated keys now include **atr_column** wherever `atr_series()` feeds context; **prior_day** includes `level_buffer_atr` and roll window `ww`; **vwap_reclaim** includes `W = max(mb+5,15)`; **failed_orb** includes `atr_column`.

## Suspected fake / unsupported axes (addressed)

- `afternoon_continuation.features.midday_window`: unused → **rejected in `validate_config`**, removed from default + focused YAML.
- Long-only MVPs: **gap_acceptance_failure**, **prior_day_level_trap** (level_type), **orb_retest_continuation**, **vwap_reclaim_reject**, **vwap_trend_pullback**, **midday_compression_breakout**, **afternoon_continuation** — `validate_long_only_mvp` or explicit level_type check.

## Tests added

- `tests/test_strategy_config_validation.py` — common + combiner + strategy-specific rejects.
- `tests/test_strategy_context_keys.py` — `context_key` sensitivity + afternoon `normalized_param_key` ignores fake `midday_window`.

## Implementation summary (executed)

1. `src/utils/config_validation.py` — nested getters, numeric/minute validators, `validate_common_*`, `validate_long_only_mvp`.
2. `BaseStrategy.validate_config()` default no-op.
3. Call sites: `engine.run_strategy_backtest`, `sweep.main` loop, `candidate.precompute_candidate_signal_matrices`, `combiner/run.py`, `combiner/sweep.py`, `research/check_strategy_fast_parity.py`, `research/run_layer1_focused.py` (`validate_testing_grid_for_strategy`).
4. Per-strategy `validate_config` + `context_key` / `normalized_param_key` tweaks as above.
5. YAML: removed `midday_window` from afternoon parameters + focused fixed block.

## Next (Commit D)

Per `hardening_audit_plan.md`: behavior-level dedupe, cost-as-R, R-based metrics, daily/monthly breakdowns.
