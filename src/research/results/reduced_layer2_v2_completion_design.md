# Reduced Layer 2 — Strategy Library v2 completion (design only)

**Status:** design / planning only. **No** combiner sweep executed.

## 1. Context

Layer 1 completion (QQQ 2023–2024) produced **30** candidate YAMLs under `layer1_v2_completion_qqq_2023_2024/selected_candidates/`. Two strategies (`sma20_reclaim_reject`, `large_candle_failure`) have **no** candidates.

## 2. Candidate sets (for future combiner YAML)

These are **logical** buckets referencing the Layer 1 library by strategy name (actual wiring uses paths to YAMLs).

| Set id | Contents |
|--------|----------|
| `ma_reclaim_family` | *(empty in completion track)* |
| `macd_momentum_family` | `macd_momentum_turn` |
| `oscillator_reversal_family` | `stochastic_oversold_cross`, `cci_extreme_snapback` |
| `trend_strength_family` | `adx_dmi_trend_continuation` (relaxed-only; use sparingly) |
| `atr_trend_family` | `supertrend_atr_flip` |
| `price_action_failure_family` | *(empty)* |
| `level_reclaim_family` | `multi_day_level_trap`, `prior_close_reclaim` |
| `all_strict_completion` | All candidates with `selection.filters_used: strict` in YAML |
| `all_with_relaxed_completion` | All 30 YAMLs |
| `strict_core_v3` | **Future:** refined failed/gap core library + completion strict winners (requires separate Layer 2 manifest; not defined here) |

## 3. Proposed combiner rule grid (when implemented)

- `max_open_positions`: **1**
- `max_trades_per_day`: `[1, 2, 3]`
- `daily_max_loss_r`: `[-1.5, -2.0, -3.0]`
- `cooldown_after_loss_minutes`: `[0, 15, 30]`
- `top_per_strategy`: `[1, 2, 3, 5]`
- `priority_policy`: `[metadata_priority, score_adjusted_priority]`

## 4. Risk notes

- **ADX / DMI** completion candidates are **relaxed-filter** only and show **negative total_r** on the top exported rows — treat as **diagnostic / optional** in combiner sets.
- **CCI** grid includes high-PF but **low-trade-count** corners; prefer candidates with **≥ ~100 trades** when building strict systems.
- **No SPY** and **no** new data pulls assumed for this design.

## 5. Next implementation step (out of scope here)

Author a combiner config YAML under `src/combiner/configs/` pointing at `selected_candidates/` for this root, then run `combiner/run.py` / `sweep.py` diagnostics only after explicit approval.
