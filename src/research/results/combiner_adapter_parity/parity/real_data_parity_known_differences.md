# Real-data parity — known / acceptable differences

- **Fill path semantics**: ``execution_backed`` uses ``TradeIntent -> simulate_trade_path``; ``legacy_reference`` uses archived Numba matrix scheduling. Same signals can yield different intra-session trade counts or R when ordering differs.
- **Slippage / touch ordering**: YAML slippage is applied on both paths but intrabar touch resolution can diverge slightly, producing small ``total_r`` drift at identical trade counts.
- **Rejections**: Legacy exposes richer ``rejection_counts`` in metrics; execution-backed may report fewer structured rejections while still producing coherent trades.
- Exact legacy PnL match is **not** required for research adoption if drift is stable and classified.

See ``real_data_parity_drift_classification.csv`` for this run's tags.
