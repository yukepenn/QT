# Batch 1 cost fragility — diagnostics v1

- **runs_root:** `D:\OneDrive - Washington University in St. Louis\QT\src\combiner\results\layer2_qqq_v2_batch1_2023_2024_diagnostics_local`
- **trades merged:** 4161
- **total R (all legs):** 216.1540
- **approx mean round-trip cost / R** (2×0.01 slip / risk_per_share): 0.0787
- **Bollinger squeeze ΣR:** 204.4514
- **RSI ΣR:** 4.9664

## Interpretation

1. **Trade count vs fragility:** squeeze systems run **hundreds** of trades; fixed per-share costs compound → small edge at 0.01 often flattens by 0.02.
2. **Risk per share:** many entries sit on **tight structural stops** → high `approx_round_trip_cost_r` tails.
3. **Candidate dominance:** top squeeze IDs capture most ΣR; RSI is secondary once combined.
4. **Near-duplicate YAMLs:** overlap matrix shows **same-bar collisions** across `_001…_005` grids.

See sibling CSV/MD files for bucketed views.
