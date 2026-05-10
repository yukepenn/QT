# PA Batch A — tuned Layer 1 summary (v1, QQQ 2023–2024)

## 1. Purpose

Re-grid PA Batch A after `TUNE_PA_BATCH_A_GRIDS_FIRST`: improve **multi-family** strict candidates and **edge quality** before any **PA Layer 2**. This run uses **tuned v1** YAMLs (not `*_focused.yaml`).

## 2. Original baseline recap

From `layer1_pa_batch_a_qqq_2023_2024/`: **trading range** had **high activity, negative R**; **failed trap** was the **only** strict exporter (4 YAMLs); **tight channel** was **sparse**; **MTR** was **ultra-sparse**; decision **`TUNE_PA_BATCH_A_GRIDS_FIRST`**.

## 3. Tuned YAMLs

| File | raw grid | Main changes vs `*_focused` |
|------|----------|-----------------------------|
| `pa_trading_range_bls_hs_tuned_v1.yaml` | 576 | Added **`confirm_mode`** grid, higher **`trading_range_score_min` / `min_range_width_atr`**, **`target_mode` `range_mid`**, mixed stops |
| `pa_failed_range_breakout_trap_tuned_v1.yaml` | 576 | **`fail_window_bars`**, **`require_tr_regime`**, shorter entry start, more **target/stop** modes |
| `pa_tight_channel_pullback_tuned_v1.yaml` | 768 | Lower **`tight_bull_score_min`**, deeper **`max_pullback_depth_atr`**, **`block_climax`** toggle |
| `pa_mtr_reversal_tuned_v1.yaml` | 768 | **`pa_range_window`**, lower **`bear_channel_score_min`**, **`require_wedge_proxy`**, wider holds |

**Omitted (not in strategy code):** failed-trap `confirm_mode` / `min_break_atr`; MTR “test_mode” / trendline keys — see `layer1_pa_batch_a_tuning_plan.md`.

## 4. Sweep results

| strategy | result_rows | best_trades | best_total_r | best_PF | best_maxDD_r | notes |
|----------|-------------|-------------|--------------|---------|--------------|--------|
| pa_trading_range_bls_hs | 96 | 415 | 25.57 | 1.470 | -22.17 | Dedup 576→96 |
| pa_failed_range_breakout_trap | 144 | 378 | 34.89 | 1.329 | -43.21 | Dedup 576→144 |
| pa_tight_channel_pullback | 96 | 58* | 0.95† | inf† | 0.0 | *max trades; †manifest PF row is 1-trade |
| pa_mtr_reversal | 192 | 12‡ | 11.55† | inf† | 0.0 | ‡max trades; †PF-ranked artifact |

## 5. Signal-rate comparison

See `signal_rate_diagnosis.{md,csv}`. Headline: **trading range + failed trap** now both support **strict** YAMLs; **tight channel** has **more fills** but **fails PF/R gates**; **MTR** remains **below 30 trades** on all combos.

## 6. Candidate selection

**Strict:** thresholds in `candidate_selection_config.md`. **10** YAMLs (**5** + **5**). **`no_candidate_strategies.txt`:** tight channel, MTR.

**Diagnostic relaxed:** **not run** (two families already in strict set).

## 7. Candidate sanity

`candidate_fast_context_check.{csv,md}` — **all ok** (QQQ **2023-01-03→2023-01-31** spot window).

No **`LOOKAHEAD`** in PA **`required_features`** (unchanged foundation).

## 8. Interpretation

| Strategy | Class |
|----------|--------|
| pa_trading_range_bls_hs | **PROMISING_LAYER1_CANDIDATE** |
| pa_failed_range_breakout_trap | **PROMISING_LAYER1_CANDIDATE** |
| pa_tight_channel_pullback | **IMPROVED_BUT_NEEDS_MORE_TUNING** (rate up, edge still bad at strict gates) |
| pa_mtr_reversal | **TOO_SPARSE_NEEDS_FEATURE_OR_LOGIC_REVIEW** |

## 9. Decision (exactly one)

### **PROCEED_TO_PA_BATCH_A_REDUCED_LAYER2_DESIGN**

**Rationale**

- **Strict YAMLs** exist from **two** PA families — **`pa_trading_range`** and **`pa_range_breakout_failure` / failed trap** — meeting the multi-family bar for a **design-only** Layer 2 doc.
- **Trading range** flipped to **material positive R** on exported configs; **failed trap** improved **R / DD vs baseline** manifest row.
- **Parity / fast-context** healthy; **no implementation bug** flagged.
- **Tight channel / MTR** remain non-exported — acceptable as **non-core** until further tuning or logic review (explicitly **not** blocking the design doc).

## 10. Explicit non-runs

- PA **Layer 2** / **mini-WFO** / **full WFO** / **live/paper** — **not executed**.

## 11. Artifacts

Curated root: `src/research/results/layer1_pa_batch_a_tuned_qqq_2023_2024_v1/`  
Design-only Layer 2 sketch: `src/research/results/reduced_layer2_pa_batch_a_tuned_design.md`.
