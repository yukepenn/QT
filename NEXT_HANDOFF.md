# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Latest commit before this work | `4e25f4a` — `Docs(handoff): stable cleanup tip pointer` |
| New commit | **Design global Layer 1 and Layer 2** — use `git log -1 --oneline` for SHA |
| Push status | **Pushed** to `origin/main` *(if push fails, retry from network)* |
| Working tree | Expected clean post-commit; **`src/strategies/testing_parameters_results/**`** remains local-only (sweeps for this Layer 1 run) — **do not** `git add` it |
| Known untracked local-only | `repo_cleanup_inventory.csv` regeneration; any sweep folders under `testing_parameters_results/` |

## B. Task scope

| | |
|--|--|
| Requested | Global research pipeline: strategy audit, Global Layer 1 QQQ 2023–2024, diversity + fast-context, summaries / leaderboard, Global Layer 2 **design**, conditional Layer 2 only if gates pass |
| Completed | `global_strategy_audit.py` + `global_strategy_audit_v1/`; `run_global_layer1.py` (manifest, skip list, selection, post-analysis); full **30** runnable sweeps → **`layer1_global_qqq_2023_2024_v1/`**; **81** strict YAMLs; `global_candidate_signal_diversity_qqq_2023_2024_v1/`; `global_branch_leaderboard_v1.*`; `global_layer1_qqq_2023_2024_design.md`; `global_layer2_qqq_2023_2024_design.md`; `RESULTS_INDEX`, `README`, `PROJECT_STATUS`, `PROGRESS`, `CHANGES`, this file |
| Intentionally not done | **Global Layer 2 execution** (configs under `src/combiner/configs/layer2_qqq_global_*` and combiner results root **not** created); **mini-WFO**, **full WFO**, **live/paper**; **SPY**; no new strategies or feature primitives |

## C. Files changed

| Area | Paths |
|------|--------|
| Source | `src/research/global_strategy_audit.py`, `src/research/run_global_layer1.py` |
| Tests | **None** |
| Configs / combiner | **None** (Layer 2 not run) |
| Research results / docs | `src/research/results/global_strategy_audit_v1/**`, `global_layer1_qqq_2023_2024_design.md`, `global_layer2_qqq_2023_2024_design.md`, `layer1_global_qqq_2023_2024_v1/**`, `global_candidate_signal_diversity_qqq_2023_2024_v1/**`, `global_branch_leaderboard_v1.{csv,md}`, `RESULTS_INDEX.md` |
| Root docs | `README.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `NEXT_HANDOFF.md` |
| Intentionally untracked | `src/strategies/testing_parameters_results/**` (sweep outputs tagged `layer1_global_qqq_2023_2024_v1`) |

## D. Validation

| Check | Result |
|--------|--------|
| `pytest -q` | **363 passed** |
| `python -m compileall -q src` | **OK** |
| `loader.py --list` | **35** strategies |
| Parity (failed_orb, PA tuned v3 ×2) | **OK** (`TOTAL_MISMATCH_FIELDS approx=0`) |
| Boundary `git grep` | **OK** — `LOOKAHEAD` in documented feature names; `_feat_key` / `DfSignalStrategy` hits only in **markdown** under `src/research/results` (not in `*.py`) |
| Heavy `git ls-files` pattern | **No hits** |
| No `*.py` under `src/*/results` | **OK** (PowerShell glob returned empty) |

## E. Research results

| Metric | Value |
|--------|--------|
| Strategies in audit CSV | **35** |
| Runnable READY + grid ≤1500 | **30** sweeps executed |
| Skipped (grid >1500 or non-READY in audit) | **5** (see `skipped_strategies.*`) |
| Long / short / both | See `strategy_side_support_matrix.*`; short only where YAML/metadata exposes axes (**no** forced short) |
| Layer 1 run | **Complete** — `sweep_manifest.csv` |
| Strict `selected_candidates` YAML count | **81** |
| Distinct `strategy_family` in strict CSV | **15** |
| Diversity | `candidate_signal_diversity.csv`, `duplicate_signal_groups.csv`, `strategy_diversity_summary.*`, `family_candidate_summary.*` |
| Fast-context | All **`ok`** (`fast_context_check.*`) |
| Layer 2 | **Design only** — gate **NO** (`81` > `80` cap per `global_layer2_gate_decision.md`) |
| Decision | **`TUNE_GLOBAL_LAYER1_OR_BUCKETS`** — e.g. `--top-per-strategy 4` or slightly stricter filter, then re-check gate before any Layer 2 run |

## F. Explicit non-runs

- **mini-WFO**
- **full WFO**
- **live / paper**
- **Global Layer 2 combiner** (gate failed)

## G. Risks / caveats

- **Prerun gate** failed by **one** YAML over the documented **80** cap; families/diversity/fast-context otherwise pass.
- **13** strategies produced **no** strict candidate (filters or sweep shape); see `no_candidate_strategies.txt` and leaderboard zeros.
- **`pa_generic_breakout_pullback`**, **`pa_broad_channel_zone`**: manifest shows **0** `result_rows` / zero-trade style outcomes — treat as fragile for global promotion until repaired in a later phase.
- **In-sample only** (2023–2024 QQQ); no OOS claims.

## H. Recommended next step

**Exactly one:** **tune global Layer 1 / buckets** — reduce `--top-per-strategy` or tighten one strict axis, re-run `run_global_layer1.py`, and re-evaluate `global_layer2_gate_decision.md` before authoring executable Layer 2 YAMLs.
