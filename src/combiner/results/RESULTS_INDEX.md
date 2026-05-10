# Combiner results index (`src/combiner/results/`)

This index classifies committed Layer 2 result roots without deleting them.

**Note:** PA Batch A (`pa_*` plugins) now has a PA-only reduced Layer 2 root: `layer2_qqq_pa_batch_a_tuned_2023_2024_v1/` (QQQ 2023–2024). See `src/research/results/pa_batch_a_implementation_summary.md` and the Layer 1 tuned root `layer1_pa_batch_a_tuned_qqq_2023_2024_v1/`.

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

- **`layer2_qqq_v2_completion_2023_2024/`**
  - **status**: active **v2 completion** reduced Layer 2 (QQQ 2023–2024)
  - **window**: 2023‑01‑01 → 2024‑12‑31
  - **key summaries**: `layer2_v2_completion_summary.md`, `fixed_run_summary.md`, `top_unique_systems.md`, `behavior_unique_systems.md`, `cost_stress/cost_stress_summary.md`, `diagnostics/diagnostics_summary.md`, `candidate_precompute_profile_summary.{csv,md}` (root copies mirror diagnostics)
  - **keep**: yes (heavy `sweep_*`, `run_*`, `fixed_runs/`, `top_runs/` remain gitignored)

- **`layer2_qqq_v2_completion_tuned_v1_2023_2024/`**
  - **status**: active **v2 completion tuned v1** (QQQ 2023–2024)
  - **window**: 2023‑01‑01 → 2024‑12‑31
  - **key summaries**: `layer2_v2_completion_tuned_v1_summary.md`, `fixed_run_summary.md`, `top_unique_systems.md`, `behavior_unique_systems.md`, `cost_stress/cost_stress_summary.md`, `diagnostics/diagnostics_summary.md`, `diagnostics_completion_no_prior_close/`, `diagnostics_oscillator_momentum_trend/`, `candidate_precompute_profile_summary.{csv,md}` (root)
  - **keep**: yes (heavy `sweep_*`, `run_*`, `fixed_runs/`, `top_runs/` remain gitignored)

- **`layer2_qqq_v2_completion_tuned_v2_high_trade_2023_2024/`**
  - **status**: active **v2 completion tuned v2 high-trade** (QQQ 2023–2024)
  - **window**: 2023‑01‑01 → 2024‑12‑31
  - **key summaries**: `layer2_v2_completion_tuned_v2_high_trade_summary.md`, `fixed_run_summary.md`, `top_unique_systems.md`, `behavior_unique_systems.md`, `rank_high_trade_systems.md`, `high_trade_cost_review.md`, `cost_stress/cost_stress_summary.md`, `candidate_precompute_profile_summary.{csv,md}` (root)
  - **keep**: yes (heavy `sweep_*`, `run_*`, `fixed_runs/`, `top_runs/` remain gitignored)

- **`layer2_qqq_pa_batch_a_tuned_2023_2024_v1/`**
  - **status**: active PA-only reduced Layer 2 (tuned v1; research evaluation)
  - **window**: 2023‑01‑01 → 2024‑12‑31
  - **key summaries**: `layer2_pa_batch_a_tuned_summary.md`, `fixed_run_summary.md`, `top_unique_systems.md`, `behavior_unique_systems.md`, `cost_stress/cost_stress_summary.md`, `diagnostics/*`
  - **keep**: yes (heavy `sweep_*`, `run_*`, `fixed_runs/`, `top_runs/` remain gitignored)

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

