# baseline_inventory — exit_overlay_diagnostics_v1

## Git tip before this work

- **`fefb268`** — `Research(router): refine offline quality diagnostics` (synced `main` at task start).

## Formal decision upstream (router_quality_refinement_v2)

- **`RUN_EXIT_OVERLAY_DIAGNOSTICS`** — see `src/research/results/router_quality_refinement_v2/router_quality_refinement_v2_decision.md`.

## NEXT_HANDOFF.md status (pre-exit-cycle)

- Prior repo-root handoff still emphasized **router/quality v2** completion and listed **`RUN_EXIT_OVERLAY_DIAGNOSTICS`** as decision **I** only; it did **not** yet reflect the executed **exit_overlay_diagnostics_v1** harness, validation counts, or the new post-run decision label.
- **Action:** `NEXT_HANDOFF.md` refreshed in this cycle for the **exit-overlay** workstream (full A–L).

## Champion v0 (frozen)

| profile_id | role |
|------------|------|
| `pa_only_mtp1_meta` | CLEAN_BASELINE — `PA_BUY_SELL_CLOSE_TREND_003` |
| `pa_gap_mtp2_meta` | DEFAULT_COMBINED — PA + `GAP_ACCEPTANCE_FAILURE_001` |
| `primary_mtp2_meta` | BREADTH_REFERENCE_ONLY — PA + GAP + `CCI_EXTREME_SNAPBACK_003` |

## Local row-level dependency

- **Panel path (local-only, gitignored):** `src/research/results/local_detailed_trade_context_replay_v1/local_rows/trade_context_panel.csv`
- **Status at run:** present — **10,628** rows, **170** columns (Champion v0 profiles × windows as filtered in runner).
- **Overlay row output (local-only):** `src/research/results/exit_overlay_diagnostics_v1/local_rows/overlay_trade_results.csv` — **not** committed.

## Router / quality v2 result paths (reference)

- `src/research/results/router_quality_refinement_v2/router_v2/router_v2_results.csv`
- `src/research/results/router_quality_refinement_v2/quality_v2_refined/quality_variant_results.csv`
- `src/research/results/router_quality_refinement_v2/combined_light_guards/combined_guard_results.csv`

## Exit readiness / design sources

- `src/research/results/local_detailed_trade_context_replay_v1/exit_overlay_readiness_v1/`
- `src/research/results/playbook_router_research_cycle_v1/exit_overlay_design_v1/exit_overlay_design.csv`

## QQQ 1m bars (canonical)

- Loader: `src/data/read_bars.py` — `read_bars(asset="equity", symbol="QQQ", ...)`
- **Coverage check:** `overlay_data_quality.csv` — `missing_count=0`; `overlay_input_coverage.csv` — **1526** session dates, **0** sessions without bars.

## Local-only vs committed

| Path | Commit |
|------|--------|
| `trade_context_panel.csv` | **no** (gitignored) |
| `local_rows/**` under this root | **no** |
| Aggregate CSV/MD, scripts, tests, indexes | **yes** |
