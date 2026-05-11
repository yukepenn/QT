# PA Brooks feature registry / `feature_key` audit — 2026-05-10

## 1. `FEATURE_COLUMNS` registry

- **`price_action`:** Includes bar primitives such as `strong_bull_close`, `bull_micro_channel_*` (see `feature_config.py` → `FEATURE_COLUMNS["price_action"]`).
- **`pa_swings`:** Built via `pa_swing_column_names(PaFeatureConfig)` in `pa_swings.py` — includes `pa_failed_breakout_down_age_{N}`, `pa_failed_breakout_up_age_{N}`, and legacy `pa_failed_breakout_age_{N}` (alias of down-age).
- **`regime`:** Built via `regime_column_names(RegimeFeatureConfig, PaFeatureConfig)` — includes `pa_always_in_side_*`, `pa_regime_label_*`, `pa_trade_mode_*`, etc., from `pa_regime_column_names`.
- **`pa_magnet_levels`:** Built via `pa_magnet_level_column_names(swing_windows)` in `pa_magnet_columns.py` (`near_orb_*`, VWAP band proximity, `pa_mm_range_*`, `near_pa_mm_range_*`).

## 2. `FEATURE_DEPENDENCIES`

- `pa_swings` depends on `price_action` bar columns where second-entry proxies use strong closes / reversal flags.
- `pa_magnet_levels` depends on ORB known columns, VWAP bands (when present), ATR, and prior-safe PA range columns.
- `regime` / PA regime scores depend on session OHLC, ATR, VWAP distance, overlap, etc., as declared in `feature_config.py`.

## 3. `feature_key_from_config`

The frozen `("pa", f.pa)` entry in `feature_key_from_config` carries the full **`PaFeatureConfig`** dataclass, including:

- `swing_windows`
- `regime_windows`
- `atr_window`
- `strong_bar_body_pct`, `close_near_*` thresholds, etc.

Therefore the key **changes** when `features.pa.swing_windows` or `features.pa.regime_windows` (or other `PaFeatureConfig` fields) change. **`price_action_windows`** still affects `price_action` outputs and remains in the top-level `("price_action_windows", …)` tuple.

## 4. Tests

- `tests/test_pa_brooks_feature_registry.py` asserts representative columns exist after `build_features_from_config`, registry lists include new swing names, and `feature_key` differs when PA swing/regime windows change.

## 5. Strategy `required_features`

- No PA strategy adds `*_LOOKAHEAD` to `required_features` (checked in registry test + existing `test_pa_required_features_no_lookahead.py`).
