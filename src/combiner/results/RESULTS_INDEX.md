# Combiner results index (`src/combiner/results/`)

This index classifies committed Layer 2 result roots without deleting them.

## A. Active / current

- **`layer2_qqq_2020_20260430_posthardening_strict_v1/`**
  - **status**: active baseline (strict)
  - **window**: 2020‑01‑01 → 2026‑04‑30
  - **key summaries**: `top_unique_systems.md`, `fixed_run_summary.md`, `cost_stress/cost_stress_summary.md`, `diagnostics/diagnostics_summary.md`
  - **keep**: yes

- **`layer2_qqq_2020_20260430_posthardening_relaxed_v1/`**
  - **status**: active baseline (relaxed)
  - **window**: 2020‑01‑01 → 2026‑04‑30
  - **key summaries**: `top_unique_systems.md`, `fixed_run_summary.md`, `cost_stress/cost_stress_summary.md`, `diagnostics/diagnostics_summary.md`
  - **keep**: yes

- **`layer2_qqq_2025_20260430_recent_check_v1/`**
  - **status**: active recent-window check
  - **window**: 2025‑01‑01 → 2026‑04‑30
  - **key summaries**: `layer2_recent_2025_summary.md`, `top_unique_systems.md`, `fixed_run_summary.md`, `diagnostics/diagnostics_summary.md`
  - **keep**: yes

- **`layer2_qqq_v2_batch1_2023_2024/`**
  - **status**: active Batch 1 reduced Layer 2
  - **window**: 2023‑01‑01 → 2024‑12‑31
  - **key summaries**: `layer2_v2_batch1_summary.md`, `top_unique_systems.md`, `fixed_run_summary.md`, `cost_stress/cost_stress_summary.md`, `behavior_unique_systems.md`, `diagnostics/diagnostics_summary.md`
  - **keep**: yes (heavy `sweep_*`, `run_*`, `fixed_runs/`, `top_runs/` remain gitignored)

- **`layer2_qqq_v2_batch1_tuned_2023_2024_v1/`**
  - **status**: active Batch 1 **tuned** reduced Layer 2 (strict squeeze + RSI)
  - **window**: 2023‑01‑01 → 2024‑12‑31
  - **key summaries**: `layer2_v2_batch1_tuned_summary.md`, `top_unique_systems.md`, `fixed_run_summary.md`, `cost_stress/cost_stress_summary.md`, `behavior_unique_systems.md`, `cost_robust_systems.md`, `fixed_vs_sweep_comparison.md`, `diagnostics/diagnostics_summary.md`
  - **keep**: yes (heavy `sweep_*`, `run_*`, `fixed_runs/`, `top_runs/`, `rank_by_*.csv` remain gitignored)

- **`layer2_qqq_v2_batch1_tuned_v2_2023_2024/`**
  - **status**: **skipped** (no Layer 1 YAMLs for tuned_v2)
  - **summary only**: `layer2_v2_batch1_tuned_v2_summary.md`

## B. Reference / historical

- **`layer2_qqq_2023_20260430_posthardening_strict_v1/`**, **`layer2_qqq_2023_20260430_posthardening_relaxed_v1/`**
  - **status**: reference
  - **window**: 2023‑01‑01 → 2026‑04‑30
  - **keep**: yes

## C. Stale / superseded (do not use for new decisions)

- **`layer2_qqq_2020_20260430_v2_relaxed/`**
  - **status**: stale for ranking (pre-hardening candidate root)
  - **summary**: `layer2_v2_2020_summary.md` already warns about staleness
  - **replacement**: post-hardening 2020 strict/relaxed roots

- **`layer2_qqq_v1/`**
  - **status**: legacy seed baseline / recovery template
  - **replacement**: post-hardening 2020/2025 baselines

- **`layer2_qqq_v2_relaxed/`**
  - **status**: legacy / unclear naming; keep for history
  - **replacement**: post-hardening roots

## Notes

- Large per-run artifacts (e.g. `top_runs/`, detailed `run_*` folders) are intentionally gitignored.
- Committed roots are intended to remain **lightweight**: keep curated summaries/CSVs/MDs, not full `equity.csv`/`trades.csv` dumps.

