# baseline_inventory — local_detailed_trade_context_replay_v1

- **git_tip_at_start**: `92ba1fab0002929a9e6805ba896ef7c1a79a6567` (Playbook Router Research Cycle v1 complete)
- **formal_decision_from_NEXT_HANDOFF**: `RUN_LOCAL_DETAILED_TRADE_CONTEXT_REPLAY`

## Champion v0 profiles (frozen; do not modify)

| profile_id | role | candidates |
|------------|------|------------|
| `pa_only_mtp1_meta` | CLEAN_BASELINE | `PA_BUY_SELL_CLOSE_TREND_003` |
| `pa_gap_mtp2_meta` | DEFAULT_COMBINED | `PA_BUY_SELL_CLOSE_TREND_003` + `GAP_ACCEPTANCE_FAILURE_001` |
| `primary_mtp2_meta` | BREADTH_REFERENCE_ONLY | PA + GAP + `CCI_EXTREME_SNAPBACK_003` |

## Source roots inspected / reused

- `src/research/results/playbook_router_research_cycle_v1/` (schema + router/quality designs)
- `src/research/results/layer3_fixed_profile_smoke_complete_v1/` (curated aggregates)
- `src/research/results/layer3_expanded_stability_v1/` (weak periods + market context labels)
- `src/research/fixed_profile_oow.py` and `src/research/enrich_combiner_trades.py` (enrichment patterns; backward `merge_asof`)

## Row-level fields currently missing from curated summaries

See `playbook_router_research_cycle_v1/trade_context_panel_v1/trade_context_missing_inputs.csv`:

- trade identifiers, timestamps, bars held, prior-trade linkage
- decision-time PA regime / VWAP / ORB / level proximity / gap context
- per-trade market context label and derived context buckets

## Local-only output locations (NOT COMMITTED)

- `src/research/results/local_detailed_trade_context_replay_v1/local_rows/**`
  - detailed `trades.csv` per profile/window
  - row-level `trade_context_panel.csv`
  - optional cached features

## Committed aggregate output locations

- `src/research/results/local_detailed_trade_context_replay_v1/aggregates/**`
- `src/research/results/local_detailed_trade_context_replay_v1/router_diagnostics_v1/**`
- `src/research/results/local_detailed_trade_context_replay_v1/quality_score_v2/**`
- `src/research/results/local_detailed_trade_context_replay_v1/**.md` / `SOURCE_MAP.csv` / `CHATGPT_REVIEW_BUNDLE.md`

