# Artifact policy

This repo is a **research framework**. Keep committed artifacts small, curated, and reproducible.

## 1. Source code

Commit:

- `src/**` (modules)
- `tests/**`
- `README.md`, `PROJECT_STATUS.md`, and curated docs under `src/research/results/`
- `src/combiner/configs/*.yaml`, `src/strategies/parameters/*.yaml`, `src/strategies/testing_parameters/*_focused.yaml`

## 2. Local data

Never commit:

- `data/raw/**` (local IBKR parquet / raw bars)

## 3. Caches

Never commit:

- `.cache/**`
- `data/cache/**`
- `*.npy`, `*.npz`, `*.memmap`

Notes:

- **Signal cache** lives under `.cache/qt/candidate_signals` and is always safe to delete (rebuildable).
- **FeatureStore** is in-memory only and produces no persistent cache.

## 4. Curated research artifacts (commit)

Commit curated, small artifacts that summarize experiments:

- Candidate libraries:
  - `selected_candidates.csv`
  - `selected_candidates/*.yaml`
  - `sweep_manifest.csv` (and optional `.md`)
  - summary MDs (e.g. `layer1_*_summary.md`)
- Layer 2 summaries:
  - `top_unique_systems.csv` / `.md`
  - `fixed_run_summary.csv` / `.md`
  - `diagnostics/*.csv` and `diagnostics_summary.md`
  - `behavior_unique_systems.csv` / `.md`
  - `cost_stress/cost_stress_results.csv` and `cost_stress_summary.md`
  - `cost_robust_systems.csv` / `.md`
  - profile summaries like `candidate_precompute_profile_summary.csv` / `.md`

## 5. Generated heavy artifacts (do not commit)

Do not commit:

- `top_runs/` folders
- detailed per-run folders (`run_*`, `fixed_runs/`, `sweep_*/`) unless explicitly curated and small
- `candidate_signal_log.csv`, `rejected_signals.csv`
- full `trades.csv` unless explicitly curated and intentionally kept small

## 6. Tests

- `tests/` must remain committed.
- Do not treat tests as temporary artifacts.

## 7. Cleanup policy (safe deletions)

Safe to delete locally:

- `__pycache__/`, `.pytest_cache/`, `*.pyc`, `*.pyo`, `*.nbc`, `*.nbi`
- `_tmp*.py`, `temp*.py`, `scratch*.py` (and yaml variants)
- `_smoke*` / `_equiv*` output folders under `src/**/results/`
- `.cache/**` (rebuildable)

Not safe to delete without explicit intent:

- `selected_candidates/*.yaml`
- curated summaries and indexes under `src/research/results/` and `src/combiner/results/`
- curated Layer 3 smoke summaries under `src/walkforward/results/**` when intentionally kept small

## 8. Walk-forward smoke outputs (`src/walkforward/results/`)

Treat like Layer 2 results roots:

- **Commit:** aggregate CSVs (`fold_summary.csv`, `system_summary.csv`, `stitched_summary.csv`, `cost_stress_by_fold.csv`, `monthly_breakdown_all.csv`, `daily_trade_number_by_fold.csv`, `layer3_smoke_summary.md`) and small per-fold `metrics.json` / `summary.csv` when curated.
- **Do not commit:** `compact_trades.csv` when large, full `trades.csv`, `equity.csv`, `candidate_signal_log.csv`, `rejected_signals.csv`, `top_runs/`, dense matrices — same rules as sections 4–5 for Layer 2/research roots.
- Per-fold Layer 2 profiling dumps under smoke (`candidate_precompute_profile*.csv`, `candidates_used.csv`, `feature_store_stats.json`) should remain local — see `.gitignore` rules under `src/walkforward/results/`.
- **Diagnosis v1** (`layer3_smoke_v1_diagnosis_qqq_components/`): commit aggregate CSVs + `layer3_smoke_diagnosis_summary.md` + `layer3_smoke_summary.md`; large per-fold trees optional/local unless intentionally curated small.

