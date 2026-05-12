# Code readability check (canonical execution smoke)

## Reformatted / hardened (normal Python layout)

- `src/execution/types.py`, `policy.py`, `fill.py`, `exits.py`, `pnl.py`, `path.py`, `validators.py`
- `src/execution/fast_path.py` (docstring only; still delegates)
- `src/management/*.py` (module docstrings + scalp `max_hold_bars_cap`)
- `src/backtest/engine.py` (adapter docstring + `trade_results_to_frame`)
- `src/combiner/selection.py`, `state.py`, `simulator.py` (docstrings / helpers)
- `src/router/*.py`, `src/portfolio/*.py` (already small modules)
- Active `tests/test_*.py` at repo `tests/` root touched in this pass

## Intentionally legacy / shims (not canonical layout)

- `src/backtest/legacy/*`, `src/combiner/legacy/*` — duplicate accounting allowed until migration.
- `src/backtest/engine.py` → `run_backtest` delegates to `engine_legacy`.

## Known style debt

- Legacy engines remain large; do not reformat wholesale in a smoke pass.
- `scripts/canonical_execution_smoke.py` prepends `sys.path` so it runs standalone on Windows without `PYTHONPATH`.
