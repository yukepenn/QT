# Structure consolidation plan

## Goal

Contract `src/backtest` to six Python modules (`__init__.py` plus five mainline files), fold sweep helpers into `sweep.py`, relocate shared types (`TM_*` → `execution/types.py`), archive the Layer 2 Numba reference simulator, and keep CI green (`compileall`, `pytest`, sweep smoke / validate-pipeline).

## Done (2026-05-11)

- Merged former `sweep_types`, `sweep_grid`, `sweep_io`, `sweep_results`, `config`, `backtest_config` into `sweep.py` / `strategy_runner.py` / `engine.py` as appropriate.
- Removed `src/backtest/fast.py`, `execution.py`, `constants.py`, and combiner `bar_arrays.py` from the active tree.
- Archived `src/combiner/reference_simulator.py` → `archive/legacy_combiner/reference_simulator.py`; `combiner/simulator.py` is a constants + `NotImplementedError` stub until Layer 2 is rebuilt on `execution.path`.

## Inventory

See `docs/STRUCTURE_CONSOLIDATION_INVENTORY.csv` for path-level mapping.

## Non-goals (this pass)

- No WFO, live/paper, broad historical sweeps, or Champion migration.
- No new strategy logic or feature math.
