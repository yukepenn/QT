# Decision — Layer1 execution-backed controlled (design package)

## Label (exactly one)

**`RUN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`**

## Rationale (3–6 bullets)

- **Design package complete:** pipeline map, data window, three-strategy scope, grids with caps, artifact schema, execution policy alignment, runbooks, validation gates, CLI capability documented.
- **Current `backtest.sweep` can execute** real-symbol capped sweeps with **`--data-root data/raw/ibkr`**, per-strategy **`--grid`**, and **`--output-root`**; **`--dry-run`** verified.
- **Accounting path is correct:** **`simulate_trade_path`** is the sole simulator for Layer1 backtests; no second engine required for the run.
- **`sweep.py` CLI entry fixed:** **`python -m src.backtest.sweep`** now invokes **`main()`**, matching README/tests.
- **Minor gaps are non-blocking:** sweep omits `--engine` flag and uses `engine=reference` label; candidate stamping and optional **`min_risk_per_share`** policy threading are small follow-ups inside the **run** task, not reasons to block the first sweep.
- **No new broad runner required** for first pass; optional thin `run_layer1_execution_backed_controlled.py` only if shell orchestration becomes painful.

## Recommended next step (exactly one)

**`RUN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`**

## Explicit non-runs (this design task)

No real Layer1 sweeps, no broad Layer2/Layer3, no WFO, no live/paper, no SPY sweeps, no router, no new strategy families, no signal semantic edits, no champion YAML edits, no legacy delete/archive, no Numba fast path implementation, no raw trade / heavy artifact commits.
