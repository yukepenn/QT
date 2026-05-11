# CHATGPT_REVIEW_BUNDLE — Playbook Router Research Cycle v1

## 1) Git / validation
- git_tip: `e1dc075a29418b5166c0b4306456b0d4e4103711`

## 2) Why Champion v0 is frozen
- See `champion_v0_freeze.md`

## 3) Champion v0 roles
- PA-only baseline; PA+GAP default; primary/CCI reference-only.

## 4) Stop over-polishing strategies
- Pivot to **context permissioning**, **trade quality**, **exit management**, and **isolated short/scalp** branches later.

## 5) Trade-context panel
- Schema: `trade_context_panel_schema.csv`
- Aggregates: `trade_context_panel_v1/`
- Missing: `trade_context_missing_inputs.csv`

## 6) Context diagnostics
- `context_diagnostics_v1/context_diagnostics_summary.md`

## 7) Candidate playbook metadata
- `router_metadata_v1/candidate_playbook_metadata.csv`

## 8) Offline router design
- `router_design_v1/offline_router_rule_design.csv` + `router_v1_config_draft.yaml` (`enabled: false`)

## 9) Trade-quality score v2
- `trade_quality_score_v2/trade_quality_score_design.md` (weights sum to 100%)

## 10) Exit overlay design
- `exit_overlay_design_v1/exit_overlay_design.csv`

## 11) Scalp roadmap
- `scalp_strategy_roadmap_v1/` — all **DESIGN_ONLY_NOT_IMPLEMENTED**

## 12) Short roadmap
- `short_strategy_roadmap_v1/` — **DESIGN_ONLY_NOT_IMPLEMENTED**

## 13) Next 3-layer sweep
- `next_3layer_sweep_roadmap.csv`

## 14) Decision
- **`RUN_LOCAL_DETAILED_TRADE_CONTEXT_REPLAY`**

## 15) Explicit non-runs
- No WFO/live/SPY/broad L2/new strategies/router implementation/YAML edits

## 16) Recommended next step
- Local-only row-level trade-context build + backward feature join (disk only), then offline router diagnostics.
