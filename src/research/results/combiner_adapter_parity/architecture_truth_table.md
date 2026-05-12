# Architecture truth table — combiner_adapter_parity

Machine-readable rows: `architecture_truth_table.csv`.

## Principles

- **Single accounting authority for mainline:** `src.execution.path.simulate_trade_path` once a `TradeIntent` is built.
- **Layer 2 selection/state:** arbitration and session guards only — no independent intrabar fill math.
- **legacy_reference:** archived Numba in `archive/legacy_combiner/reference_simulator.py` remains for compatibility and parity baselines until drift is fully catalogued.

## Notes

- `simulator.py` must never silently route `execution_backed` to Numba; engine choice is explicit in `run.py` / `sweep.py` via `normalize_combiner_engine_label`.
- Layer 3 `runner.py` still calls `run_combiner_fixed_config` with default `engine="legacy"` until parity and ops review justify `execution_backed`.
