# PA Batch B/C — diversity repair summary (climax focus)

## 1. Purpose

Resolve whether **`pa_climax_reversal`** strict exports were **selector-collapsed** vs **single-mask limited**, then repair Layer 1 exports and optionally run **reduced Layer 2** on the repaired root.

## 2. Why v3 Layer 1 still “failed” diversity

Strict **top-5** YAMLs were **score-ranked** within a pool where **many rows share the same discrete entry path**; climax exports were **not** exploring lower-ranked strict rows.

## 3. Raw sweep diversity audit

Script: `src/research/sweep_result_signal_diversity.py`  
Output: `pa_batch_bc_raw_signal_diversity_v3/` + `raw_signal_diversity_summary.md`

Headline: **176** strict climax rows; **5** distinct `pure_signal_hash` values already within the **top-100** score-sorted strict pool (**2** @ top-20, **2** @ top-50, **5** @ top-100). Close-trend strict pool **895** rows with **26** unique hashes @ top-100.

## 4. Repaired candidate root

Exporter: `src/research/export_diverse_candidates_from_results.py`  
Root: `layer1_pa_batch_bc_tuned_qqq_2023_2024_v3/selected_candidates_repaired/` (**6** YAMLs + `selected_candidates.csv` + `diversity_repair_summary.md`).

## 5. Climax cap vs diversification

**Not capped:** exporter pulled **three** distinct climax strict rows (distinct `pure_signal_hash` at `hash_pick_rank==1`).

## 6. Fast-context check

`selected_candidates_repaired/candidate_fast_context_check.md` — **all `ok`**.

## 7. Layer 2 repaired v3

Ran **diagnostics**, **96-combo sweep** (`sweep_20260510_220219/`), **postprocess** (dedupe + cost stress; **no** `behavior_unique` because sweep used `--detail-top 0`).  
Summary: `src/combiner/results/layer2_qqq_pa_batch_bc_repaired_v3_2023_2024/layer2_pa_batch_bc_repaired_v3_summary.md`.

## 8. Decision

- **Layer 1 repair path:** **validated** (H1 confirmed).
- **Layer 2 repaired:** executed; combiner decision **`PROCEED_TO_PA_BATCH_BC_MINI_WFO_DESIGN`** (design-only follow-up; optional behavior rerun documented in Layer 2 summary).

## 9. Explicit non-runs

- **mini-WFO / full WFO / live/paper:** not run.

## 10. Next step

Author **mini-WFO design** (single doc) when you start that phase; optionally **re-sweep Layer 2 with `--detail-top 8`** locally to populate `behavior_unique_*` without committing `top_runs/` (keep gitignored).
