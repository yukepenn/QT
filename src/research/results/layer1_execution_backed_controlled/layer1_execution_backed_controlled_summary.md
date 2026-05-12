# Layer1 execution-backed controlled — design summary

**Result root:** `src/research/results/layer1_execution_backed_controlled/`  
**Task type:** DESIGN ONLY — no broad Layer1 execution in this commit.

## Contents

| Doc | Purpose |
|-----|---------|
| `baseline_inventory.*` | Git tip, counts, non-goals |
| `baseline_validation.*` | compileall / pytest / CLI checks |
| `layer1_pipeline_state.*` | File roles + accounting ownership |
| `data_design.*` | Repo-local QQQ windows |
| `strategy_selection_design.*` | PA, GAP, CCI only |
| `grid_design.*` | Caps + gates |
| `candidate_artifact_schema.*` | Future YAML + indices |
| `execution_policy_design.*` | Policy fields + known min_risk threading gap |
| `run_commands.*` | Preflight + sweep commands (real runs commented in scripts) |
| `cli_capability_check.*` | Answers: dry-run, data-root, single strategy |
| `runner_gap_analysis.md` | No `--engine`; selection not in sweep |
| `validation_gates.*` | Pre/run/post checklist |
| `layer1_execution_backed_controlled_decision.md` | **`RUN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`** |
| `CHATGPT_REVIEW_BUNDLE.md` | Review narrative |
| `SOURCE_MAP.csv` / `chatgpt_key_tables.csv` | Navigation |

## Decision

**`RUN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`** — execute capped sweeps under `runs/` then add selection + YAML stamping in a follow-up commit series.
