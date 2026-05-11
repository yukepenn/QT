# baseline_inventory — router_quality_refinement_v2

## Git tip before this work

- **`d81a1791bcf7d254b4754988816ea8969dce4c2c`** — `Research(router): run local trade context replay`

## Formal decision (pre-work NEXT_HANDOFF)

- **`REFINE_ROUTER_QUALITY_SCORE`** (superseded by this cycle’s new decision in `router_quality_refinement_v2_decision.md` after diagnostics).

## Champion v0 profiles (frozen)

| profile_id | role |
|------------|------|
| `pa_only_mtp1_meta` | CLEAN_BASELINE (PA only) |
| `pa_gap_mtp2_meta` | DEFAULT_COMBINED (PA + GAP) |
| `primary_mtp2_meta` | BREADTH_REFERENCE_ONLY (PA + GAP + CCI) |

## Local row-level dependency

- **Panel path (local-only):** `src/research/results/local_detailed_trade_context_replay_v1/local_rows/trade_context_panel.csv`
- **Status:** present for this workspace run; **must not** be committed.
- **Join coverage (committed):** `local_detailed_trade_context_replay_v1/aggregates/trade_context_coverage.csv` → **10,628** rows with decision-time join fields populated.

## v1 router / quality result paths (reference)

- Router v1: `local_detailed_trade_context_replay_v1/router_diagnostics_v1/router_filter_results.csv`
- Quality v1: `local_detailed_trade_context_replay_v1/quality_score_v2/quality_group_results.csv`
- Playbook design: `playbook_router_research_cycle_v1/router_design_v1/offline_router_rule_design.csv`

## README / docs staleness (pre-fix)

- `README.md` had drifted toward long historical narrative and under-described the Layer3/playbook/local-replay architecture.

## Scripts reviewed for readability

- `run_local_trade_context_replay.py`, `run_offline_router_diagnostics.py`, `run_trade_quality_score_v2.py`, `build_trade_context_panel.py`, `analyze_playbook_context.py` — see `script_cleanup_inventory.md`.

## Missing files (none blocking)

- No missing committed aggregates required to run v2 diagnostics once the local panel exists.
