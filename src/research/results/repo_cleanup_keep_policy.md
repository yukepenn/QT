# Repo cleanup — keep policy

Hard **keep** (never delete in automated LOW-risk passes):

## Source / core

- `src/features/**`
- `src/strategies/**` (including `strategy/`, `common/`, `testing_parameters/`, `parameters/`, `loader.py`)
- `src/backtest/**`
- `src/combiner/**` **source** (`*.py`, `README` if any) — not obsolete **result** trees unless marked stale and approved
- `src/data/**`
- `src/utils/**`
- `src/walkforward/**` **source** (`*.py`, configs under `src/walkforward/configs/`)
- `src/research/*.py` (scripts, including `repo_cleanup_inventory.py`)
- `requirements.txt`, `pytest.ini`

## Tests

- `tests/**` — default **KEEP**; delete only after explicit audit, duplicate proof, and green `pytest`.

## Canonical docs / indexes

- `README.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `NEXT_HANDOFF.md`
- `docs/ARTIFACT_POLICY.md`
- `src/research/results/RESULTS_INDEX.md`
- `src/combiner/results/RESULTS_INDEX.md`
- `src/combiner/configs/CONFIG_INDEX.md`
- `src/strategies/testing_parameters/GRID_INDEX.md`

## Active research / combiner roots (PA B/C + global baselines)

- **PA B/C repaired (current):**  
  `src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v3/`  
  `src/research/results/pa_batch_bc_candidate_signal_diversity_repaired_v3/`  
  `src/research/results/pa_batch_bc_raw_signal_diversity_v3/`  
  `src/combiner/results/layer2_qqq_pa_batch_bc_repaired_v3_2023_2024/`
- **Post-hardening all-10 Layer 1 / Layer 2** windows documented in **RESULTS_INDEX.md** (e.g. `layer1_all10_qqq_*_posthardening_v1/`, `layer2_qqq_*_posthardening_*_v1/`).
- **Strategy Library v2 completion** artifacts referenced from **PROJECT_STATUS.md** / **RESULTS_INDEX.md**.
- **Refined failed ORB / mini-WFO** curated exports under `src/walkforward/results/` when listed as active train artifacts.

## Stale / superseded (eligible for removal when LOW-risk criteria met)

- Any result root containing **`PRE_HARDENING_STALE.md`**
- Any result root containing **`STALE.md`** with replacement documented in **RESULTS_INDEX.md**
- Legacy names: `layer1_all10_qqq_v1`, `layer2_qqq_v1`, pre-hardening `layer1_all10_qqq_2020_20260430_v1`, `layer2_qqq_2020_20260430_v2_relaxed` (removed from repo **2026-05-10**)
- **`src/strategies/testing_parameters_results/**`** — local sweep scratch (regenerable); keep optional **`.gitkeep`** only
- Untracked: `sweep_*`, `top_runs/`, `run_*`, `fixed_runs/`, raw `trades.csv`, `equity.csv`, `candidate_signal_log.csv`, `rejected_signals.csv`, `feature_store_stats.json`, raw `candidate_precompute_profile.csv` under result roots per **ARTIFACT_POLICY.md**

## Medium / high risk (manual approval only)

- Curated result roots **without** stale markers
- `selected_candidates` trees that are still the **active** input to a documented Layer 2 / WFO run
- Obsolete tests (only after audit + pytest proof)
