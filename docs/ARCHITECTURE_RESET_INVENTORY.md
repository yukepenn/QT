# Architecture reset — file inventory

Machine-readable inventory: `ARCHITECTURE_RESET_INVENTORY.csv` (generated from `src/**/*.py`).

High-level themes:

- **Canonical execution** lives in `src/execution/` (new).
- **Legacy duplicate accounting** for backtest/combiner Numba paths lives under `src/backtest/legacy/` and `src/combiner/legacy/`.
- **Research scripts** referenced by archived tests live under `src/research/results/Archive/` (not part of new mainline).

See `ARCHITECTURE_RESET_PLAN.md` and `ARCHITECTURE_RESET_SUMMARY.md`.
