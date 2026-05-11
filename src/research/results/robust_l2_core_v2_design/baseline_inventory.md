# Robust l2_core v2 design — baseline inventory

- **git tip:** `67cbe86 Docs(handoff): note final push tip range`
- **handoff decision:** `CREATE_ROBUST_L2_CORE_V2_DESIGN`
- **audit coverage:** 66 / 66 candidates; 198 / 198 candidate-window metric rows OK

## Robust-positive candidates (nominal, n=10)

- CCI_EXTREME_SNAPBACK_002
- CCI_EXTREME_SNAPBACK_003
- GAP_ACCEPTANCE_FAILURE_001
- GAP_ACCEPTANCE_FAILURE_002
- GAP_ACCEPTANCE_FAILURE_003
- GAP_ACCEPTANCE_FAILURE_004
- PA_BUY_SELL_CLOSE_TREND_001
- PA_BUY_SELL_CLOSE_TREND_002
- PA_BUY_SELL_CLOSE_TREND_003
- PA_BUY_SELL_CLOSE_TREND_004

## Anti-predictive candidates (n=5)

- MACD_MOMENTUM_TURN_003
- MULTI_DAY_LEVEL_TRAP_001
- MULTI_DAY_LEVEL_TRAP_002
- MULTI_DAY_LEVEL_TRAP_003
- MULTI_DAY_LEVEL_TRAP_004

## Current policy-action counts (from full audit)

- KEEP_CORE_CANDIDATE: **10**
- WATCHLIST_DIAGNOSTIC: **43**
- DROP_FROM_CORE: **8**
- REQUIRES_SIDE_FLIP_RESEARCH: **5**

## Files inspected / inputs

- `D:/OneDrive - Washington University in St. Louis/QT/src/research/results/layer2_candidate_robustness_v1/candidate_robustness_labels.csv`
- `D:/OneDrive - Washington University in St. Louis/QT/src/research/results/layer2_candidate_robustness_v1/candidate_oow_metrics.csv` (not parsed here; labels are authoritative)
- `D:/OneDrive - Washington University in St. Louis/QT/src/research/results/layer2_candidate_robustness_v1/robust_core_dry_run/selected_candidates_manifest.csv`

## Local raw run availability

- local runs root: `D:/OneDrive - Washington University in St. Louis/QT/src/research/results/layer2_candidate_robustness_v1/local_runs`
- trade overlap read: **enabled**

## Expected outputs from this design pack

- `robust_candidate_dedupe_table.csv`
- `effective_signal_clusters.csv`
- `robust_candidate_near_duplicates.csv`
- `robust_candidate_overlap_matrix.csv`
- `robust_candidate_overlap_summary.md`
- `representative_candidate_manifest.{csv,md}`
- `candidate_sets_design.{csv,md}`
- `core_watchlist_drop_policy.md`
- `core_watchlist_drop_actions.csv`
- `robust_l2_core_v2_design.md`
- `robust_l2_core_v2_decision.md`
- `robust_l2_core_v2_design_summary.md`
- `robust_l2_core_v2_key_findings.csv`
