# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Tip | After push, verify `git log -1 --oneline` matches `origin/main`. |
| Working tree | Stage curated paths only — **never** `git add .` |

## B. Structure consolidation

- Folded **`sweep_types`**, **`sweep_grid`**, **`sweep_io`**, **`sweep_results`**, **`config`**, **`backtest_config`** into **`src/backtest/sweep.py`** and **`strategy_runner.py`** / **`engine.py`** as needed.
- **`TM_*`** live in **`src/execution/types.py`**; strategies import from there.
- Removed **`src/backtest/fast.py`**, **`execution.py`**, **`constants.py`** from active tree.
- **`prepare_backtest_arrays`** inlined into **`src/combiner/precompute.py`**; deleted **`src/combiner/bar_arrays.py`**.
- **`src/combiner/reference_simulator.py`** → **`archive/legacy_combiner/reference_simulator.py`**.
- **`src/combiner/simulator.py`** is a **stub** (`NotImplementedError` for Numba entry points).

## C. Active `src/backtest` files

`__init__.py`, `engine.py`, `sweep.py`, `signal_adapter.py`, `strategy_runner.py`, `metrics.py` only.

## D. Archived files

- **`archive/legacy_combiner/reference_simulator.py`** — historical Numba Layer 2 simulator.

## E. Backtest / sweep

- CLI: `--help` (via no-args), `--smoke`, `--pipeline-help`, `--validate-pipeline`, `--strategy`, `--symbol`, `--asset`, `--start`, `--end`, `--data-root`, `--config`, `--grid`, `--output-root`, `--max-combos`, `--no-save`, `--dry-run`.
- Artifacts: **`sweep_results.csv`**, **`sweep_summary.md`**, **`sweep_smoke.csv`**, **`sweep_meta.json`** (real runs: manifest merged into **`sweep_meta.json`**; no separate **`run_manifest.json`**).
- Schema: **`result_lineage=mainline`**, **`engine=reference`**, **`execution_semantics_version`**, metrics columns per **`tests/test_sweep_result_schema.py`**.

## F. Strategy runner

- **`FeatureFrameCache`**, grid/YAML merge helpers, **`validate_pipeline`** (alias **`validate_canonical_pipeline`** kept for compatibility); pipeline report key **`pipeline_signal_ready`** (replaces **`canonical_signal_ready`** in new output).

## G. Combiner

- **`simulate_combiner_numba`** / **`simulate_combiner_legacy_logs`** raise **`NotImplementedError`** until Layer 2 is rebuilt on **`execution.path`**.
- **`run.py`**, **`sweep.py`**, **`postprocess.py`** still import simulator symbols; runtime combiner runs will fail until adapter work lands.

## H. Docs renamed / added

- Added **`docs/STRUCTURE_CONSOLIDATION_PLAN.md`**, **`docs/STRUCTURE_CONSOLIDATION_INVENTORY.csv`**.
- Updated **`docs/PROJECT_STRUCTURE.md`**, **`docs/FILE_OWNERSHIP.md`**, **`docs/MAINLINE_STRUCTURE_SUMMARY.md`**, **`docs/LAYER_FLOW.md`**.

## I. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **116 passed** |
| `python -m src.strategies.loader --list` | **35** strategies (unchanged contract) |
| `python -m src.backtest.sweep --smoke` | OK |
| `python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend` | exit 0 |
| `tests/test_backtest_package_layout.py` | backtest dir allowlist |
| `tests/test_mainline_no_legacy_imports.py` | skips `src/**/Archive/**` |

## J. Explicit non-runs

No WFO, mini-WFO, live/paper, SPY research, broad Layer 2/3, Champion migration, broad historical sweeps, new strategies, short/scalp research, performance claims, trade-level artifact commits.

## K. Risks / caveats

- **`src/combiner/`** still contains **`postprocess.py`**, **`behavior.py`**, **`diagnostics.py`** beyond the long-term ten-file target; trimming is a follow-up.
- Walkforward / combiner **`run`** paths are blocked until simulator is reimplemented.
- Real-symbol sweep optional smoke against local QQQ parquet was **not** run in CI.

## L. Recommended next step (exactly one)

**`COMPLETE_COMBINER_ADAPTER`**
