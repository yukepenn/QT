# Target project structure (summary)

- **data** — load and validate bars only.
- **features** — no-lookahead feature columns; optional FeatureStore reuse.
- **strategies** — raw candidate signal generation only.
- **execution** — fill, exit, PnL accounting; reference `path.py`; `types.py` holds `TM_*` signal-array labels; future `fast_path.py` after parity.
- **management** — exit plans and trade-management modes.
- **backtest** — exactly six Python modules: `__init__.py`, `engine.py`, `sweep.py`, `strategy_runner.py`, `signal_adapter.py`, `metrics.py`.
- **combiner** — candidate competition; mainline Layer 2 simulator pending (`simulator.py` stub); archived Numba reference under `archive/legacy_combiner/`.
- **router / walkforward / portfolio / research / utils** — unchanged intent from architecture docs.
- **archive** — historical code and deprecated sweep/combiner paths.

## Policy: `src/backtest`

Only the six files above. Anything else must merge into one of them, move to `execution/` or `utils/`, or live under `archive/`.

## Policy: `src/combiner` (active mainline)

Target set: `__init__.py`, `candidate.py`, `precompute.py`, `signal_cache.py`, `selection.py`, `state.py`, `simulator.py`, `run.py`, `sweep.py`, `metrics.py`. Extra modules (for example `postprocess.py`, `behavior.py`, `diagnostics.py`) remain until a follow-up migration; they must not import `archive/` or legacy packages.
