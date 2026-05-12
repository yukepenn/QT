# Archived Numba backtest / sweep (historical reference)

This folder holds the former `src/backtest/legacy/*` modules (Numba grid sweep,
`run_backtest` loop, shared validators copy). **Mainline code must not import
from here.** Run manually only if you extend `PYTHONPATH` to this directory
for local experiments; intra-folder imports use sibling modules (e.g.
`sweep_legacy.py` imports `fast_legacy`).
