# playbook_router_cycle_v1_decision

## Decision: `RUN_LOCAL_DETAILED_TRADE_CONTEXT_REPLAY`

### Rationale
- Champion v0 is **frozen** and documented; strategic shift is to **context/router/quality** — not more strategies.
- Trade-context **schema** and **offline router / quality / exit / roadmaps** are specified for the next cycle.
- **Row-level** columns (regime at entry, true `market_context_label` per trade, `prior_trade_r`, bars_held) are **not** present in committed `complete_*` CSVs.
- Aggregated diagnostics answer **window-level** PA vs PA+GAP vs primary questions only.
- Next increment to reduce unknowns is a **local-only** trade tape + backward-asof feature join (not committed).

### Recommended next step
- Run **local-only** Layer3 Champion v0 replay enrichment (existing tooling: `fixed_profile_oow` / trade enrich patterns) to materialize a **row-level** trade-context panel on disk, then re-run offline router scoring.

### Explicit non-runs
- No WFO / live / SPY / broad L2 / combiner router wiring / new strategies / YAML edits / short implementation.
