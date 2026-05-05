# Recovery status — before restore actions (Phase 0)

Timestamp: emergency recovery audit (local workspace).

## Environment

- **PWD:** `D:\OneDrive - Washington University in St. Louis\QT`
- **Python:** 3.11.4 (from shell)
- **Git:** not initialized (no `.git` directory at repo root at audit time)
- **Remote:** none (git not initialized)

## Tree summary

### Present (combiner core)

- `src/combiner/__init__.py`
- `src/combiner/candidate.py`
- `src/combiner/simulator.py`
- `src/combiner/metrics.py`
- `src/combiner/run.py`
- `src/combiner/sweep.py`
- `src/combiner/configs/layer2_qqq_v1.yaml`
- `src/combiner/configs/layer2_sweep_qqq_v1.yaml`
- `src/combiner/configs/orb_vwap_simple.yaml`

### Missing

- **`src/combiner/postprocess.py`** — not present; must be recreated (generic CLI).

### Layer 2 results (`src/combiner/results/layer2_qqq_v1`)

**Present:**

- `layer2_summary.md` — content matches **older Phase 18** draft (short-window diagnostics note, fixed runs incomplete, cost stress “not run”).
- `cost_stress/cost_stress_summary.md` only (no `cost_stress_results.csv` alongside in audit).

**Missing / incomplete vs last known closeout:**

- `diagnostics/candidate_signal_summary.csv`
- `diagnostics/candidate_overlap_matrix.csv`
- `diagnostics/candidate_conflict_summary.csv`
- `diagnostics/diagnostics_summary.md`
- `sweep_*_sweep_v1_full/` (full sweep folder + `results.csv`)
- `fixed_run_summary.csv`, `fixed_run_summary.md`
- `fixed_runs/run_*` (seven tagged runs)
- `top_unique_systems.csv`, `top_unique_systems.md`
- `top_unique_run_map.csv`
- `cost_stress/cost_stress_results.csv` (if only summary exists, stress grid is incomplete)

## Layer 1 (`src/research/results/layer1_all10_qqq_v1`)

- **Folder exists:** `selected_candidates/`
- **Critical:** **`*.yaml` count = 0** in `selected_candidates/` (empty library).
- **Missing:** `selected_candidates.csv`, `sweep_manifest.csv`, `candidate_summary.md` (not found at audit).

**Suspected rollback:** Candidate YAMLs and Layer 2 generated CSVs were deleted or never synced to this copy; repo may pre-date validation closeout artifacts.

## What must be restored

1. **Source:** Add **`postprocess.py`** (generic; full grid dedupe key per spec).
2. **Layer 1:** Restore **~40 candidate YAMLs** (and optional manifest/summary) from backup, another machine, or re-run `select_candidates` **only after explicit approval** (can be time-consuming).
3. **Layer 2 artifacts:** After Layer 1 is restored, rerun only missing steps (diagnostics → postprocess summary; sweep if no `results.csv`; seven fixed runs + collect; dedupe + cost stress) **or** restore those files from backup.
4. **Docs:** Refresh `layer2_summary.md` from **actual CSVs** once they exist; update `README.md` / `PROGRESS.md` / `CHANGES.md` for recovery.
5. **Git:** `git init`, `.gitignore`, commit, push to `https://github.com/yukepenn/QT.git`.

## Blockers

- **Cannot** run combiner diagnostics, sweep, fixed runs, or cost stress until **`selected_candidates/*.yaml`** exist (and bar data available locally under `data/raw/ibkr` without running IBKR pull).
