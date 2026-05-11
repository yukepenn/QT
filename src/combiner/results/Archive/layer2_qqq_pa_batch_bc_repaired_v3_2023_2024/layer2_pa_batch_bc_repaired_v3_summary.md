# PA Batch B/C — repaired Layer 2 v3 summary (QQQ 2023–2024)

## 1. Purpose

Run a **narrow reduced Layer 2** on **diversity-repaired** Layer 1 candidates (`selected_candidates_repaired/`), after raw sweep audit showed **H1 (selector)** — multiple strict `pure_signal_hash` groups exist within the top-100 score pool for climax.

## 2. Inputs

- **Candidate root:** `src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v3/selected_candidates_repaired/selected_candidates` (**6** YAMLs: 3× `pa_buy_sell_close_trend`, 3× `pa_climax_reversal`)
- **Configs:** `layer2_qqq_pa_batch_bc_repaired_v3_2023_2024.yaml`, `layer2_sweep_qqq_pa_batch_bc_repaired_v3_2023_2024.yaml`
- **Precompute universe (sweep):** **4** candidates (union over `candidate_set × top_per_strategy` with `top_per_strategy ∈ {1,2}`)

## 3. Diagnostics

- **Diagnostics run:** `pa_batch_bc_core`, `top_per_strategy=2` → **4** candidates loaded, **1004** total precomputed signals (`pa_buy_sell_close_trend` **904**, `pa_climax_reversal` **100**).
- **Outputs:** `diagnostics/` (`candidate_signal_summary.csv`, overlap / conflict CSVs, `diagnostics_summary.md`).

## 4. Sweep

- **Grid:** **96** combos (`3 × 2 × 2 × 2 × 2 × 2`).
- **Latest sweep (behavior rerun):** `sweep_20260510_221442/` — **`--top 30`**, **`--detail-top 15`**, tag `sweep_repaired_v3_behavior` (**local / gitignored**; enables `top_runs/` trade logs for postprocess).
- **Earlier sweep (no behavior):** `sweep_20260510_220219/` used **`--detail-top 0`** — kept for reference **locally only**.

## 5. Representative economics

- **Best `total_r` (local `rank_by_total_r.csv` / `results.csv`):** combo **96**, `pa_batch_bc_core`, `top_per_strategy=2`, `max_trades_per_day=2`, `daily_max_loss_r=-2`, `cooldown_after_loss_minutes=15`, `score_adjusted_priority` — about **48.66** `total_r`, **1.245** `profit_factor`, **517** trades @ baseline slip **0.01** in the sweep row (see `results.csv` under the latest sweep dir).
- **Leaderboard note:** `combiner_score` sorts the **`top_unique`** slice toward **compact `pa_climax`** rows first; **portfolio `pa_batch_bc_core`** economics require **`rank_by_total_r.csv`** / **`results.csv`** (local `rank_by_*.csv` is gitignored).

## 6. Postprocess

- **Dedupe:** `dedupe_top=50` → `top_unique_systems.csv` / `.md`, `top_unique_run_map.csv`.
- **Behavior dedupe:** `behavior_dedupe_top=30`, **`--write-behavior-unique`** → `behavior_unique_systems.*`, `behavior_unique_run_map.csv` — see **`layer2_pa_batch_bc_repaired_v3_behavior_completion.md`** ( **`behavior_unique = 1`** strong hash; **15 / 30** rows missing `top_runs` ).
- **Cost stress:** `cost_stress_top=10` — see `cost_stress/cost_stress_summary.md` and `cost_stress_results.csv`.
- **Period breakdowns:** written under the sweep’s **`top_runs/`** (gitignored).

## 7. Decision (exactly one)

### **`TUNE_PA_BATCH_BC_GRIDS_AGAIN`**

Full evidence: **`layer2_pa_batch_bc_repaired_v3_behavior_completion.md`**.

High level:

1. Layer 1 **signal-mask** diversity repair remains valid (**3 / 3** per family on YAMLs).
2. **Trade-sequence (`behavior_unique`) diversity is still 1** on the completed slice — **not** sufficient to claim a multi-behavior combiner freeze.
3. **`cost_robust_systems`** is **climax-only** in this pass — avoid **single-family overclaim** for “the” robust system.
4. **`PROCEED_TO_PA_BATCH_BC_MINI_WFO_DESIGN` is retracted** until behavior **and** cost gates support it without the caveats above.

## 8. Explicit non-runs

- **mini-WFO / full WFO / live:** not executed.
