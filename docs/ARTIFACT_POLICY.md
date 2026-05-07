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

