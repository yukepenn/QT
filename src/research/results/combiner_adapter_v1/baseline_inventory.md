# Combiner adapter v1 — baseline inventory

## Git tip (before adapter work)

`4da3ed1` — Architecture: consolidate mainline structure

## NEXT_HANDOFF recommended step (pre-change)

`COMPLETE_COMBINER_ADAPTER`

## Actual code state (verified)

| Component | State |
|-------------|--------|
| `src/combiner/simulator.py` | **Mixed**: lazy-load legacy Numba from `archive/legacy_combiner/reference_simulator.py`; exposes `simulate_combiner_canonical` (delegates to `adapter.py`); `simulate_combiner_numba` is legacy alias. |
| `src/combiner/run.py` | Imports simulator; **can import**; runtime previously failed when stub raised `NotImplementedError` — **restored** with legacy delegate. |
| `src/combiner/sweep.py` | **Can import**; `--engine canonical` supported. |
| Layer3 `walkforward/runner.py` | Imports `run_combiner_fixed_config`; **OK** with default `engine="legacy"`. |
| Legacy simulator location | `archive/legacy_combiner/reference_simulator.py` |
| Canonical execution | `src/execution/path.py` + `TradeIntent` in `src/execution/types.py` |

## Doc vs code contradictions (resolved)

- Docs said simulator was **stub-only** (`NotImplementedError`): **was true** after consolidation commit; **fixed** by restoring lazy legacy + adding canonical adapter.
- `docs/LAYER_FLOW.md` implied Layer2 still “legacy accounting only”: **updated** to describe dual paths (`--engine legacy|canonical`).

## Blocked entrypoints (pre-fix)

- `simulate_combiner_numba()` / full combiner run without legacy file: would fail.
- Canonical path: **did not exist** before this task.

## Tests before change

116 `pytest` (per prior handoff).
