# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Latest commit | **`Test(execution): expand accounting boundary matrix`** — verify SHA with `git log -1 --oneline` after pull/push |
| Remote | `git ls-remote origin refs/heads/main` must match local `HEAD` after push |
| Working tree | Stage curated paths only — **never** `git add .` |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | Pass (run locally before push) |
| `python -m pytest -q` | **68 passed** (active `tests/`; `tests/Archive` excluded) |
| `python -m src.strategies.loader --list` | Run before handoff |
| Import smoke (`src.execution`, `src.backtest.engine`, `src.backtest.metrics`, combiner, router, portfolio) | `imports_ok` |
| `python scripts/canonical_execution_smoke.py` | Synthetic OHLC smoke |
| Tracked-heavy check | No forbidden paths in `git ls-files` |

## C. Accounting boundary resolution

- **`src/execution/materialize.py`:** canonical entry fill, initial risk, target (`fixed_r` / `fixed_price` / `none`), targetless exit-path guard (EOD sentinel `eod_exit_minute >= 500` disables EOD for validation only; scale-out without trailing rejected).
- **`src/backtest/engine.py`:** raw `sig_*` → `TradeIntent` only; no adapter-side fill/risk/target math; `run_backtest` remains legacy Numba entry.
- **`src/backtest/metrics.py`:** aggregates `r_multiple` / `net_pnl` / optional `gross_r_multiple`; does not recompute trade R from OHLC.

## D. Execution semantics updates

- Documented exit order matches `src/execution/path.py` (stop/target → prior trailing → scale-out → NFT → max-hold → EOD → end data → trail ratchet).
- **`scale_fill_policy`:** `close` vs `trigger_price` for scale-out raw fill.
- Gross vs net R on `TradeResult`; `r_multiple` aliases net R.

## E. Backtest adapter changes

- `signals_to_trade_intents` — no `entry_price` / precomputed risk / `tgt_px` parameters; passes `target_mode`, `target_r`, optional `target_price`, optional `risk_per_share`.
- MVP unchanged: first valid signal per session → one `simulate_trade_path` call.

## F. Metrics / R multiple changes

- `summarize_trades`: `total_r` = sum of `r_multiple` (net); `total_net_pnl` = sum of `net_pnl`; `total_gross_r` when `gross_r_multiple` column exists.

## G. Legacy sweep status

- **`src/backtest/sweep.py`** module docstring: **legacy Numba fast**, not canonical execution.
- Canonical sweep on reference engine: **deferred**.

## H. Test matrix coverage

- Materialization, targetless (trailing, EOD path, scale+trail, rejections), exit-priority same-bar cases, scale fill policies, commission gross vs net, metrics aggregation, legacy boundary / import hygiene.

## I. Explicit non-runs

No WFO, mini-WFO, live/paper, SPY, broad Layer2, Champion migration, historical sweeps, new strategies, short/scalp research, selected-candidate YAML edits, raw artifacts.

## J. Risks / caveats

- Targetless validation uses an **EOD minute sentinel** (`>= 500`); consider a dedicated policy flag later.
- Combiner simulator remains legacy Numba.
- No canonical sweep / Numba parity harness yet.

## K. Files changed (high level)

`src/execution/*` (incl. `materialize.py`, `__init__.py` exports), `src/backtest/engine.py`, `src/backtest/metrics.py`, `src/backtest/sweep.py`, `tests/test_execution_*.py`, `tests/test_backtest_*`, `tests/test_legacy_boundary.py`, `docs/EXECUTION_SEMANTICS.md`, `docs/ACCOUNTING_BOUNDARY_REVIEW.*`, `docs/EXECUTION_TEST_MATRIX_SUMMARY.md`, `docs/ACCOUNTING_OWNERSHIP_AUDIT.md`, `CHANGES.md`, `PROGRESS.md`, `NEXT_HANDOFF.md`.

## L. Recommended next step (exactly one)

**`HOLD_AND_REVIEW`**
