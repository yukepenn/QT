# Candidate-level OOW audit — compact summary

## Scope

- **Candidates:** 66 (full l2_core singleton grid)
- **Windows:** `early_oow`, `insample_ref`, `late_oow`
- **Runs:** 198 singleton combiner replays expected (`local_runs/**` local-only)

## Robustness label counts (candidate-level)

| robustness_label | count |
|------------------|------:|
| OOW_MIXED | 40 |
| ROBUST_POSITIVE | 10 |
| INSAMPLE_ONLY | 8 |
| ANTI_PREDICTIVE_CANDIDATE | 5 |
| OOW_NEGATIVE | 3 |

## Policy action counts

| policy_action | count |
|---------------|------:|
| WATCHLIST_DIAGNOSTIC | 43 |
| KEEP_CORE_CANDIDATE | 10 |
| DROP_FROM_CORE | 8 |
| REQUIRES_SIDE_FLIP_RESEARCH | 5 |

## ROBUST_POSITIVE

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

## INSAMPLE_ONLY

MACD_MOMENTUM_TURN_001, MACD_MOMENTUM_TURN_002, PA_TRADING_RANGE_BLS_HS_005, RSI_FAILURE_SWING_002, SUPERTREND_ATR_FLIP_004, VWAP_RECLAIM_REJECT_001, VWAP_RECLAIM_REJECT_002, VWAP_RECLAIM_REJECT_003

## Artifacts

- Long metrics: `candidate_oow_metrics.csv`
- Wide + embedded labels: `candidate_oow_wide_metrics.csv`
- Labels: `candidate_robustness_labels.csv`
- Family/strategy rolls: `family_oow_summary.csv`, `strategy_oow_summary.csv`
- Profile-aware join: `l2_core_failure_analysis.csv`
- Manifests: `candidate_audit_run_manifest.csv`, `run_execution_manifest.csv`, `run_discovery_manifest.csv`