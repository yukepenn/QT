# CLI wiring

## `src.combiner.run`

- `--engine legacy` (default): `simulate_combiner_numba` or `simulate_combiner_legacy_logs` when `--detailed`.
- `--engine canonical`: `simulate_combiner_canonical` (detailed flag ignored for engine choice; logs empty).
- `--dry-run`: no `run_*` directory writes; still runs precompute/simulation in memory.

## `src.combiner.sweep`

- `--engine legacy|canonical` passed through per combo (canonical uses `simulate_combiner_canonical`).

## `run_combiner_fixed_config`

- New keyword `engine: str = "legacy"` for programmatic calls (walkforward unchanged).
