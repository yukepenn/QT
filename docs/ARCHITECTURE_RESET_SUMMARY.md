# Architecture reset summary (2026-05-11)

## What shipped

- **Canonical `src/execution/`** package: types, policy, fill, exits, pnl, reference `path.simulate_trade_path`, validators, `fast_path` placeholder.
- **`src/management/`** exit-plan scaffolding (`ManagementMode`, default `ExitPlan` templates).
- **`src/router/`** and **`src/portfolio/`** scaffolds (disabled-by-default / generic helpers).
- **Legacy isolation**: moved `engine`, `fast`, `execution`, `simulator` into `legacy/` with **import shims** to avoid breaking strategies/combiner imports.
- **New backtest adapter API**: `run_strategy_backtest` (execution-backed) + `run_backtest` delegates to legacy for sweep parity.
- **Combiner `simulator.py`**: re-exports legacy Numba implementation pending execution-backed combiner loop.
- **Tests**: new execution + adapter smoke tests; `pytest.ini` skips `tests/Archive` collection.
- **Docs**: architecture, semantics, signal contract, ownership, inventories, moves log.

## Explicit non-runs

- No WFO / mini-WFO / live / paper / SPY / broad Layer2 / new strategies / scalp-short research.

## Recommended next step

**`EXPAND_EXECUTION_TEST_MATRIX`** — add more same-bar grids, commission splits,
and combiner→execution integration once Champion mapping is specified.

## 2026-05-11 — Canonical execution smoke

- Reformatted / documented `src/execution/**`, management, adapters, selection/state.
- **Trailing** default is conservative (no same-bar ratchet trigger).
- **Scale-out** triggers on intrabar touch; fills at **close** for that leg.
- **Tests:** expanded active suite (`pytest` at repo root).
- **Script:** `scripts/canonical_execution_smoke.py` (synthetic OHLC only).
