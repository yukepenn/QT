# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Latest commit before cleanup | `4601c7d` — `Docs(handoff): PA BC NEED staging label` |
| New commit | `1e0f2af` — tip of `main` after cleanup (`cea3a58` = `Chore(repo): clean stale research artifacts`; follow-up doc commits) |
| Push status | **Pushed** to `origin/main` |
| Working tree | Curated cleanup artifacts + doc/index updates only; **no** new `sweep_*` / `top_runs/` committed |
| Known untracked local-only | Regenerated **`repo_cleanup_inventory.csv`** may list local-only dirs; re-run `python src/research/repo_cleanup_inventory.py` after large local sweeps |

## B. Task scope

| | |
|--|--|
| Requested | Repo cleanup before global Layer 1/2: inventory, keep policy, LOW-risk deletes, test audit, index/doc updates |
| Completed | `repo_cleanup_inventory.py` + CSV/MD outputs; **`repo_cleanup_keep_policy.md`**, **`repo_cleanup_delete_plan.*`**, **`repo_cleanup_summary.md`**, **`test_suite_cleanup_audit.*`**; **`git rm`** four stale roots; cleared **`testing_parameters_results/`** children (keep **`.gitkeep`**); removed listed untracked heavy diagnostics; updated **README**, **PROJECT_STATUS**, **PROGRESS**, **CHANGES**, **RESULTS_INDEX** ×2, **CONFIG_INDEX**, **ARTIFACT_POLICY**, **`recovery_status_before.md`**, this file |
| Intentionally not done | MEDIUM/HIGH-risk result-root deletes; **no** test file deletions; **no** new Layer 1/2/WFO/live runs |

## C. Files changed

| Area | Paths |
|------|--------|
| Deleted (tracked) | `src/research/results/layer1_all10_qqq_2020_20260430_v1/**`, `layer1_all10_qqq_v1/**`, `src/combiner/results/layer2_qqq_2020_20260430_v2_relaxed/**`, `layer2_qqq_v1/**` |
| Deleted (local) | `src/strategies/testing_parameters_results/**` (except `.gitkeep`); untracked `feature_store_stats.json` / `candidate_precompute_profile*.csv` under several `layer2_*` roots; `pa_batch_bc_gate_diagnostics_v3_preflight/pa_gate_rows.jsonl` |
| Added / updated | `src/research/repo_cleanup_inventory.py`, `src/research/results/repo_cleanup_*.{csv,md}`, `test_suite_cleanup_audit.*`, root + index + policy docs above |
| Tests | **No** `tests/**` changes |

## D. Validation

| Check | Result |
|--------|--------|
| `pytest -q` | **363 passed** |
| `compileall` | **OK** |
| `loader.py --list` | **35** strategies |
| Parity (failed_orb, PA tuned v3 ×2) | **OK** (`TOTAL_MISMATCH_FIELDS approx=0`) |
| Boundary greps | **OK** — `LOOKAHEAD` only in documented feature names / guards; **`_feat_key`** / **`DfSignalStrategy`** not in tracked `*.py` |
| Heavy `git ls-files` pattern | **No hits** |
| `*.py` under `src/*/results/` | **None** |

## E. Cleanup results

| Metric | Value |
|--------|--------|
| Tracked roots removed | **4** (`layer1_all10_qqq_2020_20260430_v1`, `layer1_all10_qqq_v1`, `layer2_qqq_2020_20260430_v2_relaxed`, `layer2_qqq_v1`) |
| `testing_parameters_results` | Children cleared (LOW-risk local scratch) |
| Tests audited | **73** files — all **KEEP** / parser **REVIEW** only; **0** deleted |
| Manual review backlog | Older PA intermediates, `layer2_qqq_v2_relaxed/` — see **`repo_cleanup_summary.md` §8** |

## F. Explicit non-runs

- **Layer 1**, **Layer 2**, **mini-WFO**, **full WFO**, **live/paper**

## G. Risks / caveats

- Legacy YAML **`layer2_qqq_v1.yaml`** / **`layer2_sweep_qqq_v1.yaml`** / **`layer2_qqq_2020_20260430_v2_relaxed.yaml`** remain; **candidate_root paths in comments are gone** — use post-hardening configs + roots (**CONFIG_INDEX.md** §F).
- Historical markdown (e.g. **`recovery_status_before.md`**) may still mention removed paths; top banner added where touched.

## H. Recommended next step

**Global Layer 1 / global Layer 2 design** (windows, symbol set, which post-hardening baselines anchor “global”) — **not** PA B/C v4 tuning, **not** mini-WFO execution until that design lands.
