# Canonical strategy integration (first targets)

**Date:** 2026-05-11  
**Status:** Design only — no signal or YAML edits in this milestone.

These three are the first **single-strategy** candidates for wiring `read_bars` → features → `generate_signals` → `signal_adapter` → `run_strategy_backtest` in a future canonical sweep (after `COMPLETE_CANONICAL_BACKTEST_SWEEP` expands the runner).

## pa_buy_sell_close_trend

| Topic | Detail |
|--------|--------|
| Required features | Session OHLCV, VWAP, `close_near_high`, `body_pct`, `consecutive_bull_closes_3`, `trend_score_{regw}`, `pa_climax_score_{rw}`, rolling range columns, `atr_like_20` (see `required_features()`). |
| Output contract | Uses `finalize_long_signals_df` / standard `sig_*` columns. |
| Canonical mapping | Identity — already `STANDARD_SIGNAL_COLUMNS`. |
| Gaps | None for signal shape; sweep must supply full feature bar set. |
| management_mode | From metadata / defaults when execution supports it (optional column). |
| target_mode | `fixed_r` from strategy. |
| max_hold | From `backtest.max_hold_minutes` in normalized key — must flow into `sig_max_hold_bars` when policy requires. |
| Risk | Feature store size / alignment; fast-path vs reference parity not in scope. |

## gap_acceptance_failure

| Topic | Detail |
|--------|--------|
| Required features | Gap / VWAP / ATR / rolling lows / session open / prior close (see strategy). |
| Output contract | `init_standard_signal_columns` + side/valid/stop/target fields; `sig_reason` tagged `gap_{mode}`. |
| Canonical mapping | Identity. |
| Gaps | Modes `gap_acceptance` vs `gap_failure` affect reason string only. |
| management_mode | Default from metadata when wired. |
| target_mode | Primarily `fixed_r` when `target_mode_code` maps to TM_FIXED_R. |
| max_hold | From config (`max_hold_minutes` in normalized key). |
| Risk | Session boundary features must be no-lookahead. |

## cci_extreme_snapback

| Topic | Detail |
|--------|--------|
| Required features | CCI columns (`cci_14`, `cci_20`, `cci_30` precomputed), swings, VWAP, ATR. |
| Output contract | Standard `sig_*` via same pattern as gap strategy. |
| Canonical mapping | Identity. |
| Gaps | Window-specific CCI column name must match `features.cci_window`. |
| management_mode | Default when execution wiring adds partials. |
| target_mode | `fixed_r`. |
| max_hold | `risk.max_trades_per_day` is not max_hold — use `backtest.max_hold_minutes` when present. |
| Risk | Numba kernel inside signal generation is strategy-side only; accounting remains `simulate_trade_path`. |

## Conclusion

No `output_contract` renames required for these three today; `infer_signal_mapping` may stay empty. Machine-readable status rows: **`docs/CANONICAL_STRATEGY_INTEGRATION_STATUS.csv`**. The real-symbol connector (`strategy_runner` + `run_canonical_real_symbol_sweep`) now covers the data → feature → signal → backtest path; broaden coverage after Champion migration planning.
