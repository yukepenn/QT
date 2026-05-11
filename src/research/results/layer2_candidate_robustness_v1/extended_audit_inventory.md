# Extended audit inventory

## Repo / handoff

- **git tip:** `d058827 Docs(handoff): mark push complete`
- **handoff decision (parsed from `layer2_candidate_robustness_decision.md` then `NEXT_HANDOFF.md`):** `CREATE_ROBUST_L2_CORE_V2_DESIGN`

## Candidate root and coverage

- candidate root: `D:/OneDrive - Washington University in St. Louis/QT/src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates`
- total l2_core YAMLs: **66**
- fully replayed (metrics.json on all **3** windows): **66**
- remaining without full metrics grid: **0**
- planned in filtered slice (`planned_for_extended_audit=yes`): **0**
- **audit families already complete:** afternoon, indicator, opening_trap, other, pa, vwap
- **families still incomplete (if any):** (none — full grid)

## Candidate IDs

### Planned for extended singleton run (this filter)

- *(none — all candidates have metrics on all windows, or filter excluded remaining)*

### All l2_core candidates (metrics complete on all windows)

**66** candidates — list for inventory reconciliation (not only last-wave skips).

- AFTERNOON_CONTINUATION_001
- AFTERNOON_CONTINUATION_002
- AFTERNOON_CONTINUATION_003
- AFTERNOON_CONTINUATION_004
- CCI_EXTREME_SNAPBACK_001
- CCI_EXTREME_SNAPBACK_002
- CCI_EXTREME_SNAPBACK_003
- CCI_EXTREME_SNAPBACK_004
- MACD_MOMENTUM_TURN_001
- MACD_MOMENTUM_TURN_002
- MACD_MOMENTUM_TURN_003
- RSI_FAILURE_SWING_001
- RSI_FAILURE_SWING_002
- RSI_FAILURE_SWING_003
- RSI_FAILURE_SWING_005
- STOCHASTIC_OVERSOLD_CROSS_001
- STOCHASTIC_OVERSOLD_CROSS_002
- STOCHASTIC_OVERSOLD_CROSS_003
- STOCHASTIC_OVERSOLD_CROSS_004
- SUPERTREND_ATR_FLIP_001
- SUPERTREND_ATR_FLIP_002
- SUPERTREND_ATR_FLIP_003
- SUPERTREND_ATR_FLIP_004
- FAILED_ORB_001
- FAILED_ORB_002
- FAILED_ORB_003
- FAILED_ORB_005
- GAP_ACCEPTANCE_FAILURE_001
- GAP_ACCEPTANCE_FAILURE_002
- GAP_ACCEPTANCE_FAILURE_003
- GAP_ACCEPTANCE_FAILURE_004
- MULTI_DAY_LEVEL_TRAP_001
- MULTI_DAY_LEVEL_TRAP_002
- MULTI_DAY_LEVEL_TRAP_003
- MULTI_DAY_LEVEL_TRAP_004
- ORB_CONTINUATION_001
- ORB_CONTINUATION_002
- ORB_CONTINUATION_003
- PRIOR_CLOSE_RECLAIM_001
- PRIOR_CLOSE_RECLAIM_002
- PRIOR_CLOSE_RECLAIM_003
- PRIOR_CLOSE_RECLAIM_005
- PA_BUY_SELL_CLOSE_TREND_001
- PA_BUY_SELL_CLOSE_TREND_002
- PA_BUY_SELL_CLOSE_TREND_003
- PA_BUY_SELL_CLOSE_TREND_004
- PA_CLIMAX_REVERSAL_001
- PA_CLIMAX_REVERSAL_002
- PA_CLIMAX_REVERSAL_003
- PA_CLIMAX_REVERSAL_004
- PA_FAILED_RANGE_BREAKOUT_TRAP_001
- PA_FAILED_RANGE_BREAKOUT_TRAP_002
- PA_FAILED_RANGE_BREAKOUT_TRAP_003
- PA_FAILED_RANGE_BREAKOUT_TRAP_005
- PA_TRADING_RANGE_BLS_HS_001
- PA_TRADING_RANGE_BLS_HS_002
- PA_TRADING_RANGE_BLS_HS_003
- PA_TRADING_RANGE_BLS_HS_005
- VWAP_RECLAIM_REJECT_001
- VWAP_RECLAIM_REJECT_002
- VWAP_RECLAIM_REJECT_003
- VWAP_RECLAIM_REJECT_004
- VWAP_TREND_PULLBACK_001
- VWAP_TREND_PULLBACK_002
- VWAP_TREND_PULLBACK_003
- VWAP_TREND_PULLBACK_005

## Local raw runs (do not commit)

- `D:/OneDrive - Washington University in St. Louis/QT/src/research/results/layer2_candidate_robustness_v1/local_runs/<candidate_id>/<window_id>/run_*`

## Postprocess outputs (curated, under output root)

- `candidate_oow_metrics.csv`
- `candidate_oow_wide_metrics.csv`
- `candidate_robustness_labels.csv`
- `family_oow_summary.csv`
- `strategy_oow_summary.csv`
- `candidate_audit_run_manifest.csv`
- `run_execution_manifest.csv`
- `run_discovery_manifest.csv`
- `l2_core_failure_analysis.csv`
- `l2_core_policy_v2_candidate_actions.csv`

## Reconciliation

- `n_all` (66) = `n_aud` (66) + incomplete (0)
