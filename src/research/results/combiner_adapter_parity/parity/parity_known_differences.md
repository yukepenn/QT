# Known differences (synthetic slice)

1. **Session loop**: ``execution_backed`` uses the sequential adapter in ``adapter.py`` (cursor jumps to post-exit bar). ``legacy_reference`` uses archived Numba matrix semantics that may schedule additional entries differently across the same bar series.
2. **Target materialization**: Execution-backed path materializes fixed-R targets through ``simulate_trade_path``; legacy may differ slightly on slippage / touch ordering even at zero slippage when matrix preview vs entry-time materialization diverges.
3. **Rejection taxonomy**: Legacy fills ``rejection_counts``; execution-backed adapter currently returns zeroed rejection arrays (documented simplification).
4. **Toy matrix observation**: On the built-in synthetic slice used by ``run_combiner_adapter_parity``, **legacy_reference** may emit **zero** completed trades while **execution_backed** emits **one** (see ``parity_summary.csv``). Treat as a parity signal, not a silent pass.

These are expected until a full parity harness aligns bar cursor, signal→entry gating, and rejection mapping.
