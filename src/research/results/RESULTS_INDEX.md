# Research results index (`src/research/results/`)

This index classifies **result roots** without moving or deleting them.

## A. Active / current

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

- **`strategy_library_v2_completion_summary.md`** (+ `strategy_library_v2_completion_*.{md,csv}`)
  - **status**: Strategy Library v2 **completion** pack (9 new plugins + feature deltas + Jan smoke health)
  - **keep**: yes (no heavy sweep outputs)

- **`layer1_v2_completion_qqq_2023_2024/`**
  - **status**: Layer 1 **completion** QQQ 2023–2024 (nine strategies; full focused grids; manifest + **30** selected YAMLs)
  - **window**: 2023‑01‑01 → 2024‑12‑31
  - **purpose**: economics + candidate library for v2 completion track; summary `layer1_v2_completion_summary.md`
  - **Layer 2 follow-up:** `src/combiner/results/layer2_qqq_v2_completion_2023_2024/layer2_v2_completion_summary.md` (run plan `reduced_layer2_v2_completion_run_plan.md`; design `reduced_layer2_v2_completion_design.md`)
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

