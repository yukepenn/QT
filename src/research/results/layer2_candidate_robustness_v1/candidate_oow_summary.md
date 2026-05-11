# Candidate-level OOW audit — compact summary

## Scope

- **Candidates:** 27 (families **vwap** + **indicator** from l2_core)
- **Windows:** `early_oow`, `insample_ref`, `late_oow`
- **Runs:** 81 singleton combiner replays (`local_runs/**` local-only)

## Robustness label counts (candidate-level)

| robustness_label | count |
|------------------|------:|
| OOW_MIXED | 17 |
| INSAMPLE_ONLY | 7 |
| ROBUST_POSITIVE | 2 |
| ANTI_PREDICTIVE_CANDIDATE | 1 |

## Policy action counts

| policy_action | count |
|---------------|------:|
| WATCHLIST_DIAGNOSTIC | 17 |
| DROP_FROM_CORE | 7 |
| KEEP_CORE_CANDIDATE | 2 |
| REQUIRES_SIDE_FLIP_RESEARCH | 1 |

## ROBUST_POSITIVE (this slice)

- `CCI_EXTREME_SNAPBACK_002`
- `CCI_EXTREME_SNAPBACK_003`

## INSAMPLE_ONLY (this slice)

`MACD_MOMENTUM_TURN_001`, `MACD_MOMENTUM_TURN_002`, `RSI_FAILURE_SWING_002`, `SUPERTREND_ATR_FLIP_004`, `VWAP_RECLAIM_REJECT_001`, `VWAP_RECLAIM_REJECT_002`, `VWAP_RECLAIM_REJECT_003`

## Artifacts

- Long metrics: `candidate_oow_metrics.csv`
- Wide + embedded labels: `candidate_oow_wide_metrics.csv`
- Labels: `candidate_robustness_labels.csv`
- Family/strategy rolls: `family_oow_summary.csv`, `strategy_oow_summary.csv`
- Profile-aware join: `l2_core_failure_analysis.csv`
- Manifests: `candidate_audit_run_manifest.csv`, `run_execution_manifest.csv`, `run_discovery_manifest.csv`
