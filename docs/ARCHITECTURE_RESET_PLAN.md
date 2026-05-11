# Architecture reset plan (QT)

## Motivation

Legacy `backtest` and `combiner` each implemented fill / exit / PnL accounting, which caused alignment drift versus later overlay replay. The reset establishes **one canonical execution accounting layer** under `src/execution/`.

## Principles

- Old curated research artifacts remain **historical priors**, not canonical truth for accounting semantics.
- No `*_v2.py` filenames: new mainline uses normal names (`engine.py`, `simulator.py`, …).
- Legacy code lives under `**/legacy/` with `_legacy` suffix where moved wholesale.
- Do not commit raw trades, parquet, caches, sweep trees, `top_runs/`, or `local_rows/`.

## Phased rollout

| Phase | Deliverable |
|-------|-------------|
| 0 | Git baseline, inventories (`ARCHITECTURE_RESET_INVENTORY.*`) |
| 1 | `MODULE_OWNERSHIP.md` |
| 2 | `EXECUTION_SEMANTICS.md` |
| 3 | `SIGNAL_CONTRACT.md`, strategy metadata extensions |
| 4 | Legacy moves + `ARCHITECTURE_RESET_MOVES.*` |
| 5 | `src/execution/` canonical package |
| 6 | `src/management/` exit-plan builders |
| 7–8 | Thin `backtest/` and `combiner/` adapters calling `execution` |
| 9–10 | `router/`, `portfolio/` scaffolds |
| 11 | Feature/strategy contract audits (CSVs) |
| 12 | New tests under `tests/test_*` |
| 13–15 | Docs refresh, validation, explicit `git add` paths, single commit |

## Non-goals (this reset)

- No WFO / mini-WFO / live / paper / SPY / broad Layer2 runs.
- No new trading strategies or scalp/short research.
- No edits to selected-candidate YAMLs.
- No Numba fast-path parity until reference engine is stable (`fast_path.py` placeholder).

## Recommended next step after merge

See `NEXT_HANDOFF.md` — default: **`RUN_CANONICAL_EXECUTION_SMOKE`**.
