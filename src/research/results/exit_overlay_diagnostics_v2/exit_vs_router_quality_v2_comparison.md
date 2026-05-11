# Exit vs router / quality v2 (post exit-overlay v2 scaffolding)

Router/quality v2 answers **which trades to keep**; exit overlay v2 answers **how exits could differ** given identical entries.

Until **`combiner_clone_replay`** matches panel `r_multiple` within agreed gates, treat **exit overlay v2 PF / drawdown deltas as non-actionable** for integration priority.

Programmatic “best row” picks remain in `router_quality_refinement_v2/` CSVs referenced by v1 `run_exit_overlay_diagnostics.write_router_quality_comparison`.
