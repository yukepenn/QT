# Layer 1 v2 Completion — QQQ 2023–2024

## 1. Purpose

Evaluate the **nine** Strategy Library v2 **completion** plugins on **QQQ** over **2023-01-01 → 2024-12-31** using each strategy’s **`*_focused.yaml`** grid. This is **Layer 1 only** (per-strategy sweeps + manifest + candidate YAML export). **No** Layer 2, **no** mini-WFO, **no** full WFO.

## 2. Input strategy universe

| Strategy | Family (metadata) |
|----------|-------------------|
| `sma20_reclaim_reject` | `moving_average_reclaim` |
| `macd_momentum_turn` | `macd_momentum_shift` |
| `stochastic_oversold_cross` | `oscillator_reversal` |
| `cci_extreme_snapback` | `oscillator_reversal` |
| `adx_dmi_trend_continuation` | `trend_strength_continuation` |
| `supertrend_atr_flip` | `atr_trend_following` |
| `large_candle_failure` | `price_action_failure` |
| `multi_day_level_trap` | `multi_day_level_trap` |
| `prior_close_reclaim` | `value_reclaim` |

## 3. Run settings

- **Symbol:** QQQ (equity)
- **Window:** 2023-01-01 → 2024-12-31
- **Grids:** `src/strategies/testing_parameters/<strategy>_focused.yaml`
- **Grid policy:** All raw grid sizes **≤ 1500** → **full** grid (no `--max-combos` cap). See `grid_review.csv`.
- **Sweep CLI:** `src/research/run_layer1_v2_completion.py` → `sweep.py` with `--top 50`, `--min-trades 25`, `--profile`, `--tag layer1_v2_completion_qqq_2023_2024`
- **Orchestration:** `python src/research/run_layer1_v2_completion.py ... --select-candidates`

### Candidate selection (manifest)

- **Strict:** `min_trades=40`, `min_profit_factor=1.05`, `min_total_r=0`, `max_drawdown_r=-60`, `max_avg_bars_held=120`, `max_eod_count=0`, `max_end_of_data_count=0`
- **Relaxed fallback:** `min_trades=25`, `min_profit_factor=1.00`, `min_total_r=-5`, `max_drawdown_r=-70`, `max_avg_bars_held=150`
- **Top per strategy:** 5  
- Details: `candidate_selection_config.md`

### Engineering fix (candidate YAML)

`select_candidates.unflatten_config_from_row` previously stored keys like `features.indicators.macd_tuples` as a **single flat key** under `features`, so nested `indicators` blocks were wrong and **fast-context reruns failed**. This is fixed by using `set_nested` for multi-segment paths. Candidate YAMLs were **regenerated** after the fix. Sanity: `candidate_fast_context_check.*` — **all 30 candidates OK** on QQQ **2023-01-03 → 2023-01-31**.

## 4. Sweep results

| strategy | capped? | result_rows | best_trades | best_total_r | best_profit_factor | best_max_drawdown_r | warning |
|----------|---------|-------------|-------------|--------------|-------------------|---------------------|---------|
| sma20_reclaim_reject | no | 64 | 502 | -1.42 | 0.97 | -25.06 | best PF still negative total_r |
| macd_momentum_turn | no | 32 | 501 | 11.70 | 1.09 | -16.92 | |
| stochastic_oversold_cross | no | 32 | 502 | 38.05 | 1.22 | -14.51 | |
| cci_extreme_snapback | no | 32 | 4 | 0.44 | 1.95 | -2.04 | sparse top-PF combos (few trades) |
| adx_dmi_trend_continuation | no | 32 | 450 | -46.68 | 1.04 | -69.09 | negative total_r at best PF row |
| supertrend_atr_flip | no | 32 | 502 | 19.99 | 1.12 | -19.68 | |
| large_candle_failure | no | 32 | 457 | -19.08 | 0.99 | -46.31 | |
| multi_day_level_trap | no | 32 | 48 | 4.55 | 1.42 | -6.27 | |
| prior_close_reclaim | no | 32 | 24 | 7.60 | 1.63 | -7.95 | manifest “best_*” uses PF sort over full CSV |

Full machine-readable manifest: `sweep_manifest.csv` / `sweep_manifest.md`.

## 5. Candidate selection

| strategy | strict count | relaxed count | total | top candidate id | top PF / total_r / trades |
|----------|----------------|----------------|-------|-------------------|---------------------------|
| macd_momentum_turn | 3 | 0 | 3 | MACD_MOMENTUM_TURN_001 | 1.06 / 15.76 / 497 |
| stochastic_oversold_cross | 5 | 0 | 5 | STOCHASTIC_OVERSOLD_CROSS_001 | 1.22 / 38.05 / 502 |
| cci_extreme_snapback | 5 | 0 | 5 | CCI_EXTREME_SNAPBACK_001 | 1.57 / 19.34 / 122 |
| adx_dmi_trend_continuation | 0 | 2 | 2 | ADX_DMI_TREND_CONTINUATION_001 | 1.03 / -3.61 / 399 |
| supertrend_atr_flip | 5 | 0 | 5 | SUPERTREND_ATR_FLIP_001 | 1.10 / 21.75 / 497 |
| multi_day_level_trap | 5 | 0 | 5 | MULTI_DAY_LEVEL_TRAP_001 | 1.42 / 4.55 / 48 |
| prior_close_reclaim | 5 | 0 | 5 | PRIOR_CLOSE_RECLAIM_001 | 1.60 / 12.24 / 45 |
| sma20_reclaim_reject | 0 | 0 | 0 | — | no rows passed filters |
| large_candle_failure | 0 | 0 | 0 | — | no rows passed filters |

**Total selected YAMLs:** 30 (`selected_candidates/*.yaml`).

## 6. No-candidate strategies

Listed in `no_candidate_strategies.txt`:

- **`sma20_reclaim_reject`** — no rows met strict or relaxed gates (PF / total_r / drawdown vs thresholds on high-trade grid).
- **`large_candle_failure`** — same.

## 7. Family interpretation

| Family | Strategies | Classification |
|--------|-------------|----------------|
| `moving_average_reclaim` | `sma20_reclaim_reject` | **DEFER** — no candidates |
| `macd_momentum_shift` | `macd_momentum_turn` | **PROMISING_FOR_REDUCED_LAYER2** — strict candidates |
| `oscillator_reversal` | `stochastic_oversold_cross`, `cci_extreme_snapback` | **PROMISING_FOR_REDUCED_LAYER2** — both have strict sets |
| `trend_strength_continuation` | `adx_dmi_trend_continuation` | **WATCHLIST_NEEDS_TUNING** — only relaxed; weak economics |
| `atr_trend_following` | `supertrend_atr_flip` | **PROMISING_FOR_REDUCED_LAYER2** |
| `price_action_failure` | `large_candle_failure` | **DEFER** — no candidates |
| `multi_day_level_trap` | `multi_day_level_trap` | **PROMISING_FOR_REDUCED_LAYER2** |
| `value_reclaim` | `prior_close_reclaim` | **PROMISING_FOR_REDUCED_LAYER2** |

## 8. Recommended next step

**`PROCEED_TO_REDUCED_LAYER2_V2_COMPLETION_DESIGN`**

Rationale: Multiple **non-overlapping** families have **strict** candidates (oscillator ×2, MACD, Supertrend, multi-day trap, prior close). **ADX** is weak but only a small relaxed set. **Fast-context check passed** for all exported YAMLs after the `unflatten` fix. Layer 2 design doc: `../reduced_layer2_v2_completion_design.md`.

## 9. Explicit non-runs

- Layer 2 **not** run  
- mini-WFO v4 **not** run  
- mini-WFO v5 **not** run  
- full WFO **not** run  
