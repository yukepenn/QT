# PA Batch B/C — tuned Layer 1 v2 summary (QQQ 2023–2024)

**Tag:** `layer1_pa_batch_bc_tuned_qqq_2023_2024_v2`  
**Curated root:** `src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v2/`

## 1. Purpose

Post-P0 **`normalized_param_key`** fixes and **diagnostic-driven** grids (not blind expansion): recover **`pa_buy_sell_close_trend`** economics after v1 hold cuts, keep **`pa_climax_reversal`** in a tight robustness band, loosen **`pa_second_entry_pullback`** slightly, small **`pa_wedge_reversal`** retest, and attempt to unblock **`pa_broad_channel_zone`** via **`signal.zone_max_frac`** plus **`pa_generic_breakout_pullback`** geometry.

## 2. Why previous PA Batch B/C Layer 1 runs are cautious

Sweeps before commit `307d90f` may have **dedupe-collapsed** distinct combos. **Tuned v2** is the first **post-key-fix** fully documented rerun for these YAML families.

## 3. Diagnostics used

- Gate / exit v1 packs (`pa_batch_bc_gate_diagnostics_v1/`, `pa_batch_bc_exit_diagnostics_v1/`).
- **Gate preflight v2:** `pa_batch_bc_gate_diagnostics_v2_preflight/` (first combo per tuned v2 YAML).

## 4. v2 YAML design

| Strategy | YAML | Raw grid | Blocker / intent |
|----------|------|---------:|-------------------|
| pa_broad_channel_zone | `pa_broad_channel_zone_tuned_v2.yaml` | 972 | Zone gate → **`zone_max_frac`** (default `1/3` ≡ legacy); grid orders **2/3 first** for preflight |
| pa_generic_breakout_pullback | `pa_generic_breakout_pullback_tuned_v2.yaml` | 576 | Pullback band / overlap / followthrough |
| pa_buy_sell_close_trend | `pa_buy_sell_close_trend_tuned_v2.yaml` | 576 | Longer **max_hold_minutes**, moderate body/trend |
| pa_climax_reversal | `pa_climax_reversal_tuned_v2.yaml` | 576 | Hull around v1 profitable band |
| pa_second_entry_pullback | `pa_second_entry_pullback_tuned_v2.yaml` | 576 | Context / depth slightly looser |
| pa_wedge_reversal | `pa_wedge_reversal_tuned_v2.yaml` | 144 | Small quality retest |

**Code:** `signal.zone_max_frac` added only on **`pa_broad_channel_zone`** (backward-compatible default).

## 5. Gate preflight

See `pre_sweep_gate_decision.md`. **`pa_broad_channel_zone`** and **`pa_generic_breakout_pullback`** remained **0 final signals** on first combo → **full sweeps skipped**. Others nonzero → swept.

## 6. Sweep results

| strategy | status | result_rows | best_trades | best_total_r | best_PF | best_maxDD_R | best_avg_bars_held |
|----------|--------|-------------|-------------|--------------|---------|--------------|-------------------|
| pa_broad_channel_zone | skipped_zero_signal_preflight | — | — | — | — | — | — |
| pa_generic_breakout_pullback | skipped_zero_signal_preflight | — | — | — | — | — | — |
| pa_buy_sell_close_trend | ok | 576 | 461 | 41.56 | 1.260 | −13.78 | 84.8 |
| pa_climax_reversal | ok | 576 | 51 | 6.23 | 1.373 | −6.29 | 9.3 |
| pa_second_entry_pullback | ok | 576 | 8 | 5.33 | 2.080 | −1.07 | 4.4 |
| pa_wedge_reversal | ok | 144 | 54 | −1.47 | 1.027 | −11.04 | 1.8 |

Details: `sweep_manifest.csv`, `sweep_manifest.md`.

## 7. Comparison (baseline vs v1 vs v2)

See `signal_rate_diagnosis.md`. Headline: **close-trend** regains strong PF vs v1; **climax** stays PF>1 with moderate n; **broad/generic** still blocked.

## 8. Candidate selection

- **Strict:** `candidate_selection_config.md` → **10 YAMLs** — **5×** `pa_buy_sell_close_trend`, **5×** `pa_climax_reversal`.
- **No strict:** `no_candidate_strategies.txt` lists broad/generic/second-entry/wedge.
- **Diagnostic relaxed:** `diagnostic_relaxed_selection/` — see **`DIAGNOSTIC_ONLY.md`**.

## 9. Candidate sanity

- Fast context (Jan 2023 smoke): **`candidate_fast_context_check.*`** — all **ok**.

## 10. Exit / cost diagnostics

- **`pa_batch_bc_exit_diagnostics_v2/`** — **0.02** stress on strict YAMLs; close-trend remains **max-hold-heavy**; climax **stop/target** balanced, low max_hold exits.

## 11. Interpretation (classification)

| Strategy | Tag |
|----------|-----|
| pa_buy_sell_close_trend | **PROMISING_LAYER1_CANDIDATE** / **PROMISING_BUT_COST_SENSITIVE** |
| pa_climax_reversal | **PROMISING_LAYER1_CANDIDATE** |
| pa_second_entry_pullback | **IMPROVED_BUT_SPARSE** |
| pa_wedge_reversal | **SIGNAL_RATE_OK_BUT_WEAK_EDGE** |
| pa_broad_channel_zone | **STILL_ZERO_TRADE** / **FIX_IMPLEMENTATION_FIRST** candidate |
| pa_generic_breakout_pullback | **STILL_ZERO_TRADE** / **DEFER** |

## 12. Decision

**PROCEED_TO_PA_BATCH_BC_REDUCED_LAYER2_DESIGN**

**Rationale:** Strict YAMLs exist from **two** PA Batch B/C families (**close-trend** + **climax**), fast-context clean, exit diagnostics show manageable (though cost-sensitive) profiles for the primary family.

**Design-only artifact:** `src/research/results/reduced_layer2_pa_batch_bc_tuned_v2_design.md` — **Layer 2 not executed**.

## 13. Explicit non-runs

- Layer 2 combiner **execution** not run  
- mini-WFO / full WFO / live / paper not run  
- No new strategies; no global shorts; no trailing stops  
