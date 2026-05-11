# trade_context_panel_schema

Row-level panel is **not** committed; see `trade_context_panel_schema.csv` for column contract.

## Principles
- All feature joins at **entry** use **backward** `merge_asof` (no lookahead).
- Champion v0 remains **long-only** in this cycle.
