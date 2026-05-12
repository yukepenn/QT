# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Latest commit | **`Architecture: clarify canonical layer connectivity`** — verify SHA with `git log -1 --oneline` after pull/push |
| Remote | `git ls-remote origin refs/heads/main` must match local `HEAD` after push |
| Working tree | Stage curated paths only — **never** `git add .` |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | Run before handoff |
| `python -m pytest -q` | **85 passed** |
| `python -m src.strategies.loader --list` | **35** strategies |
| Import smoke (execution, management, backtest engine/metrics, combiner selection/state, router, portfolio) | `imports_ok` |
| `import src.backtest.legacy.fast_legacy` | `legacy_fast_import_ok` |
| `python -m src.backtest.sweep --help` | Placeholder CLI + `--legacy` documented |
| `python scripts/canonical_execution_smoke.py` | Synthetic OHLC |
| Tracked-heavy check | Clean |

## C. Legacy surface cleanup

- **`src/backtest/sweep.py`:** canonical **placeholder** CLI; default exit ≠ 0 with guidance; **`--legacy`** delegates to **`src/backtest/legacy/sweep_legacy.py`** (prints `engine=legacy_numba_fast`).
- **`src/backtest/fast.py`:** **only** `TM_*` constants; `__getattr__` rejects `prepare_backtest_arrays` / `run_fast_backtest_from_arrays` (use **`legacy.fast_legacy`** explicitly).
- **`src/combiner/precompute.py`:** imports **`legacy.fast_legacy`** for `prepare_backtest_arrays`.
- **`src/combiner/simulator.py`:** explicit named re-exports from **`legacy.simulator_legacy`**; docstring states legacy-only (no `import *`).

## D. Layer 1 / 2 / 3 connectivity

- **Layer 1:** Documented in **`docs/LAYER_FLOW.md`** / **`docs/LAYER_FLOW.csv`**; canonical path = signals → adapter → execution; grid sweep = future + **`docs/CANONICAL_SWEEP_DESIGN.md`**.
- **Layer 2:** **`docs/CANONICAL_COMBINER_DESIGN.md`** — selection/state → `TradeIntent` → execution (target); today’s Numba sim is legacy.
- **Layer 3:** **`docs/LAYER3_VALIDATION_DESIGN.md`**, **`docs/WALKFORWARD_STATUS.md`** — harnesses depend on legacy combiner until adapter lands.

## E. Canonical sweep status

- **Not implemented** on reference engine; placeholder + **`run_canonical_sweep_placeholder`** raises `NotImplementedError`.

## F. Canonical combiner status

- **Legacy** Numba re-export only; do not extend with new accounting.

## G. Walkforward status

- **`docs/WALKFORWARD_STATUS.csv`**: runner / mini_wfo depend on legacy combiner; safe to keep; migrate when execution-backed combiner exists.

## H. Feature / strategy connectivity

- **`docs/FEATURE_STRATEGY_CONNECTIVITY.md`** + CSV; loader **35** strategies; Champion-related IDs load (`pa_buy_sell_close_trend`, `gap_acceptance_failure`, `cci_extreme_snapback`).

## I. Explicit non-runs

No WFO, mini-WFO, live/paper, SPY, broad Layer2, Champion migration, historical sweeps, new strategies, short/scalp research, selected YAML edits, performance claims.

## J. Risks / caveats

- Archive scripts under `src/research/results/Archive/` may still `import src.backtest.fast` for prepare/run — update to **`legacy.fast_legacy`** when touched.
- `python -m src.backtest.sweep` requires **`--legacy` first** for Numba grid (not discoverable from old habits alone — docs mitigate).

## K. Recommended next step (exactly one)

**`COMPLETE_CANONICAL_BACKTEST_SWEEP`**
