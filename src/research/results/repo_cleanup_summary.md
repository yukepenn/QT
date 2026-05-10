# Repo cleanup summary (2026-05-10)

## 1. Purpose

Trim **stale / superseded research artifacts** and **local-heavy sweep outputs** before global Layer 1 / Layer 2 work, without touching correctness infrastructure (source, active configs, active tests, active candidate libraries).

## 2. What was deleted

### Tracked (git rm)

- `src/research/results/layer1_all10_qqq_2020_20260430_v1/` — **PRE_HARDENING_STALE.md**
- `src/research/results/layer1_all10_qqq_v1/` — **STALE.md** (legacy seed baseline)
- `src/combiner/results/layer2_qqq_2020_20260430_v2_relaxed/` — **PRE_HARDENING_STALE.md**
- `src/combiner/results/layer2_qqq_v1/` — **STALE.md** (legacy Layer 2 seed)

### Local / untracked

- All children under `src/strategies/testing_parameters_results/` except **`.gitkeep`** (if present)
- Untracked heavy diagnostics under several Layer 2 roots: `candidate_precompute_profile.csv`, `feature_store_stats.json`, optional `candidate_precompute_profile_summary.*` under PA Batch A / B/C v2 / repaired v3 / v2 completion variant trees
- `src/research/results/pa_batch_bc_gate_diagnostics_v3_preflight/pa_gate_rows.jsonl` (local diagnostic dump)

## 3. What was kept

- All **Python source** under `src/` (including combiner/research/walkforward **code**)
- **Active** Layer 1/2 roots: post-hardening all-10 libraries, PA Batch B/C **v3 / repaired v3**, v2 completion stacks, mini-WFO curated exports, hardening docs
- **`tests/**`** — no test files removed (audit only)
- **Legacy YAML configs** `layer2_qqq_v1.yaml`, `layer2_sweep_qqq_v1.yaml`, `layer2_qqq_2020_20260430_v2_relaxed.yaml` (+ sweeps) — **kept** as historical references; **RESULTS_INDEX** / **CONFIG_INDEX** now state candidate roots were removed from the working tree

## 4. Active roots after cleanup (non-exhaustive)

See **`src/research/results/RESULTS_INDEX.md`** and **`src/combiner/results/RESULTS_INDEX.md`**. Highlights:

- `layer1_all10_qqq_{2020,2023,2025}_*_posthardening_v1/`
- `layer2_qqq_*_posthardening_{strict,relaxed}_v1/`
- PA B/C: `layer1_pa_batch_bc_tuned_qqq_2023_2024_v3/`, `layer2_qqq_pa_batch_bc_repaired_v3_2023_2024/`, related diversity / repair docs

## 5. Stale roots removed

Listed in §2; replacements documented in **RESULTS_INDEX** § “Removed from repository”.

## 6. Tests audit

- **`src/research/results/test_suite_cleanup_audit.csv`** / **`.md`**: **73** files, all **`KEEP`** or **`REVIEW`** only for parser edge cases; **no** automatic test deletion.

## 7. Validation

Post-change: `pytest -q`, `compileall`, `loader.py --list`, three PA/failed_orb parity smokes, boundary greps, no `*.py` under `src/*/results/`, heavy-path `git ls-files` check — recorded in **NEXT_HANDOFF.md**.

## 8. Remaining cleanup candidates (manual / MEDIUM)

- Older **PA Batch A/B/C intermediate** research folders not marked STALE — review against **PROJECT_STATUS** before deletion
- **`layer2_qqq_v2_relaxed/`** (combiner) — legacy naming; still **REVIEW_MANUAL**
- **`src/research/results/artifact_cleanup_audit_after.csv`** — historical audit rows referencing deleted paths (informational)
- Any future **`sweep_*` / `top_runs/`** under result roots — keep **gitignored** / local only per **ARTIFACT_POLICY.md**

## 9. Next recommended step

**Global Layer 1 / global Layer 2 design** (windowing, symbol universe, post-hardening baseline pointers) — **not** PA B/C v4 tuning, **not** mini-WFO execution until that design is explicit.
