# Target project structure (summary)

- **data** — load and validate bars only.
- **features** — no-lookahead feature columns; optional FeatureStore reuse.
- **strategies** — raw candidate signal generation only.
- **execution** — fill, exit, PnL accounting; reference `path.py`; future `fast_path.py` after parity.
- **management** — exit plans and trade-management modes.
- **backtest** — single-strategy adapter and Layer 1 sweep (`engine`, `sweep`, `strategy_runner`, `metrics`).
- **combiner** — candidate competition; `reference_simulator` Numba until execution-backed loop.
- **router / walkforward / portfolio / research / utils** — unchanged intent from architecture docs.
- **archive** — historical code and deprecated sweep/combiner paths.
