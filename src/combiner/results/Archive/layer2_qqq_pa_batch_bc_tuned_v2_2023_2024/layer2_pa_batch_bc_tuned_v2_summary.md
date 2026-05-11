# PA Batch B/C tuned v2 — reduced Layer 2 summary (QQQ 2023–2024)

## 1. Purpose

Reduced **Layer 2** combiner evaluation on **strict** PA Batch B/C **tuned v2** candidates only (`pa_buy_sell_close_trend` + `pa_climax_reversal`), QQQ **2023-01-01 → 2024-12-31**. **Not** mini-WFO, full WFO, or live.

## 2. Inputs

- **Candidate root:** `src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v2/selected_candidates`
- **Strict YAMLs:** **10** (5 close-trend + 5 climax) — no relaxed/diagnostic Layer 1 rows
- **Configs:** `layer2_qqq_pa_batch_bc_tuned_v2_2023_2024.yaml`, `layer2_qqq_pa_batch_bc_tuned_v2_2023_2024_trade2.yaml` (fixed run #7), `layer2_sweep_qqq_pa_batch_bc_tuned_v2_2023_2024.yaml`
- **Signal cache:** `%LOCALAPPDATA%\QT\candidate_signals`

## 3. Candidate sets

- `pa_close_trend`, `pa_climax`, `pa_batch_bc_core` (+ diagnostic single-name sets in YAML for future use)

## 4. Diagnostics

- **Total precomputed signals (10 candidates):** **2570** (`pa_buy_sell_close_trend` **2315**, `pa_climax_reversal` **255**)
- **Overlap / conflict:** see `diagnostics/candidate_overlap_matrix.csv`, `candidate_conflict_summary.csv`
- **Narrative:** `diagnostics_interpretation.md`

## 5. Fixed runs (baseline slippage 0.01)

| tag | candidate_set | top | max_trades/day | daily_max_loss_r | cooldown | total_r | PF | maxDD_r | trades | notes |
|-----|---------------|-----|----------------|------------------|----------|---------|-----|---------|--------|-------|
| fixed_pa_close_trend_top1 | pa_close_trend | 1 | 1 | -1.5 | 0 | 41.56 | 1.260 | -13.78 | 461 | strong single-candidate |
| fixed_pa_close_trend_top5 | pa_close_trend | 5 | 1 | -1.5 | 0 | 41.56 | 1.260 | -13.78 | 461 | extra YAMLs fully conflicted out |
| fixed_pa_climax_top1 | pa_climax | 1 | 1 | -1.5 | 0 | 6.23 | 1.373 | -6.29 | 51 | healthy PF, low n |
| fixed_pa_climax_top5 | pa_climax | 5 | 1 | -1.5 | 0 | 6.23 | 1.373 | -6.29 | 51 | duplicates |
| fixed_pa_core_top1 | pa_batch_bc_core | 1 | 1 | -1.5 | 0 | 48.59 | 1.258 | -16.43 | 469 | portfolio |
| fixed_pa_core_top2 | pa_batch_bc_core | 2 | 1 | -1.5 | 0 | 48.59 | 1.258 | -16.43 | 469 | same fills as top1 |
| fixed_pa_core_top2_trade2 | pa_batch_bc_core | 2 | 2 | -2.0 | 15 | 49.60 | 1.270 | -16.69 | 505 | **trade #2 helps slightly** (+36 trades, +1.0 R) |

**Fixed-run gate:** **PASS** (both single-family top1 paths positive; core not catastrophic vs best single family; trade-2 variant not degrading).

## 6. Sweep

- **Grid:** **144** combos (3 × 3 × 2 × 2 × 2 × 2)
- **Precompute universe:** **6** candidates (max `top_per_strategy=3` across sets)
- **Wall clock (this machine):** precompute ~**11 s**, sweep ~**20 s** total
- **Sweep directory:** `sweep_20260510_211847/`
- **`top_unique`:** dominated by **`pa_climax` / `PA_CLIMAX_REVERSAL_001`** rows at the top of `combiner_score` (compact PF systems win the score sort despite smaller `total_r` than close-trend).
- **`pa_batch_bc_core` portfolio** appears lower in `top_unique` with **negative `combiner_score`** but **large `total_r` (~48.6)** — see rows 49–50 in `top_unique_systems.csv`.

## 7. Cost stress (0.01 / 0.02 / 0.03)

Source: `cost_stress/cost_stress_results.csv`, `cost_stress_summary.md` (top **10** unique rows re-simulated).

**Representative — `pa_climax` top1 (`PA_CLIMAX_REVERSAL_001`):**

| slip | total_r | profit_factor | label (CSV) |
|------|---------|---------------|-------------|
| 0.01 | 6.23 | 1.373 | — |
| 0.02 | 1.72 | 1.224 (PF_R **~0.95**, below **1.05**) | `robust_positive_at_0_02` (PF-only label in postprocess) |
| 0.03 | −2.65 | 1.076 | fragile |

**`pa_batch_bc_core` combo 97** was **outside** the cost-stress top-10 slice; baseline economics remain in `fixed_run_summary.csv` / sweep row (469 trades, **48.6 R @ 0.01**). Expect **close-trend-heavy** cost drag at **0.02** similar to other PA portfolio runs — verify locally if needed by raising `--cost-stress-top`.

## 8. Behavior dedupe

- **`behavior_unique` = 1** strong hash (only **`pa_climax` / 001** produced a distinct detailed path in the `top_runs` slice used for hashing).
- **15 / 30** inspected rows lacked usable detailed trades (hash misses) — dominated by **score-ranked climax** reruns.

## 9. Daily trade number

- **`max_trades_per_day=2`** (fixed `…_trade2`): **505** trades vs **469** at `=1`; **total_r** rises **48.59 → 49.60** (no catastrophic trade-#2 blow-up in this window).

## 10. Exit / cost context (Layer 1 diagnostics)

Aligns with **`pa_batch_bc_exit_diagnostics_v2/`**: close-trend remains **turnover / hold** sensitive; climax is **sparse but cleaner PF**. Layer 2 **does not overturn** that story.

## 11. Decision (exactly one)

### **TUNE_PA_BATCH_BC_GRIDS_AGAIN**

Reasons:

1. **`behavior_unique` collapsed to 1** — fails the “≥ 2 strong behavior hashes” portfolio readiness gate.
2. **Sweep score ordering** hides **close-trend** economic mass behind **negative `combiner_score`** rows even though **`total_r` is large** — needs either **grid / priority** rework or **score interpretation** before mini-WFO.
3. **`pa_climax` YAMLs are signal-identical** in this window (51 signals each) — strict “5× climax” is **not** five independent behaviors.

**Not** `PROCEED_TO_PA_BATCH_BC_MINI_WFO_DESIGN` (behavior gate unmet).  
**Not** `DEFER_PA_BATCH_BC` (families are not economically empty; issue is **router/dedupe/diversity**, not dead strategies).  
**Not** `FIX_IMPLEMENTATION_FIRST` (no invalid outputs observed).

## 12. Explicit non-runs

- **mini-WFO:** not executed (no design doc — gate not met)
- **full WFO / live / paper:** not executed
- **Layer 1:** not rerun

## 13. Next recommended step

- **Tune grids / priorities** to (a) differentiate climax candidates if possible, (b) reduce close-trend **cost fragility** under **0.02**, and/or (c) adjust **`combiner_score`** weighting if it should better reflect portfolio `total_r` for research sorting.
- Re-run a **narrow Layer 2** after a **tuned v3** Layer 1 pass; only then reconsider **mini-WFO design**.
