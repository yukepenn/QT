# Testing parameter grids — index

All YAMLs live under `src/strategies/testing_parameters/`. **Do not delete** grids; deferred grids stay for reference.

Legend: **status** = how the grid is used in current research; **result root** = last known Layer 1 / research artifact folder when applicable.

---

## 1. Active focused grids (`*_focused.yaml`)

| Strategy | File | Purpose | Status | Last known result root | Notes |
|----------|------|---------|--------|------------------------|-------|
| failed_orb | `failed_orb_focused.yaml` | Core failed-ORB sweep grid | Active | `layer1_*batch1*` / refined tracks | Primary refined family |
| gap_acceptance_failure | `gap_acceptance_failure_focused.yaml` | Gap acceptance failure | Active | batch1 / refined | |
| orb_continuation | `orb_continuation_focused.yaml` | ORB continuation | Active | library v1 | |
| orb_retest_continuation | `orb_retest_continuation_focused.yaml` | ORB retest | Active | library v1 | |
| prior_day_level_trap | `prior_day_level_trap_focused.yaml` | Prior day level | Active | library v1 | |
| vwap_reclaim_reject | `vwap_reclaim_reject_focused.yaml` | VWAP reclaim/reject | Active | library v1 | |
| vwap_trend_pullback | `vwap_trend_pullback_focused.yaml` | VWAP trend pullback | Active | library v1 | |
| vwap_reversal | `vwap_reversal_focused.yaml` | VWAP reversal | Active | library v1 | |
| afternoon_continuation | `afternoon_continuation_focused.yaml` | Afternoon trend | Active | library v1 | |
| midday_compression_breakout | `midday_compression_breakout_focused.yaml` | Midday compression | Active | library v1 | |
| intraday_ma_crossover | `intraday_ma_crossover_focused.yaml` | MA crossover | Active | library v1 | |
| consecutive_bar_exhaustion | `consecutive_bar_exhaustion_focused.yaml` | Exhaustion | Active | library v1 | |
| bollinger_band_fade_chop | `bollinger_band_fade_chop_focused.yaml` | BB fade chop | Active | library v1 | |
| bollinger_squeeze_breakout | `bollinger_squeeze_breakout_focused.yaml` | BB squeeze | Active | batch1 | |
| donchian_channel_breakout | `donchian_channel_breakout_focused.yaml` | Donchian | Active | library v1 | |
| rsi_failure_swing | `rsi_failure_swing_focused.yaml` | RSI failure swing | Active | batch1 | |
| **macd_momentum_turn** | `macd_momentum_turn_focused.yaml` | **v2 completion** | Active | `layer1_v2_completion_qqq_2023_2024` | Strict winners |
| **stochastic_oversold_cross** | `stochastic_oversold_cross_focused.yaml` | **v2 completion** | Active | same | |
| **cci_extreme_snapback** | `cci_extreme_snapback_focused.yaml` | **v2 completion** | Active | same | Sparse high-PF corners |
| **adx_dmi_trend_continuation** | `adx_dmi_trend_continuation_focused.yaml` | **v2 completion** | Diagnostic | same | Relaxed-only candidates |
| **supertrend_atr_flip** | `supertrend_atr_flip_focused.yaml` | **v2 completion** | Active | same | |
| **multi_day_level_trap** | `multi_day_level_trap_focused.yaml` | **v2 completion** | Active | same | |
| **prior_close_reclaim** | `prior_close_reclaim_focused.yaml` | **v2 completion** | Active | same | |

### PA Batch A (Brooks-style branch — four plugins)

| Strategy | File | Purpose | Status | Last known result root | Notes |
|----------|------|---------|--------|------------------------|-------|
| pa_trading_range_bls_hs | `pa_trading_range_bls_hs_focused.yaml` | PA trading-range BLS/HS long MVP | Active | `src/research/results/layer1_pa_batch_a_qqq_2023_2024/` | Formal Layer 1 2023–2024; no strict YAML (see summary) |
| pa_failed_range_breakout_trap | `pa_failed_range_breakout_trap_focused.yaml` | Failed rolling-range breakout trap | Active | same | **4** strict YAMLs; best in-batch edge |
| pa_tight_channel_pullback | `pa_tight_channel_pullback_focused.yaml` | Tight bull channel pullback | Active | same | Sparse; tune grid |
| pa_mtr_reversal | `pa_mtr_reversal_focused.yaml` | Major trend reversal proxy | Active | same | Ultra-sparse on focused grid |

---

## 2. Refined grids (`*_refined_v1.yaml`)

| Strategy | File | Purpose | Status | Notes |
|----------|------|---------|--------|-------|
| failed_orb | `failed_orb_refined_v1.yaml` | Tighter failed-ORB grid | Active | Post–batch 1 refinement |
| gap_acceptance_failure | `gap_acceptance_failure_refined_v1.yaml` | Tighter gap grid | Active | |

---

## 3. Tuned grids (`*_tuned_v1.yaml`, `*_tuned_v2.yaml`)

| Strategy | File | Purpose | Status | Notes |
|----------|------|---------|--------|-------|
| bollinger_squeeze_breakout | `bollinger_squeeze_breakout_tuned_v1.yaml` | Cost-aware tuning v1 | Active | `layer1_v2_batch1_tuned_qqq_2023_2024_v1` |
| bollinger_squeeze_breakout | `bollinger_squeeze_breakout_tuned_v2.yaml` | Cost-aware tuning v2 | Reference | Paired with tuned v2 Layer 1 manifest |
| rsi_failure_swing | `rsi_failure_swing_tuned_v1.yaml` | Cost-aware tuning v1 | Active | batch1 tuned track |

---

## 4. Completion grids (Strategy Library v2 — nine completion plugins)

Used by `run_layer1_v2_completion.py` with `*_focused.yaml` per strategy (same files as in section 1 for those nine names).

| Strategy | File | Status in completion | Result root |
|----------|------|---------------------|-------------|
| macd_momentum_turn | `macd_momentum_turn_focused.yaml` | Strict candidates | `layer1_v2_completion_qqq_2023_2024` |
| stochastic_oversold_cross | `stochastic_oversold_cross_focused.yaml` | Strict | same |
| cci_extreme_snapback | `cci_extreme_snapback_focused.yaml` | Strict | same |
| adx_dmi_trend_continuation | `adx_dmi_trend_continuation_focused.yaml` | Relaxed-only / diagnostic | same |
| supertrend_atr_flip | `supertrend_atr_flip_focused.yaml` | Strict | same |
| multi_day_level_trap | `multi_day_level_trap_focused.yaml` | Strict | same |
| prior_close_reclaim | `prior_close_reclaim_focused.yaml` | Strict | same |
| sma20_reclaim_reject | `sma20_reclaim_reject_focused.yaml` | **No candidates** | same (empty selection) |
| large_candle_failure | `large_candle_failure_focused.yaml` | **No candidates** | same (empty selection) |

---

## 5. Deferred / weak grids (do not delete)

| File | Strategy | Status | Notes |
|------|----------|--------|-------|
| `sma20_reclaim_reject_focused.yaml` | sma20_reclaim_reject | Deferred | No rows passed strict/relaxed in completion manifest |
| `large_candle_failure_focused.yaml` | large_candle_failure | Deferred | No candidates |

---

## 6. Deprecated / reference only

None explicitly marked deprecated in-repo. `*_tuned_v2` and older batch1 artifacts serve as **historical reference** alongside current focused grids.

---

## Maintenance

- New strategies: add a row here when adding `*_focused.yaml`.
- Layer 2 combiner uses **candidate YAMLs**, not these grids directly, except that candidates were generated from these sweeps.
