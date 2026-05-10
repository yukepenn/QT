# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Latest commit before work | `3f88882` — Feat(research): PA Batch B/C diversity v3 |
| New commit hash | `pending-before-commit` (replace after push if mirroring from GitHub) |
| Commit message | `Repair PA Batch B/C candidate diversity` |
| Push status | Run `git push` after commit; confirm on remote `main` |
| Working tree status | Curated PA B/C repair + Layer 2 repaired v3 summaries staged; heavy sweep dirs (`sweep_*`, `top_runs/`, raw `candidate_precompute_profile.csv`, `feature_store_stats.json` under repaired root) remain **local / untracked** |
| Known untracked local-only artifacts | `src/strategies/testing_parameters_results/**`; various `**/cost_stress/candidate_precompute_profile.csv`, `**/feature_store_stats.json`; `pa_gate_rows.jsonl`; other Layer 2 precompute dumps from prior runs |

## B. Task Scope

| | |
|--|--|
| Requested task | PA Batch B/C **climax-focused** diversity repair: raw sweep audit → repaired candidate root → optional Layer 2 repaired v3; docs + tests; **no** mini/full WFO, **no** new strategies |
| What was actually completed | `sweep_result_signal_diversity.py`, `export_diverse_candidates_from_results.py`, `candidate_signal_diversity.py` refactor; tests; `pa_batch_bc_climax_diversity_repair_plan.md`, raw audit `pa_batch_bc_raw_signal_diversity_v3/`, `selected_candidates_repaired/` (6 YAMLs), `pa_batch_bc_candidate_signal_diversity_repaired_v3/`, `repaired_candidate_decision.md` (**RUN_LAYER2_REPAIRED_V3**), `pa_batch_bc_diversity_repair_summary.md`; Layer 2 configs + curated results `layer2_qqq_pa_batch_bc_repaired_v3_2023_2024/`; indexes + `README` / `PROJECT_STATUS` / `PROGRESS` / `CHANGES` / `.gitignore` |
| What was intentionally not done | **mini-WFO**, **full WFO**, **live/paper**; PA Batch A tuning; new Brooks primitives; committing `sweep_20260510_220219/` or `top_runs/`; Phase 7 default-preserving climax **code** param (not needed — H1 selector) |

## C. Files Changed

| Category | Paths (high level) |
|----------|---------------------|
| Source / code | `src/research/sweep_result_signal_diversity.py`, `src/research/export_diverse_candidates_from_results.py`, `src/research/candidate_signal_diversity.py` |
| Tests | `tests/test_sweep_result_signal_diversity.py`, `tests/test_export_diverse_candidates_from_results.py` |
| Config / YAML | `src/combiner/configs/layer2_qqq_pa_batch_bc_repaired_v3_2023_2024.yaml`, `src/combiner/configs/layer2_sweep_qqq_pa_batch_bc_repaired_v3_2023_2024.yaml` |
| Research results / docs | `src/research/results/pa_batch_bc_climax_diversity_repair_plan.md`, `pa_batch_bc_raw_signal_diversity_v3/*`, `pa_batch_bc_diversity_repair_summary.md`, `pa_batch_bc_candidate_signal_diversity_repaired_v3/*`, `layer1_pa_batch_bc_tuned_qqq_2023_2024_v3/selected_candidates_repaired/**`, `repaired_candidate_decision.md`, `RESULTS_INDEX.md` |
| Combiner results (curated) | `src/combiner/results/layer2_qqq_pa_batch_bc_repaired_v3_2023_2024/` — summary, `top_unique_*`, `cost_stress/cost_stress_{results.csv,summary.md}`, `cost_robust_systems.*`, `diagnostics/*` **summary tables only** (see `.gitignore` force-include list) |
| Repo docs | `README.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `tests/README.md`, `src/combiner/configs/CONFIG_INDEX.md`, `src/combiner/results/RESULTS_INDEX.md`, `.gitignore`, `NEXT_HANDOFF.md` |
| Intentionally left untracked | `sweep_20260510_220219/` under repaired Layer 2; `feature_store_stats.json`; raw `candidate_precompute_profile.csv` under `cost_stress/` / `diagnostics/` |

## D. Validation

| Check | Result |
|--------|--------|
| `python -m pytest -q` | **363 passed** |
| `python -m compileall -q src` | **OK** |
| `python src/strategies/loader.py --list` | **35** strategies listed |
| Parity (`failed_orb`, `pa_buy_sell_close_trend` tuned v3, `pa_climax_reversal` tuned v3, Jan 2025 window, `--max-combos 2`) | **OK** (`TOTAL_MISMATCH_FIELDS approx=0`) |
| Boundary | `LOOKAHEAD` only in documented full-session columns + strategy guard; **`_feat_key`** / **`DfSignalStrategy`**: **no matches in `src/**/*.py`** |
| No `*.py` under `src/*/results` | **None found** |
| `git ls-files` heavy pattern (`top_runs`, `trades.csv`, `.parquet`, etc.) | **No tracked matches** |

## E. Research / Experiment Results

| Item | Detail |
|------|--------|
| Window | QQQ **2023-01-01 → 2024-12-31** |
| Raw strict pool (filters in `raw_signal_diversity_summary.md`) | **Climax:** 1152 sweep rows → **176** strict eligible; unique `pure_signal_hash` in top **20 / 50 / 100** score pool: **2 / 2 / 5**. **Close-trend:** **895** strict; **8 / 13 / 26** |
| Hypothesis | **H1 (selector)** supported — multiple climax masks exist **below** score-top-five; not H2-only |
| Repaired Layer 1 | **6** YAMLs (`3+3`); `pa_batch_bc_candidate_signal_diversity_repaired_v3`: **3 / 3** unique pure hashes per strategy |
| Layer 2 repaired v3 | **96** combos; sweep dir **`sweep_20260510_220219/`** (local); postprocess **behavior_unique skipped** (`--detail-top 0`); decision **`PROCEED_TO_PA_BATCH_BC_MINI_WFO_DESIGN`** (design-only next) |
| Cost stress highlight | Leading **0.02** row on cost slice ≈ **`pa_climax`** / `PA_CLIMAX_REVERSAL_DIVERSE_001` — see `cost_stress/cost_stress_summary.md` |
| Decision reached | Layer 2 summary: **`PROCEED_TO_PA_BATCH_BC_MINI_WFO_DESIGN`** — **do not run mini-WFO** until explicit design phase |

## F. Explicit Non-Runs

- **mini-WFO**, **full WFO**, **live/paper**
- **Layer 2 on original strict v3 root** (still superseded by repair narrative)
- **Broad v4 climax YAML / strategy param expansion** (Phase 7 code change not applied)

## G. Risks / Caveats

- **Behavior-unique** gate not evaluated on this Layer 2 run; re-sweep locally with detail depth + postprocess if that gate blocks freeze.
- Economics on **`pa_batch_bc_core`** at **0.02** need explicit CSV review if cost slice is climax-heavy only.

## H. Recommended Next Step

**Design-only: PA Batch B/C mini-WFO** — draft harness + train/test split config from **`PROCEED_TO_PA_BATCH_BC_MINI_WFO_DESIGN`**; **no** execution until a dedicated phase.
