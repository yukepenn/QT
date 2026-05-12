# Module ownership (architecture reset)

This document defines **what each top-level package may do** and what is **forbidden**. The goal is a single canonical execution layer (`src/execution/`) used by backtest, combiner, and future paper/live adapters.

## 1. `data/`

**Owns:** load, normalize, sort, dedupe, validate bars.  
**Must not:** strategy logic, feature math, execution, PnL, candidate selection.

## 2. `features/`

**Owns:** no-lookahead column computation, stable `feature_key` / config contracts.  
**Must not:** trade simulation, fills, PnL, combiner selection.

## 3. `strategies/`

**Owns:** raw candidate signal generation; standardized signal contract (via metadata + adapters).  
**Must not:** PnL, portfolio sizing, router wiring (router consumes outputs later).

## 4. `execution/` (canonical)

**Owns:** entry and exit fill math, **materialization** of entry price, initial risk, and targets (`materialize.py`), exit ordering, ambiguity policy, gross and net PnL/R (commission as one charge per trade), `scale_fill_policy`, MFE/MAE path accounting.  
**Must not:** strategy discovery, combiner priority rules, walk-forward folds.

All backtest/combiner/research replay code that needs fills must call into `execution/`.

## 5. `management/`

**Owns:** exit-plan construction (targets, scale-out, trailing, no-followthrough, mode templates).  
**Must not:** decide *whether* a trade is allowed (router), or *which* candidate wins (combiner).

## 6. `backtest/`

**Owns:** single-strategy adapter: validate signal columns, map rows to **raw** `TradeIntent` → `execution.path.simulate_trade_path`; `metrics.py` aggregates canonical trade columns only. **Placeholder** Layer 1 sweep CLI (`sweep.py`): canonical sweep not implemented; `--legacy` delegates to `legacy/sweep_legacy.py`. **`fast.py`** exposes only legacy `TM_*` signal-array codes — not `prepare_backtest_arrays` / `run_fast_backtest_from_arrays` (those live in `legacy.fast_legacy`).  
**Must not:** compute entry fill, execution risk, or fixed-R targets in the adapter; must not imply Numba sweep is canonical (use docs + CLI messaging).

## 7. `combiner/`

**Owns:** candidate arbitration, risk knobs (max trades, cooldown, daily loss), building `TradeIntent`, calling `execution`.  
**Must not:** implement fill/exit/PnL accounting in new mainline code; the legacy Numba `simulator` path is compatibility-only until migrated.

## 8. `router/` (scaffold)

**Owns:** context labels, permission decisions, quality scores (offline-friendly).  
**Must not:** execute trades or mutate execution policy unless explicitly passed through adapters later.

## 9. `walkforward/`

**Owns:** folds, fixed-profile harnesses, reporting orchestration.  
**Must not:** bar-level fill rules or strategy signal semantics.

## 10. `portfolio/` (scaffold)

**Owns:** sizing, equity curve helpers, daily loss guards (generic math).  
**Must not:** intraday stop/target intrabar logic.

## 11. `research/`

**Owns:** thin experiment runners, artifact writers.  
**Must not:** canonical accounting (delegate to `execution/` when trades are simulated).

## 12. `utils/`

**Owns:** config validation, IO helpers, cross-cutting pure utilities.
