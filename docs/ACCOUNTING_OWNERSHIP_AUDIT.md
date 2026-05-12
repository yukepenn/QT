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
loop for production paths. Remaining risk is **`src/backtest/legacy`** and
**`src/combiner/legacy`** until migrated.

See `docs/ACCOUNTING_OWNERSHIP_AUDIT.csv` for sample rows.
