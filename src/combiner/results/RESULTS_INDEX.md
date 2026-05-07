# Combiner results index (`src/combiner/results/`)

This index classifies committed Layer 2 result roots without deleting them.

## A. Active / current

- **`layer2_qqq_2020_20260430_posthardening_strict_v1/`**
  - **status**: active baseline (strict)
  - **window**: 2020‑01‑01 → 2026‑04‑30
  - **key summaries**: `top_unique_systems.md`, `fixed_run_summary.md`, `cost_stress/cost_stress_summary.md`
  - **keep**: yes

- **`layer2_qqq_2020_20260430_posthardening_relaxed_v1/`**
  - **status**: active baseline (relaxed)
  - **window**: 2020‑01‑01 → 2026‑04‑30
  - **key summaries**: `top_unique_systems.md`, `fixed_run_summary.md`, `cost_stress/cost_stress_summary.md`
  - **keep**: yes

- **`layer2_qqq_2025_20260430_recent_check_v1/`**
  - **status**: active recent-window check
  - **window**: 2025‑01‑01 → 2026‑04‑30
  - **key summaries**: `layer2_recent_2025_summary.md`, `top_unique_systems.md`, `fixed_run_summary.md`
  - **keep**: yes

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
- Some committed roots include large `equity.csv` files; treat them as **curated historical artifacts**, not as mandatory for new runs.

