# local_trade_context_replay_summary

## What was done

- Regenerated local-only detailed `trades.csv` for Champion v0 profiles × windows.
- Built a local-only row-level trade-context panel joined to **decision-time** context (`signal_ts_utc`) using backward `merge_asof`.
- Emitted commit-safe **aggregates** for context coverage, regime/context buckets, market context, attribution, freshness, offline router diagnostics, and trade-quality v2 diagnostics.

## Local-only artifacts (not committed)

- `local_rows/trade_context_panel.csv`
- `local_rows/trades/**/trades_enriched_local.csv`
- `local_runs/**/trades.csv`

## Key coverage

- local panel rows: **10,628**
- decision context join (regime window 20): **10,628 / 10,628**

## Key pointers

- Aggregates: `aggregates/`
- Router diagnostics: `router_diagnostics_v1/`
- Quality score v2: `quality_score_v2/`
- Attribution: `attribution_v1/`
- Freshness: `freshness_v1/`
- Exit overlay readiness: `exit_overlay_readiness_v1/`
- Roadmap update: `roadmap_update_v1/`
- Decision: `local_trade_context_replay_decision.md`

