# Strategy Library v2 — completion (plugins + smoke)

## 1. Purpose

Add the nine remaining non-overlapping **v2_completion** strategy plugins (QQQ-oriented, long-only MVP) using the existing **generic feature layer**, **BaseStrategy** fast context path, and **no** strategy-specific logic in `src/backtest/fast.py` / `src/backtest/sweep.py`. This phase is **code + tests + Jan 2025 wiring smokes** only.

**Not run:** Layer 2, mini-WFO v4/v5, full Layer 1 2023–2024 sweeps (optional capped 2023–2024 smokes were skipped after Jan health checks).

## 2. Starting repo state

- **Strategies before:** 16 (`python src/strategies/loader.py --list`).
- **After:** 25 (+9).
- **Existing feature modules reused:** `indicators.py` (MACD, stoch, CCI, ADX/DMI, EMA/SMA), `levels.py` (prior day + gaps), `price_action.py`, `volatility.py`, `vwap.py`, etc.
- **Patched:** `indicators.py` + `build_types.py` + `feature_key.py` + `feature_config.py` + `levels.py` for **session supertrend** and **multi-session reference lows** (`prior_3day_low`, `prior_5day_low`, `previous_week_low`).

## 3. Feature additions

| Area | Action |
|------|--------|
| Supertrend | `supertrend_line_{atr_w}_{mult_z}`, `supertrend_dir_{atr_w}_{mult_z}` from `features.indicators.supertrend_tuples`; requires matching `atr_like_{atr_w}` via `features.vol_windows`. |
| Multi-day lows | Prior-exclusive lows merged from completed sessions only (see `levels.py` + `test_levels_multiday_no_lookahead.py`). |
| MACD grid safety | `macd_momentum_turn` parameters include **all** `(fast,slow)` pairs used by the focused grid so columns always exist. |

No new `*_LOOKAHEAD` columns are required by the new strategies.

## 4. Strategy additions

| Strategy | Family (metadata) | Notes |
|----------|---------------------|--------|
| `multi_day_level_trap` | `multi_day_level_trap` | Overlap risk with `prior_day_level_trap`; uses **different** level anchors (3d/5d/week). |
| `adx_dmi_trend_continuation` | `trend_strength_continuation` | ADX/DMI + break / EMA reclaim. |
| `supertrend_atr_flip` | `atr_trend_following` | Session supertrend flip or pullback. |
| `macd_momentum_turn` | `macd_momentum_shift` | MACD / histogram / zero reclaim. |
| `prior_close_reclaim` | `value_reclaim` | Prior **close** reclaim (not gap strategy). |
| `sma20_reclaim_reject` | `moving_average_reclaim` | SMA/EMA line reclaim. |
| `large_candle_failure` | `price_action_failure` | Large red candle + no new low + reclaim. |
| `stochastic_oversold_cross` | `oscillator_reversal` | Stoch %K/%D cross from oversold. |
| `cci_extreme_snapback` | `oscillator_reversal` | CCI snapback from extreme. |

Each: `supports_fast = True`, `performance_tier = A_true_context_fast_core`, `prepare_signal_context` + `generate_signal_arrays_from_context`, parameters + `*_focused.yaml`, `metadata.yaml` entry.

## 5. Architecture compliance

- **Generic features only** in `src/features/`; strategies only under `src/strategies/strategy/`.
- **No** `DfSignalStrategy` usage; **no** strategy branches added in `fast.py` / `sweep.py` (not modified in this work).
- **Feature key** includes `IndicatorsFeatureConfig.supertrend_tuples` and expanded registry columns in `feature_config.py`.
- **YAML:** axes align with validated keys; `macd_momentum_turn` includes full MACD tuple set for grid Cartesian products.

## 6. Health (Jan 2025 QQQ, `--max-combos` capped)

Jan smokes completed for all nine strategies (non-zero combos, no crashes after MACD tuple fix). Metrics are **not** used for tuning—wiring only. See `strategy_library_v2_completion_health.md` / `.csv`.

## 7. Issues fixed during implementation

- **SMA reclaim Numba:** restored `min_bars_below_line` as `mb_req` parameter (was referenced but omitted).
- **MACD sweep Cartesian product:** grid `macd_fast` × `macd_slow` required extra `macd_tuples` so all pairs have columns.
- **Indicator test:** supertrend ATR column must exist—test uses `atr_like_15` / tuple `(15, 200)`.
- **Stoch/CCI:** `hh3_prior` naming consistency in Numba kernels.

## 8. Next phase (pick one)

**`RUN_LAYER1_V2_COMPLETION_2023_2024`** — run capped/full Layer 1 on QQQ 2023–2024 with completion grids when you are ready to evaluate economics (not part of this commit’s scope).

**Explicit non-runs:** Layer 2, mini-WFO v4, mini-WFO v5, full WFO.
