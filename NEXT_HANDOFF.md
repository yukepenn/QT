# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Latest commit | Architecture reset: **`Feat(architecture): introduce canonical execution engine`** — verify SHA with `git log -1 --oneline` on `main` |
| Remote | After push: `git ls-remote origin refs/heads/main` must match local `HEAD` |
| Working tree | Stage only curated paths — **never** `git add .` |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | Run before handoff |
| `python -m pytest -q` | **26 passed** (active `tests/`; `tests/Archive` excluded via `pytest.ini`) |
| `python -m src.strategies.loader --list` | **35** strategies |
| Import smoke (`src.execution`, `management`, `backtest.engine`, `combiner.simulator`, `router`, `portfolio`) | **`imports_ok`** |
| Tracked-heavy check | `git ls-files \| Select-String -Pattern "top_runs\|trades.csv\|..."` → **no matches** |

## C. Architecture reset (this cycle)

| Topic | Status |
|--------|--------|
| Canonical **`src/execution/`** | **Present** — fill, exits, pnl, validators, reference `simulate_trade_path`; `fast_path` placeholder |
| **`src/management/`** | Exit-plan templates from `ManagementMode` → `ExitPlan` (generic; not wired to router) |
| **`src/backtest/`** | **`run_strategy_backtest`** MVP (first valid signal / session, `sig_*` columns) uses execution; **`run_backtest`** → **`legacy/engine_legacy`** |
| **`src/combiner/`** | **`simulator.py`** re-exports **`legacy/simulator_legacy`** (Numba accounting still in legacy); **`selection.py` / `state.py`** minimal scaffolds |
| **`src/router/`**, **`src/portfolio/`** | Scaffolds only (disabled-by-default / generic helpers) |
| **`src/walkforward/legacy/`** | Package placeholder; main walkforward code not bulk-moved |
| Docs | `docs/ARCHITECTURE.md`, `MODULE_OWNERSHIP.md`, `EXECUTION_SEMANTICS.md`, `SIGNAL_CONTRACT.md`, `FEATURES_CONTRACT.md`, `STRATEGIES_CONTRACT.md`, reset plan/inventory/moves/summary, audit CSVs |

## D. Files moved to legacy

| Old (conceptual) | New |
|------------------|-----|
| `src/backtest/engine.py` | `src/backtest/legacy/engine_legacy.py` |
| `src/backtest/fast.py` | `src/backtest/legacy/fast_legacy.py` |
| `src/backtest/execution.py` | `src/backtest/legacy/execution_legacy.py` |
| `src/combiner/simulator.py` | `src/combiner/legacy/simulator_legacy.py` |

Shims: `src/backtest/execution.py`, `src/backtest/fast.py`, `src/combiner/simulator.py` (re-exports).

## E. Explicit non-runs

- No WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global Layer1 grids.
- No new trading strategies; no scalp / short research runs; no selected-candidate YAML edits.
- No commits of raw trades, parquet, `local_rows`, `top_runs`, sweep folders, caches, logs, npy/npz/memmap.

## F. Risks / caveats

- **Legacy Numba** backtest/combiner paths still contain **duplicate accounting**; they are isolated under `legacy/` but remain the default for existing sweeps until migration.
- **`run_strategy_backtest`** is **intentionally minimal** (not full sweep parity).
- **Numba `fast_path`** is a placeholder; parity tests target the reference engine only.
- Prior research metrics (overlay alignment, Layer3, etc.) are **historical priors** vs new execution semantics.

## G. Recommended next step (exactly one)

**`RUN_CANONICAL_EXECUTION_SMOKE`**
