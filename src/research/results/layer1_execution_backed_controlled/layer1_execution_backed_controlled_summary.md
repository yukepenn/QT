# Layer1 execution-backed controlled — summary (minimal proof complete)

**Result root:** `src/research/results/layer1_execution_backed_controlled/`  
**Active candidates:** `src/strategies/testing_parameters_results/l1_execution_backed_controlled/`

## What shipped in this line of work

1. **Sweep checkpointing** — **`sweep_results_partial.csv`**, **`sweep_progress.json`**, CLI **`--checkpoint-every`**, **`--resume`**, per-combo timing columns; atomic writes; partial removed on successful completion (`src/backtest/sweep.py`).
2. **Balanced minimal grids** — **16 + 16 + 8** combos in **`src/strategies/testing_parameters/*_minimal_proof.yaml`** (no research **`--max-combos`**).
3. **Curated minimal runs** — QQQ **2023-01-01..2024-12-31** under **`runs/*_2023_2024_minimal_proof/`** with **`sweep_results.csv`**, meta, progress, summary.
4. **Promotion** — **`--include-run-name-contains minimal_proof`**, gate **`L1_EXECUTION_BACKED_MINIMAL_PROOF`**, candidate IDs **`*_L1M_*`** (`src/research/run_layer1_execution_backed_controlled.py`).
5. **Fast path** — design only: **`fast_path_numba_readiness.*`** (no Numba code).

## Decision

**`RUN_CONTROLLED_LAYER2_ON_MINIMAL_CANDIDATES`** — see **`layer1_execution_backed_controlled_decision.md`**.

## Review bundle

**`CHATGPT_REVIEW_BUNDLE.md`**, **`SOURCE_MAP.csv`**, **`chatgpt_key_tables.csv`**.
