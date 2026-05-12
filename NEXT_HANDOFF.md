# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Tip | After push, verify `git log -1 --oneline` matches `origin/main`. |
| Working tree | Stage curated paths only — **never** `git add .` |

## B. Mainline cleanup (this session)

- **`src/backtest/legacy/*`** moved to **`archive/legacy_backtest/`** (historical Numba sweep / `run_backtest`); see `archive/legacy_backtest/README.md`.
- **`src/combiner/legacy/simulator_legacy.py`** → **`src/combiner/reference_simulator.py`**; `combiner/simulator.py` re-exports unchanged API.
- **`prepare_backtest_arrays`** → **`src/combiner/bar_arrays.py`**; **`TM_*`** → **`src/backtest/constants.py`**; **`fast.py`** TM shim only.
- **`BacktestConfig` / `_bt_cfg_from_dict`** → **`src/backtest/backtest_config.py`**; grid/YAML helpers → **`src/backtest/config.py`**.
- **`sweep.py`** split: `sweep_types.py`, `sweep_grid.py`, `sweep_io.py`, `sweep_results.py`; CLI **`--legacy` removed**; **`--canonical-help`** → **`--pipeline-help`**.
- Result fields: **`result_lineage=mainline`**, **`engine=reference`**; artifacts **`sweep_results.csv`**, **`sweep_summary.md`**, **`sweep_smoke.csv`**, **`sweep_meta.json`**.
- Renamed docs: `BACKTEST_SWEEP_DESIGN.md`, `SWEEP_RESULT_SCHEMA.md`, `SWEEP_SMOKE_SUMMARY.md`, `REAL_SWEEP_*`, `STRATEGY_INTEGRATION_PLAN.md`, `STRATEGY_INTEGRATION_STATUS.csv`.

## C. Strategy runner / feature cache

- **`FeatureFrameCache`** in `strategy_runner.py` (hits/misses/signal_count/combo_count); real-symbol sweep uses it by default.

## D. Engine

- **`run_backtest`** removed from public `backtest` package.
- **`run_strategy_backtest`**: optional **`max_trades_per_session`**, **`cooldown_bars`** on `BacktestConfig` (defaults preserve prior single-trade-per-session behavior).

## E. Execution / fast path

- **`validate_trade_setup`** (+ helpers) consolidated into **`src/execution/validators.py`**; **`backtest/execution.py`** re-exports for compatibility.
- Numba acceleration remains **planned** under `src/execution/fast_path.py` with parity vs `path.py` (not implemented here).

## F. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **114 passed** |
| `python -m src.strategies.loader --list` | **35** strategies |
| `python -m src.backtest.sweep --smoke` | OK |
| `python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend` | exit 0 |
| Mainline import audit | `tests/test_mainline_no_legacy_imports.py` |

## G. Explicit non-runs

No WFO, mini-WFO, live/paper, SPY research, broad Layer2/Layer3, Champion migration, historical broad sweeps, new strategies, short/scalp research, performance claims.

## H. Risks / caveats

- Layer 2 combiner still uses **Numba reference** simulator (not `execution.path` loop).
- Docs outside the renamed set may still mention old filenames; update opportunistically.

## I. Recommended next step (exactly one)

**`COMPLETE_BACKTEST_SWEEP_HARDENING`**
