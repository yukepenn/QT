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
- **Sweep folder:** `sweep_20260510_220219/`
- **Note:** sweep used **`--detail-top 0`** to avoid generating heavy `top_runs/` trade CSVs under the result root (artifact hygiene). **Behavior-unique hashing was therefore skipped** in postprocess; for a full **behavior_unique ≥ 2** gate, re-run locally with e.g. **`--detail-top 8`** and postprocess with **`--write-behavior-unique`**.

## 5. Representative economics (from `rank_by_total_r.csv`)

- **Best `total_r` row:** `combo_id=96`, `pa_batch_bc_core`, `top_per_strategy=2`, `max_trades_per_day=2`, `daily_max_loss_r=-2`, `cooldown_after_loss_minutes=15`, `score_adjusted_priority` — about **48.66** `total_r`, **1.245** `profit_factor`, **517** trades @ baseline slip **0.01** (close-trend-heavy fills; see sweep CSV for exact floats).

## 6. Postprocess

- **Dedupe:** `dedupe_top=30` → `top_unique_systems.csv` / `.md`, `top_unique_run_map.csv` (empty detailed map when no `top_runs/`).
- **Cost stress:** `cost_stress_top=15` on unique slice — leading rows are **`pa_climax` / `PA_CLIMAX_REVERSAL_DIVERSE_001`**; **0.02** slip shows **`total_r ≈ 3.03`**, **`profit_factor ≈ 1.259`**, label **`robust_positive_at_0_02`** (see `cost_stress/cost_stress_summary.md`). **Portfolio `pa_batch_bc_core` rows are not guaranteed to appear in the top-15 cost slice**; review `rank_by_total_r.csv` / full sweep `results.csv` for core **0.02** if needed.

## 7. Decision (exactly one)

### **PROCEED_TO_PA_BATCH_BC_MINI_WFO_DESIGN**

Rationale:

1. **Layer 1 diversity repair validated** (`strategy_diversity_summary.csv`: **3 / 3** unique `pure_signal_hash` per family on repaired YAMLs).
2. **Layer 2 sweep** shows **healthy portfolio-scale `total_r`** on `pa_batch_bc_core` with repaired IDs.
3. **0.02** cost stress on the inspected **unique_rank slice** is **not** the v2 failure mode for the dominant climax row (**PF > 1.05**, **`total_r` > 0 @ 0.02** on that slice).
4. **mini-WFO is still not executed** — next step is **design-only** documentation in a future explicit phase, plus optional **behavior rerun** as above before freezing a system.

## 8. Explicit non-runs

- **mini-WFO / full WFO / live:** not executed.
