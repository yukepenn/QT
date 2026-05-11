# baseline_inventory — exit_overlay_diagnostics_v2

| Item | Value |
|------|--------|
| **Git tip (this commit)** | Resolve with `git rev-parse HEAD` after pull |
| **V1 decision** | `RUN_EXIT_OVERLAY_DIAGNOSTICS_V2` (`exit_overlay_diagnostics_v1/exit_overlay_diagnostics_decision.md`) |
| **NEXT_HANDOFF before V2** | Was still framed on v1 execution; V2 updates handoff to replay-alignment scope |
| **Champion v0** | `pa_only_mtp1_meta` (CLEAN_BASELINE, PA_003); `pa_gap_mtp2_meta` (DEFAULT, PA+GAP_001); `primary_mtp2_meta` (BREADTH, +CCI_003) |
| **V1 overlay paths** | `src/research/results/exit_overlay_diagnostics_v1/overlay_results_*.csv`, `overlay_sanity_vs_original.csv` |
| **V1 replay warning** | `fixed_target_replay` vs panel `r_multiple` mean abs diff ~0.28–0.38R — diagnostic only |
| **Local panel** | `local_detailed_trade_context_replay_v1/local_rows/trade_context_panel.csv` — **local-only** |
| **QQQ bars** | `data/raw/ibkr/equity/bars_1min/symbol=QQQ/**/data.parquet` — **not in public clone** |
| **Missing in CI checkout** | Parquet partitions → alignment returns `ALIGNMENT_DATA_LIMITED` / synthetic-only rows in curated CSVs |
| **V2 scope** | Combiner-clone replay grid; contextual overlays; ambiguity policies; aggregates vs **clone** baseline |
| **Non-goals** | WFO/live/SPY/broad L2; production router/exit-management; strategy/YAML edits; row-level commits |
