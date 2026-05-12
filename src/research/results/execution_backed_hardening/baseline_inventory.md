# Baseline inventory — execution-backed hardening

Captured at task start (git tip **`0c2e0dc`** — exit overlay diagnostic complete).

- **Prior NEXT_HANDOFF / exit-overlay decision:** `USE_EXECUTION_BACKED_FOR_RESEARCH_AND_REBUILD_LAYER1_2_3`
- **Readiness:** `EXECUTION_BACKED_READY_FOR_RESEARCH` (from `combiner_adapter_parity/execution_backed_readiness.md`)
- **Gaps addressed in this pass:** session-boundary next-bar entry, cooldown reset on new session, `min_risk_per_share` on `ExecutionPolicy` + materialization enforcement, scale-out fraction vs **remaining** qty, doc/handoff sync, fast-path plan (no Numba implementation).

Machine-readable: `baseline_inventory.csv`.
