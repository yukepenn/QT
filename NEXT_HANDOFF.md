# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Tip | After push: `git log -1 --oneline` matches `git ls-remote origin refs/heads/main`. |
| Working tree | Curated `git add` only — **never** `git add .` |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **165** passed |
| `python -m src.strategies.loader --list` | OK |
| `python -m src.backtest.sweep --help` | OK (incl. **`--checkpoint-every`**, **`--resume`**) |
| `python -m src.backtest.sweep --smoke` | OK |
| `python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend --symbol QQQ --start 2024-01-02 --end 2024-01-05 --data-root data/raw/ibkr` | OK |
| `python -m src.research.run_layer1_execution_backed_controlled --help` | OK (**`--include-run-name-contains`**) |
| `python -m src.research.run_layer1_execution_backed_controlled validate-candidates --candidate-root src/strategies/testing_parameters_results/l1_execution_backed_controlled` | OK |
| `python -m src.combiner.run --help` / `combiner.sweep --help` | OK |
| `validate_research_artifacts` on `layer1_execution_backed_controlled` | **29** curated paths OK → **`layer1_execution_backed_controlled_artifact_validation.csv`** |

## C. Task scope

**Completed:** **`RUN_MINIMAL_LAYER1_EXECUTION_BACKED_PROOF_AND_PREP_FASTPATH`** — minimal balanced **16 / 16 / 8** combo YAMLs; **`sweep.py`** incremental **`sweep_results_partial.csv`** + **`sweep_progress.json`**, **`--resume`**, per-combo timing columns; **40** real QQQ 2023–2024 minimal sweeps; promotion filtered by **`minimal_proof`** folder names; **`*_L1M_*`** minimal-proof candidate YAMLs; **Numba fast-path design doc only** (no Numba code).

## D. Interrupted full run status

Prior **`*_full_focused`** run outputs (complete but large) were **removed locally** for this task so git carries only **`minimal_proof`** runs. See **`interrupted_run_inventory.*`**.

## E. Checkpoint / resume

Atomic temp→replace for partial CSV and progress JSON; **`--resume`** skips `combo_id` already in partial; partial deleted on full success. See **`checkpoint_resume_design.*`**.

## F. Minimal balanced grids

`pa_buy_sell_close_trend_minimal_proof.yaml` (**16**), `gap_acceptance_failure_minimal_proof.yaml` (**16**), `cci_extreme_snapback_minimal_proof.yaml` (**8**). No **`--max-combos`** on research runs.

## G. Minimal sweeps

`runs/*_minimal_proof/`: `sweep_results.csv` + meta + progress **completed**; wall clock ~**1121 s** for all three; **`data_source`** = `ibkr_parquet:data/raw/ibkr`.

## H. Promotion / candidate root

Gate **`L1_EXECUTION_BACKED_MINIMAL_PROOF`**; **`--include-run-name-contains minimal_proof`**; **4** YAMLs (`GAP`×2, `CCI`×2); PA excluded under PF **1.02** on minimal slice (max PF ~**1.014**).

## I. Fast-path readiness

See **`fast_path_numba_readiness.*`** — parity-first scope, no Numba implementation in this task.

## J. Decision

**`RUN_CONTROLLED_LAYER2_ON_MINIMAL_CANDIDATES`**

## K. Explicit non-runs / risks

No full focused Layer1, no broad Layer1, Layer3, WFO, live/paper, SPY research, router, Numba PnL engine, new strategy families, raw trade commits.

## L. Files changed (high level)

`src/backtest/sweep.py`, `src/research/run_layer1_execution_backed_controlled.py`, `tests/test_sweep_checkpoint.py`, `src/strategies/testing_parameters/*_minimal_proof.yaml`, `src/research/results/layer1_execution_backed_controlled/**`, `src/strategies/testing_parameters_results/l1_execution_backed_controlled/**`, `NEXT_HANDOFF.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `RESULTS_INDEX.md`, `docs/LAYER_FLOW.md`, `run_commands.*` under the result root.

## M. Local-only artifacts

Heavy non-minimal sweep folders removed locally; re-runnable if needed.

## N. Recommended next step (exactly one)

**`RUN_CONTROLLED_LAYER2_ON_MINIMAL_CANDIDATES`**
