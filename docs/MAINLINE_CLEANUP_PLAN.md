# Mainline cleanup plan

Goal: Layer 1 uses `read_bars` → features → strategies → `signal_adapter` → `engine.run_strategy_backtest` → `execution.path` → `metrics` only. Historical Numba sweep/backtest lives under `archive/legacy_backtest/` and is not imported by `src/`. Layer 2 Numba reference remains in `src/combiner/reference_simulator.py` until an execution-backed combiner loop exists. Next: sweep UX, grid tooling, optional `execution/fast_path.py` with parity tests.
