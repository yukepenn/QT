# Trade output and feature schema inventory (v1)

**Purpose:** Document combiner trade rows vs feature columns used for entry-time enrichment (research only).

## Paths inspected

- `src/combiner/simulator.py` — legacy detailed trade dict (`trade_id`, `candidate_id`, `strategy`, `strategy_family`, `session_date`, `side`, `entry_ts_utc`, `exit_ts_utc`, `entry_price`, `exit_price`, `stop_price`, `target_price`, `risk_per_share`, `net_pnl`, `r_multiple`, `exit_reason`, `bars_held`, `daily_trade_number`, …).
- `src/combiner/run.py` — writes `trades.csv` when `--no-save` is off (default detailed path).
- `src/features/build_features.py` — `build_basic_features` orchestration.
- `src/features/build_types.py` — `RegimeFeatureConfig`, `PaFeatureConfig` (`regime_windows` default `(20,30,60)`).
- `src/features/regime.py` — `pa_regime_label_{w}`, `pa_trade_mode_{w}`, `pa_always_in_side_{w}`, `range_efficiency_{w}`, `vwap_cross_count_{w}`, … when `RegimeFeatureConfig.windows` includes `w`.
- `src/features/feature_config.py` — registry of logical feature groups.
- `src/research/enrich_combiner_trades.py` — merges trades with `read_bars` → `build_basic_features(..., regime=RegimeFeatureConfig(windows=(20,)))`.

## Observed combiner trade schema (detailed run)

Representative columns from regenerated `trades.csv` (QQQ 2023–2024):

`trade_id`, `candidate_id`, `strategy`, `strategy_family`, `symbol`, `session_date`, `side`, `signal_idx`, `signal_ts_utc`, `entry_idx`, `entry_ts_utc`, `exit_idx`, `exit_ts_utc`, `entry_price`, `exit_price`, `stop_price`, `target_price`, `risk_per_share`, `target_mode_code`, `target_r`, `net_pnl`, `r_multiple`, `exit_reason`, `bars_held`, `priority`, `daily_trade_number`.

`exit_reason` uses short names: `target`, `stop`, `eod`, etc. (`EXIT_NAMES` in `simulator.py`).

## Feature columns used at enrichment (window = 20)

Joined with **merge_asof backward** on `entry_ts_utc` ↔ `ts_utc` (no lookahead).

- Time / session: `minute_from_open` → `entry_minute_from_open`.
- Regime (PA coarse, Brooks enums): `pa_regime_label_20`, `pa_trade_mode_20`, `pa_always_in_side_20` → decoded string labels `entry_regime_label`, `entry_trade_mode`, `entry_always_in_side`.
- Generic regime window metrics (because `RegimeFeatureConfig.windows=(20,)`): `range_efficiency_20`, `vwap_cross_count_20`, `trend_score_20`, `compression_score_20` → prefixed `entry_*`.
- PA scores: `pa_strong_breakout_score_20`, `pa_trading_range_score_20`, `pa_climax_score_20`, `pa_late_trend_score_20`, `pa_trend_to_tr_transition_score_20`, `pa_limit_order_market_score_20`.
- VWAP / ORB / levels: `pa_distance_from_vwap_atr`, `vwap_slope_20`, `close_above_vwap` / `close_below_vwap`, `above_orb_high` / `below_orb_low`, `orb_width_pct`, `orb_high_dist` / `orb_low_dist`, `near_prior_close_atr`, all `near_*_atr` magnet proxies → `entry_nearest_magnet`, `entry_magnet_distance_atr`, derived `entry_distance_to_orh_atr` / `entry_distance_to_orl_atr`.

## Prior-trade context (from trade file only)

Computed in `trade_quality_helpers.add_prior_trade_columns`:

- `entry_trade_number_of_day` — overwritten from `daily_trade_number` when present (combiner authority).
- `entry_prior_trade_pnl_r`, `entry_prior_trade_same_strategy`, `entry_prior_trade_same_family`, `entry_prior_trade_was_loss`.

## Missing / optional (not required for v1)

- Separate modeling of **limit target** vs **stop** slippage in combiner PnL (still single `slippage_per_share` in simulator); enrichment flags `entry_is_profit_target_exit` from `exit_reason` for attribution only.
- Human-readable **`nearest_magnet`** is the **column name** with smallest `near_*_atr`, not a semantic level label.
- **Out-of-sample** folds — not in this diagnostic.

## If local `trades.csv` is unavailable

Regenerate with commands documented in `selected_systems_for_diagnostics.md` (same configs as Global L2 / tuned rows). Do not commit raw `trades.csv`.
