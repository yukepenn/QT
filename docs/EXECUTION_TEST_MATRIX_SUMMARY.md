# Execution test matrix summary

**Date:** 2026-05-11

## Decisions

| Topic | Decision |
|-------|-----------|
| Accounting boundary | `src/execution` is the only canonical source for entry fill, initial risk, target materialization, exit priority, partial legs, gross/net PnL and R. Adapters pass raw `TradeIntent`. |
| Backtest adapter | `signals_to_trade_intents` does not take precomputed entry, risk, or target; `run_strategy_backtest` only slices bars and calls `simulate_trade_path`. |
| Gross vs net R | `TradeResult.gross_r_multiple` = weighted leg R before commission; `net_r_multiple` = net PnL/share ÷ initial risk; `r_multiple` aliases `net_r_multiple`. |
| Exit priority (per bar) | (1) Stop/target with `same_bar_policy` (2) Prior-bar trailing stop (3) Scale-out (4) No-followthrough (5) Max-hold (6) EOD (7) End data; then ratchet trailing for next bar. |
| Scale fill policy | `ExecutionPolicy.scale_fill_policy`: `close` (default) vs `trigger_price` (limit-like touch fill); stop/target still precede scale on the same bar. |
| Targetless (`target_mode=none`) | Materialization requires a non–END_DATA-only exit path: trailing, max-hold (intent or cap), NFT pair, or EOD regarded as active when `eod_exit_minute < 500`. Scale-out without trailing is rejected. Tests use `eod_exit_minute=999` to mean “EOD not counted for targetless validation.” |

## Tests added / expanded (pytest)

- `tests/test_execution_materialize.py` — entry/risk/target materialization; targetless paths.
- `tests/test_execution_targetless_runner.py` — trailing runner; fixed_r validation; EOD-only targetless path.
- `tests/test_execution_path.py` — stop vs scale; trailing vs scale; target vs max-hold; max-hold vs EOD; commission gross vs net R.
- `tests/test_execution_partial.py` — `scale_fill_policy` close vs `trigger_price`; stop-first with trigger policy.
- `tests/test_backtest_metrics.py` — `summarize_trades` uses `r_multiple` and optional `total_gross_r`.
- `tests/test_legacy_boundary.py` — sweep docstring; execution path does not import legacy fast.

**Count:** 68 passed (active `tests/` per `pytest.ini`).

## Still legacy / deferred

- `src/backtest/sweep.py` + Numba `legacy.fast_legacy` — not canonical; canonical sweep on reference engine is future work.
- Combiner `simulator.py` — legacy Numba compatibility surface.
- Optional: explicit `ExecutionPolicy` flag instead of `eod_exit_minute >= 500` sentinel for targetless validation.

## Recommended next step

`HOLD_AND_REVIEW` — confirm the EOD sentinel convention and any research consumers of `target_mode=none` before Champion migration.
