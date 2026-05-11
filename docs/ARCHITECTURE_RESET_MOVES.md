# Architecture reset — file moves log

| old_path | new_path | reason |
|----------|----------|--------|
| `src/backtest/engine.py` | `src/backtest/legacy/engine_legacy.py` | Legacy single-strategy accounting loop |
| `src/backtest/fast.py` | `src/backtest/legacy/fast_legacy.py` | Legacy Numba sweep kernels |
| `src/backtest/execution.py` | `src/backtest/legacy/execution_legacy.py` | Legacy validation helpers (shim re-exported) |
| `src/combiner/simulator.py` | `src/combiner/legacy/simulator_legacy.py` | Legacy combiner fill/exit/R loop |

Compatibility shims remain at original import paths:

- `src/backtest/execution.py` → re-exports `execution_legacy`
- `src/backtest/fast.py` → re-exports `fast_legacy`
- `src/combiner/simulator.py` → re-exports legacy simulator API

CSV mirror: `ARCHITECTURE_RESET_MOVES.csv`.
