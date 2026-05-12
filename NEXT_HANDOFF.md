# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Latest commit | **`Test(execution): harden canonical execution smoke`** — verify SHA with `git log -1 --oneline` after pull |
| Remote | `git ls-remote origin refs/heads/main` must match local `HEAD` after push |
| Working tree | Stage curated paths only — **never** `git add .` |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | Run before handoff |
| `python -m pytest -q` | **49 passed** (active `tests/`; `tests/Archive` excluded) |
| `python -m src.strategies.loader --list` | **35** strategies |
| `python scripts/canonical_execution_smoke.py` | Synthetic OHLC smoke (adds repo root to `sys.path`) |
| Tracked-heavy check | No forbidden paths in `git ls-files` |

## C. Canonical execution smoke

- Reference engine **`simulate_trade_path`** refactored for readability + documented exit order.
- **Conservative trailing:** trail **checked** using prior bar’s ratcheted level; **updated** after other same-bar decisions.
- **Scale-out:** touch-based **trigger**; **close** used as raw exit price for the scale-out leg (documented).
- **`TradeResult`:** `REJECTED` reason; `is_win`, `total_qty_frac`, `has_partial` properties.
- **`ExitPlan.max_hold_bars_cap`** interacts with `TradeIntent.max_hold_bars` via `min`.

## D. Execution semantics covered

See `docs/EXECUTION_SEMANTICS.md` and `docs/CANONICAL_EXECUTION_SMOKE_SUMMARY.md` — includes: stop/target (+ ambiguity), trailing, scale-out, NFT, max-hold (+ cap), EOD, end-data, MFE/MAE, short gate, commission single charge per trade.

## E. Management support

- Modes still generic; **scalp** adds `max_hold_bars_cap=12` + NFT defaults.
- Runner / reversal / swing / fixed_r plans unchanged structurally; tests assert valid `ExitPlan` objects.

## F. Backtest adapter status

- `run_strategy_backtest` remains **minimal** (first signal / session MVP).
- Added **`trade_results_to_frame`** for `TradeResult` inspection.
- Canonical **`sig_*`** column expectations documented in module docstring.

## G. Combiner status

- **`simulator.py`**: still **legacy Numba** re-export — **do not extend** for new accounting.
- **`selection.py` / `state.py`**: deterministic priority + day/cooldown/daily-loss helpers with tests.

## H. Contract audit

- `docs/FEATURES_AUDIT.csv`, `docs/STRATEGIES_AUDIT.csv` regenerated (lightweight rows).
- `docs/SIGNAL_CONTRACT.md` — still authoritative for column naming; adapters may map legacy names.

## I. Explicit non-runs

No WFO, mini-WFO, live/paper, SPY, broad Layer2, Champion migration, historical sweeps, new strategies, short/scalp research, selected-candidate YAML edits, raw artifacts.

## J. Risks / caveats

- Legacy combiner/backtest still hold duplicate accounting.
- Numba `fast_path` remains a delegating placeholder.
- Scale-out fill-at-close is conservative; revisit if research needs touch fills.

## K. Files changed (high level)

`src/execution/*`, `src/management/modes.py`, `src/backtest/engine.py`, `src/combiner/selection.py`, `src/combiner/state.py`, `src/combiner/simulator.py` (docstring), `scripts/canonical_execution_smoke.py`, `docs/*` (smoke + semantics + audits), `tests/test_*`.

## L. Recommended next step (exactly one)

**`EXPAND_EXECUTION_TEST_MATRIX`**
