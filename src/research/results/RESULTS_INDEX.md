# Research results index (`src/research/results/`)

This index classifies **result roots** without moving or deleting them.

## A. Active / current

- **PA Batch A (price-action branch — planning + smokes)** — curated docs:
  - `pa_batch_a_plan.md`, `pa_repo_formatting_check.md`, `pa_feature_foundation_summary.md`
  - `pa_batch_a_parity_smoke.{md,csv}`, `pa_batch_a_jan2025_smoke.{md,csv}`, `pa_batch_a_implementation_summary.md`
  - **status:** feature foundation + four strategies in `loader`; formal economics in **`layer1_pa_batch_a_qqq_2023_2024/`** (see below).
  - **keep:** yes

- **PA Batch B (implementation + smokes)** — `pa_batch_b_c_implementation_plan.md`, `pa_batch_b_implementation_summary.md`, `pa_batch_b_parity_smoke.{md,csv}`, `pa_batch_b_jan2025_smoke.{md,csv}`
  - **status:** four plugins; formal Layer 1 economics in **`layer1_pa_batch_bc_qqq_2023_2024/`** (with Batch C)
  - **keep:** yes

- **PA Batch C (+ library handoff)** — `pa_batch_c_implementation_summary.md`, `pa_batch_c_parity_smoke.{md,csv}`, `pa_batch_c_jan2025_smoke.{md,csv}`, `pa_overlap_refinements_backlog.md`, `pa_strategy_library_completion_summary.md`
  - **status:** two plugins; formal Layer 1 economics in **`layer1_pa_batch_bc_qqq_2023_2024/`**
  - **keep:** yes

- **`layer1_pa_batch_bc_qqq_2023_2024/`**
  - **status:** formal **PA Batch B + C** Layer 1 (QQQ 2023–01–01 → 2024–12–31), tag `layer1_pa_batch_bc_qqq_2023_2024`
  - **purpose:** six `*_focused.yaml` sweeps → manifest → strict selection (**5** YAMLs, **`pa_buy_sell_close_trend` only**); `signal_rate_diagnosis.*`, optional `diagnostic_relaxed_selection/` (DIAGNOSTIC ONLY); `candidate_fast_context_check.*`
  - **decision:** **`TUNE_PA_BATCH_BC_GRIDS_FIRST`** (`layer1_pa_batch_bc_summary.md`). **PA Batch B/C Layer 2 / mini-WFO / full WFO / live not run.**
  - **keep:** yes

- **`layer1_pa_batch_bc_tuned_qqq_2023_2024_v1/`**
  - **status:** PA Batch B+C **tuned grids v1** Layer 1 (QQQ 2023–01–01 → 2024–12–31), tag `layer1_pa_batch_bc_tuned_qqq_2023_2024_v1`
  - **purpose:** tuned `*_tuned_v1.yaml` sweeps → manifest → strict selection (**5** YAMLs, **`pa_climax_reversal` only**); tuned `signal_rate_diagnosis.*`; `candidate_fast_context_check.*`; optional `diagnostic_relaxed_selection/` (**DIAGNOSTIC ONLY**; CSV + `DIAGNOSTIC_ONLY.md` only)
  - **decision:** **`TUNE_PA_BATCH_BC_GRIDS_AGAIN`** (`layer1_pa_batch_bc_tuned_v1_summary.md`). **PA Batch B/C Layer 2 / mini-WFO / full WFO / live not run.**
  - **keep:** yes

- **`layer1_pa_batch_a_tuned_qqq_2023_2024_v1/`**
  - **status:** PA Batch A **tuned grids v1** Layer 1 (QQQ 2023–01–01 → 2024–12–31)
  - **purpose:** `*_tuned_v1.yaml` sweeps → **10** strict YAMLs (trading-range + failed-trap); `signal_rate_diagnosis.*`, `layer1_pa_batch_a_tuned_v1_summary.md`
  - **decision:** **`PROCEED_TO_PA_BATCH_A_REDUCED_LAYER2_DESIGN`**; design sketch `reduced_layer2_pa_batch_a_tuned_design.md`
  - **Layer 2:** executed reduced Layer 2 under `src/combiner/results/layer2_qqq_pa_batch_a_tuned_2023_2024_v1/` → decision **`TUNE_PA_BATCH_A_GRIDS_AGAIN`** (cost stress @ 0.02 fails for core)
  - **keep:** yes

- **`layer1_pa_batch_a_qqq_2023_2024/`**
  - **status:** formal PA Batch A Layer 1 (QQQ 2023–01–01 → 2024–12–31)
  - **purpose:** focused sweeps → `sweep_manifest.*` → strict `select_candidates` (**4** YAMLs, `pa_failed_range_breakout_trap` only) + optional `diagnostic_relaxed_selection/` + `signal_rate_diagnosis.*` + `candidate_fast_context_check.*`
  - **decision:** **`TUNE_PA_BATCH_A_GRIDS_FIRST`** (`layer1_pa_batch_a_summary.md`). **PA Layer 2 / mini-WFO / full WFO not run.**
  - **keep:** yes

- **`layer1_all10_qqq_2020_20260430_posthardening_v1/`**
  - **status**: active baseline
  - **window**: 2020‑01‑01 → 2026‑04‑30
  - **purpose**: post-hardening Layer 1 manifest + selected candidate YAML library
  - **keep**: yes

- **`layer1_all10_qqq_2025_20260430_posthardening_v1/`**
  - **status**: active baseline (recent window)
  - **window**: 2025‑01‑01 → 2026‑04‑30
  - **purpose**: recent Layer 1 manifest + selected candidates
  - **keep**: yes

- **`layer1_v2_batch1_qqq_2023_2024/`**
  - **status**: active Strategy Library v2 Batch 1 Layer 1
  - **window**: 2023‑01‑01 → 2024‑12‑31
  - **purpose**: six-strategy capped sweeps → **20** selected YAMLs; manifest + `MANIFEST_CONSISTENCY_NOTE.md`
  - **Layer 2 follow-up:** `src/combiner/results/layer2_qqq_v2_batch1_2023_2024/layer2_v2_batch1_summary.md`
  - **keep**: yes

- **`layer1_v2_batch1_tuned_qqq_2023_2024_v1/`**
  - **status**: active Batch 1 **tuned** Layer 1 (squeeze + RSI only)
  - **window**: 2023‑01‑01 → 2024‑12‑31
  - **purpose**: tuned grids → **10** selected YAMLs; `sweep_manifest.*` + selection docs
  - **Layer 2 follow-up:** `src/combiner/results/layer2_qqq_v2_batch1_tuned_2023_2024_v1/layer2_v2_batch1_tuned_summary.md`
  - **keep**: yes

- **`batch1_cost_fragility_diagnostics_v1/`**
  - **status**: reference diagnostics pack (original Batch 1 Layer 2 cost attribution)
  - **keep**: yes (CSV + MD summaries only)

- **`strategy_library_v2_batch1_tuning_summary.md`**
  - **status**: Batch 1 tuning v1 narrative + decision (`TUNE_BATCH1_GRIDS_AGAIN`)
  - **keep**: yes

- **`strategy_library_v2_batch1_tuning_v2_summary.md`**
  - **status**: Batch 1 tuning v2 narrative + **`DEFER_BATCH1_AND_RETURN_TO_REFINED_FAILED_CORE`**
  - **keep**: yes

- **`layer1_v2_batch1_tuned_v2_qqq_2023_2024/`**
  - **status**: tuned_v2 Layer 1 manifest only (**no** `selected_candidates/*.yaml`)
  - **window**: 2023‑01‑01 → 2024‑12‑31
  - **keep**: yes (manifest + selection docs)

- **`batch1_tuned_v1_cost_diagnostics/`**
  - **status**: tuned_v1 winner trade-quality / bucket diagnostics
  - **keep**: yes

- **`layer2_v2_completion_tuning_plan.md`**, **`layer2_v2_completion_toxic_path_diagnosis.md`** (+ `.csv`)
  - **status**: Layer 2 v2 completion **tuned v1** planning + toxic-path diagnosis (QQQ 2023–2024)
  - **keep**: yes

- **`strategy_library_v2_completion_summary.md`** (+ `strategy_library_v2_completion_*.{md,csv}`)
  - **status**: Strategy Library v2 **completion** pack (9 new plugins + feature deltas + Jan smoke health)
  - **keep**: yes (no heavy sweep outputs)

- **`layer1_v2_completion_qqq_2023_2024/`**
  - **status**: Layer 1 **completion** QQQ 2023–2024 (nine strategies; full focused grids; manifest + **30** selected YAMLs)
  - **window**: 2023‑01‑01 → 2024‑12‑31
  - **purpose**: economics + candidate library for v2 completion track; summary `layer1_v2_completion_summary.md`
  - **Layer 2 follow-up:** `src/combiner/results/layer2_qqq_v2_completion_2023_2024/layer2_v2_completion_summary.md` (run plan `reduced_layer2_v2_completion_run_plan.md`; design `reduced_layer2_v2_completion_design.md`); **tuned v1** `src/combiner/results/layer2_qqq_v2_completion_tuned_v1_2023_2024/layer2_v2_completion_tuned_v1_summary.md` (plan `layer2_v2_completion_tuning_plan.md`; toxic-path diagnosis `layer2_v2_completion_toxic_path_diagnosis.md`); **tuned v2 high-trade** `src/combiner/results/layer2_qqq_v2_completion_tuned_v2_high_trade_2023_2024/layer2_v2_completion_tuned_v2_high_trade_summary.md` (plan `layer2_v2_completion_tuned_v2_high_trade_plan.md`)
  - **keep**: yes

- **`layer2_v2_completion_tuned_v2_high_trade_plan.md`**
  - **status**: tuned v2 high-trade rerank plan + gates
  - **keep**: yes

## B. Reference / engineering docs

- **Repo maintenance (2026-05-09):** `repo_maintenance_formatting_summary.md` (formatting-only pass; no source edits)
- **Research script audit:** `research_script_organization_audit.md` / `research_script_organization_audit.csv`
- **Testing grid index:** `src/strategies/testing_parameters/GRID_INDEX.md`
- **Hardening docs**: `hardening_*`, `rerun_plan_after_hardening.md`, `PRE_HARDENING_STALE.md` markers
- **Engineering summaries (Layer 2):**
  - `layer2_precompute_cleanup_plan.md`, `layer2_precompute_cleanup_summary.md`
  - `layer2_signal_cache_summary.md`
  - `feature_store_v1_plan.md`, `feature_store_v1_summary.md`
- **Pre‑Layer‑3 gate docs:**
  - `pre_layer3_cache_benchmark_plan.md`
  - `pre_layer3_cache_benchmark_comparison.csv`
  - `pre_layer3_cache_benchmark_summary.md`
  - `pre_layer3_cache_benchmark_full_summary.md` (may be SKIPPED if local benchmark outputs weren’t retained)
  - `pre_layer3_gate_readiness_summary.md`
- **Data coverage docs:** `data_backfill_spy_qqq_2020_20260430/` (SPY incomplete; QQQ is the research symbol)

## C. Stale / superseded (keep for history; do not use for new decisions)

- **`layer1_all10_qqq_2020_20260430_v1/`**
  - **status**: stale (pre-hardening)
  - **marker**: includes `PRE_HARDENING_STALE.md`
  - **replacement**: `layer1_all10_qqq_2020_20260430_posthardening_v1/`

- **`layer1_all10_qqq_v1/`**
  - **status**: legacy seed baseline (pre post-hardening reruns)
  - **replacement**: post-hardening 2020/2025 roots

## Notes

- **Do not delete** `selected_candidates/*.yaml` or curated summaries.
- Heavy sweep folders are intentionally gitignored elsewhere; this folder contains curated artifacts and docs.

