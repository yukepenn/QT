# Fast-path / Numba acceleration plan (no implementation in this task)

1. **`simulate_trade_path`** in `src/execution/path.py` remains the **reference** semantics implementation.
2. **`src/execution/fast_path.py`** should become a **parity-tested** accelerator (today it only delegates to the reference).
3. Any future Numba (or other) fast path must pass a growing suite mirroring: entry fill, stop/target ordering and same-bar ambiguity, max-hold, EOD, **`min_risk_per_share`**, scale-out on **remaining** qty, trailing, no-followthrough when used.
4. Archived legacy Numba combiner code is **compatibility / benchmark only** — not a second accounting truth.
5. Broad Layer1/2 sweeps may introduce `execution_mode=fast` **only after** explicit parity gates; until then use reference `simulate_trade_path` only.
