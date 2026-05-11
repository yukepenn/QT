# Brooks PA feature primitives — implementation summary (2026-05-10)

## 1. Columns added (by module)

### `src/features/price_action.py`

- `strong_bull_close`, `strong_bear_close`, `weak_bull_close`, `weak_bear_close`
- `strong_bull_signal_bar`, `strong_bear_signal_bar`, `failed_bull_signal_bar`, `failed_bear_signal_bar`
- `bull_micro_channel_3` … `bull_micro_channel_5`, `bear_micro_channel_3` … `bear_micro_channel_5`

### `src/features/pa_swings.py` (per window `N` in `features.pa.swing_windows`)

- `pa_pullback_bar_count_{N}`
- `pa_two_leg_pullback_down_{N}`, `pa_two_leg_pullback_up_{N}`
- `pa_second_entry_buy_proxy_{N}`, `pa_second_entry_sell_proxy_{N}` (honest `_proxy` suffix)
- `pa_failed_breakout_age_{N}`
- `pa_breakout_attempt_count_up_{N}`, `pa_breakout_attempt_count_down_{N}`
- `pa_trapped_bears_score_{N}`, `pa_trapped_bulls_score_{N}`

Existing columns (`pa_wedge_push_count_*`, `pa_higher_low_proxy_*`, etc.) are unchanged.

### `src/features/regime.py` + `src/features/pa_brooks_enums.py`

Integer enums: Always-In (`-1/0/1`), regime labels (`PA_REGIME_*`), trade modes (`PA_TRADE_MODE_*`).

Per `regime_windows` value `N`:

- `pa_always_in_side_{N}`
- `pa_regime_label_{N}`
- `pa_trade_mode_{N}`
- `pa_late_trend_score_{N}`
- `pa_trend_to_tr_transition_score_{N}`
- `pa_limit_order_market_score_{N}`

### `src/features/levels.py` / `pa_magnet_columns.py`

- `near_orb_high_known_atr`, `near_orb_low_known_atr`
- `near_vwap_upper_1_atr`, `near_vwap_lower_1_atr`, `near_vwap_upper_2_atr`, `near_vwap_lower_2_atr` (when source columns exist)
- Per swing window `N`: `pa_mm_range_up_{N}`, `pa_mm_range_down_{N}`, `near_pa_mm_range_up_atr_{N}`, `near_pa_mm_range_down_atr_{N}`

## 2. Files touched

| Path | Change |
|------|--------|
| `src/features/price_action.py` | Bar primitives + micro-channels |
| `src/features/pa_swings.py` | Swing / trap / second-entry proxies |
| `src/features/regime.py` | Router scores + enum-backed columns |
| `src/features/pa_brooks_enums.py` | **New** shared int enums |
| `src/features/levels.py` | `add_pa_magnet_level_features` |
| `src/features/pa_magnet_columns.py` | **New** column name helper (breaks import cycle with `feature_config`) |
| `src/features/build_features.py` | Magnet pass after `pa_swings`, before proximity |
| `src/features/feature_config.py` | Column lists + `FEATURE_DEPENDENCIES` for `pa_magnet_levels` |
| `src/strategies/strategy/pa_common.py` | **New** shared helpers |

## 3. No-lookahead proof

- Bar primitives: same-bar OHLC + existing shifted / session-safe series; micro-channels use consecutive bar comparisons within session only.
- `pa_swings` additions: session `groupby`, prior bars or same-bar flags already used elsewhere in the module; no centered windows.
- Regime router: combines **already-computed** same-window regime scores and trend / follow-through columns with vectorized rules; no future peek.
- Magnets: distances use `orb_*_known`, VWAP bands, and prior / same-bar range columns; **no** `full_session_*_LOOKAHEAD` in magnet formulas.

## 4. Feature key / build order

- `PaFeatureConfig` already includes `swing_windows`, `regime_windows`, and bar thresholds; `feature_key_from_config` continues to hash the full `pa` block.
- Build order: … `price_action` → `pa_swings` → **PA magnet levels** → `pa_proximity` → … regime pass still receives columns it needs from earlier steps.

## 5. Known limitations

- `pandas` **PerformanceWarning** (fragmented DataFrame) can appear when many columns are inserted sequentially in `price_action` / volume; backlog: batch `pd.concat` for hot paths.
- Regime / trade-mode scores are **coarse research inputs**, not standalone trade signals.
- **Delayed-confirmed** swing labels: deferred to backlog (would need explicit bar-delay spec + tests).

## 6. Strategy `required_features`

- No new primitives were added to any PA strategy’s `required_features` in this phase; consumption is reserved for future tuned YAMLs (e.g. v3).
