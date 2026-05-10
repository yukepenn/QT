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
| pa_trading_range_bls_hs | `pa_trading_range_bls_hs_focused.yaml` | PA trading-range BLS/HS long MVP | Active | `layer1_pa_batch_a_qqq_2023_2024/`, `layer1_pa_batch_a_tuned_qqq_2023_2024_v1/` | Superseded for selection by **tuned v1** (see `*_tuned_v1.yaml`) |
| pa_failed_range_breakout_trap | `pa_failed_range_breakout_trap_focused.yaml` | Failed rolling-range breakout trap | Active | same | Tuned v1: **5** strict YAMLs |
| pa_tight_channel_pullback | `pa_tight_channel_pullback_focused.yaml` | Tight bull channel pullback | Active | same | Tuned v1: no strict pass |
| pa_mtr_reversal | `pa_mtr_reversal_focused.yaml` | Major trend reversal proxy | Active | same | Tuned v1: no strict pass |

### PA Batch A — tuned grids v1 (`*_tuned_v1.yaml`)

| Strategy | File | Purpose | Status | Last known result root | Notes |
|----------|------|---------|--------|------------------------|-------|
| pa_trading_range_bls_hs | `pa_trading_range_bls_hs_tuned_v1.yaml` | Quality-biased range grid | Active | `src/research/results/layer1_pa_batch_a_tuned_qqq_2023_2024_v1/` | **5** strict YAMLs |
| pa_failed_range_breakout_trap | `pa_failed_range_breakout_trap_tuned_v1.yaml` | Failed-trap quality / regime / hold | Active | same | **5** strict YAMLs |
| pa_tight_channel_pullback | `pa_tight_channel_pullback_tuned_v1.yaml` | Loosened channel / pullback | Active | same | No strict (weak PF) |
| pa_mtr_reversal | `pa_mtr_reversal_tuned_v1.yaml` | Loosened MTR proxy | Active | same | No strict (sparse) |

### PA Batch B — implementation grids (`*_focused.yaml`)

| Strategy | File | Purpose | Status | Last known result root | Notes |
|----------|------|---------|--------|------------------------|-------|
| pa_broad_channel_zone | `pa_broad_channel_zone_focused.yaml` | Broad channel buy-zone | Active | `layer1_pa_batch_bc_qqq_2023_2024/` | ~288 raw; zero-trade QQQ 2023–2024 |
| pa_climax_reversal | `pa_climax_reversal_focused.yaml` | Climax fade | Active | same | ~288 raw; weak PF at high trade count |
| pa_second_entry_pullback | `pa_second_entry_pullback_focused.yaml` | Second-entry pullback | Active | same | ~288 raw; max ~8 trades |
| pa_wedge_reversal | `pa_wedge_reversal_focused.yaml` | Wedge reversal proxy | Active | same | ~288 raw; weak PF |

### PA Batch C — implementation grids (`*_focused.yaml`)

| Strategy | File | Purpose | Status | Last known result root | Notes |
|----------|------|---------|--------|------------------------|-------|
| pa_buy_sell_close_trend | `pa_buy_sell_close_trend_focused.yaml` | Strong-close continuation | Active | `layer1_pa_batch_bc_qqq_2023_2024/` | ~432 raw; **5** strict Layer 1 YAMLs |
| pa_generic_breakout_pullback | `pa_generic_breakout_pullback_focused.yaml` | Breakout pullback | Active | same | ~432 raw; zero-trade 2023–2024 |

### PA Batch B/C — tuned grids v1 (`*_tuned_v1.yaml`)

Purpose: grid/gate tuning after baseline `layer1_pa_batch_bc_qqq_2023_2024/` yielded strict candidates from **one** family only (see `layer1_pa_batch_bc_summary.md`). Expected result root: `src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v1/`.

Gate / exit diagnostics on tuned v1 YAMLs (QQQ 2023–2024 design aid; **not** a sweep): `src/research/results/pa_batch_bc_gate_diagnostics_v1/`, `src/research/results/pa_batch_bc_exit_diagnostics_v1/`.

| Strategy | File | Purpose | Status | Raw grid (v1) | Expected result root |
|----------|------|---------|--------|---------------|----------------------|
| pa_broad_channel_zone | `pa_broad_channel_zone_tuned_v1.yaml` | Recover signal rate from zero-trade baseline | To be swept | 864 | `layer1_pa_batch_bc_tuned_qqq_2023_2024_v1/` |
| pa_climax_reversal | `pa_climax_reversal_tuned_v1.yaml` | Tighten quality (high activity, weak edge) | To be swept | 1296 | same |
| pa_second_entry_pullback | `pa_second_entry_pullback_tuned_v1.yaml` | Increase trade count (tiny-n baseline) | To be swept | 1152 | same |
| pa_wedge_reversal | `pa_wedge_reversal_tuned_v1.yaml` | Tighten wedge proxy / context | To be swept | 432 | same |
| pa_buy_sell_close_trend | `pa_buy_sell_close_trend_tuned_v1.yaml` | Reduce hold-time/cost sensitivity while preserving edge | To be swept | 324 | same |
| pa_generic_breakout_pullback | `pa_generic_breakout_pullback_tuned_v1.yaml` | Recover signal rate from zero-trade baseline | To be swept | 1024 | same |

### PA Batch B/C — tuned grids v2 (`*_tuned_v2.yaml`)

Post-P0 diagnostics + post-key-fix Layer 1 rerun. Result root: `src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v2/`. Gate preflight: `src/research/results/pa_batch_bc_gate_diagnostics_v2_preflight/`.

| Strategy | File | Raw grid | Purpose |
|----------|------|---------:|---------|
| pa_broad_channel_zone | `pa_broad_channel_zone_tuned_v2.yaml` | 972 | `zone_max_frac` + regime/hold axes — **sweep skipped** (preflight finals 0) |
| pa_generic_breakout_pullback | `pa_generic_breakout_pullback_tuned_v2.yaml` | 576 | Loosen pullback/overlap/followthrough — **sweep skipped** (preflight 0) |
| pa_buy_sell_close_trend | `pa_buy_sell_close_trend_tuned_v2.yaml` | 576 | Longer holds + moderate filters |
| pa_climax_reversal | `pa_climax_reversal_tuned_v2.yaml` | 576 | Small hull around v1 |
| pa_second_entry_pullback | `pa_second_entry_pullback_tuned_v2.yaml` | 576 | Looser context/pullback |
| pa_wedge_reversal | `pa_wedge_reversal_tuned_v2.yaml` | 144 | Small wedge retest |

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
