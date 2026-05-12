# Mainline legacy surgery plan (2026-05-11)

## Goals

1. Top-level module names (`engine.py`, `sweep.py`, `fast.py`, `simulator.py`, `runner.py`) must not **silently** expose legacy Numba accounting as if it were canonical.
2. Legacy implementations stay importable under `**/legacy/**` for Layer1/Layer2 reference workflows until parity-backed replacements exist.
3. Canonical accounting remains solely in `src/execution/`; backtest `run_strategy_backtest` and future combiner loops delegate there.

## Completed in this pass

| Item | Action |
|------|--------|
| `src/backtest/sweep.py` | Replaced with placeholder CLI + `--legacy` delegate to `legacy/sweep_legacy.py`. |
| `src/backtest/legacy/sweep_legacy.py` | Full former sweep implementation; imports `legacy.fast_legacy` only. |
| `src/backtest/fast.py` | **Constants only** (`TM_*`); `__getattr__` rejects `prepare_backtest_arrays` / `run_fast_backtest_from_arrays`. |
| `src/combiner/precompute.py` | Imports `prepare_backtest_arrays` from `legacy.fast_legacy`. |
| `src/combiner/simulator.py` | Explicit named re-exports only; docstring states legacy-only. |

## Follow-up (not this task)

- Canonical sweep implementation (`run_strategy_backtest` grid) per `docs/CANONICAL_SWEEP_DESIGN.md`.
- Combiner adapter calling `simulate_trade_path` per `docs/CANONICAL_COMBINER_DESIGN.md`.
- `src.execution.fast_path` Numba port with parity tests vs `path.py`.

## Inventory

See `docs/MAINLINE_LEGACY_SURGERY_INVENTORY.csv`.
