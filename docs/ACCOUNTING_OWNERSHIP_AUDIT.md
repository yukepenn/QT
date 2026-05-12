# Accounting ownership audit

## Method

Ripgrep over `src/**/*.py` for symbols associated with trade accounting
(`r_multiple`, `slippage`, `entry_price`, `exit_price`, `stop_price`,
`target_price`, `max_hold`, `commission`), then classify hits.

## Summary

| Classification | Meaning |
|----------------|---------|
| `canonical_execution` | `src/execution/**` |
| `legacy_duplicate` | `src/**/legacy/**` (expected duplicate) |
| `adapter_metrics` | Backtest/combiner adapters summarizing `TradeResult` or legacy outputs |
| `research_other` | Research / diagnostics (not canonical) |
| `tests_docs` | Tests and documentation |

## Finding

Mainline **non-legacy** Python should **not** implement a second intrabar fill
loop for production paths. **`run_strategy_backtest`** now delegates fill /
risk / target / PnL to **`simulate_trade_path`** only; top-level **`sweep.py`**
is a placeholder unless ``--legacy`` (see **`legacy/sweep_legacy.py`**).
**`fast.py`** exposes only ``TM_*`` constants; Numba kernels stay in
**`legacy.fast_legacy`**. Remaining duplicate accounting risk is
**`src/backtest/legacy`**, **`src/combiner/legacy`**, and explicit combiner
simulator re-exports until migrated.

See `docs/ACCOUNTING_OWNERSHIP_AUDIT.csv` for sample rows. See also
`docs/ACCOUNTING_BOUNDARY_REVIEW.md` and `docs/EXECUTION_TEST_MATRIX_SUMMARY.md`.
