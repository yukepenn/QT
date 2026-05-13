# Fast-path Numba readiness (design only)

**No Numba in this task.** `src/execution/path.py` remains accounting truth. Next engineering work:

1. Instrumented per-combo timings (`combo_elapsed_sec`) show reference path cost; extrapolated 656-combo full focused ≈ many hours.
2. Phase-1 fast path scope: long-only, fixed-R, `min_risk_per_share`, next-bar entry, max-hold, EOD; defer scale-out/trailing until parity matrix exists.
3. Proposed API: `simulate_trade_path_fast(...)` in `src/execution/fast_path.py` delegating only after golden tests vs `simulate_trade_path`.
4. Gate: broad Layer1 / balanced64 may adopt fast path **only** after parity suite passes.

See **`fast_path_numba_readiness.csv`**.
