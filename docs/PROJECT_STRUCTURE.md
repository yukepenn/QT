# Target project structure (summary)

- **data** — load and validate bars only.
- **features** — no-lookahead feature columns; optional FeatureStore reuse.
- **strategies** — raw candidate signal generation only.
- **execution** — fill, exit, PnL accounting; reference `path.py`; `types.py` holds `TM_*` signal-array labels; future `fast_path.py` after parity.
- **management** — exit plans and trade-management modes.
- **backtest** — exactly six Python modules: `__init__.py`, `engine.py`, `sweep.py`, `strategy_runner.py`, `signal_adapter.py`, `metrics.py`.
- **combiner** — candidate competition; **legacy_reference** engine = lazy-loaded archived Numba; **execution_backed** engine = `adapter.simulate_combiner_canonical` → `execution.path` (`canonical` remains a CLI alias). Adapter enforces same-`session_date` next-bar entry, passes `min_risk_per_share` via `ExecutionPolicy`, and relies on `state.reset_day` to clear loss cooldown across sessions. Reference: `archive/legacy_combiner/`.
- **router / walkforward / portfolio / research / utils** — unchanged intent from architecture docs.
- **archive** — historical code and deprecated sweep/combiner paths.

## Policy: `src/backtest`

Only the six files above. Anything else must merge into one of them, move to `execution/` or `utils/`, or live under `archive/`.

## Policy: `src/combiner` (active mainline)

Target set: `__init__.py`, `candidate.py`, `precompute.py`, `signal_cache.py`, `selection.py`, `state.py`, `simulator.py`, `run.py`, `sweep.py`, `metrics.py`, plus **`adapter.py`** and **`trade_intent_adapter.py`** for the execution-backed Layer 2 path. Extra modules (for example `postprocess.py`, `behavior.py`, `diagnostics.py`) remain until a follow-up migration; active `src/` must not `import archive` as a package root pattern.
