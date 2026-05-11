# Robust l2_core v2 — design summary

## 1. Purpose
Deduplicate 10 robust-positive singleton candidates into effective clusters and representative candidate sets.

## 2. Input evidence
- 66/66 singleton audit complete; 198/198 metric rows OK.
- Robust-positive: 10; Anti-predictive: 5.

## 3. Robust candidate clusters
| cluster_id | cluster_kind | audit_family | strategy | members | n_members | representative_candidate_id | raw_cluster_representative | design_representative | design_representative_reason | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cluster_01 | METRIC_IDENTICAL | opening_trap | gap_acceptance_failure | GAP_ACCEPTANCE_FAILURE_001,GAP_ACCEPTANCE_FAILURE_002,GAP_ACCEPTANCE_FAILURE_003,GAP_ACCEPTANCE_FAILURE_004 | 4 | GAP_ACCEPTANCE_FAILURE_001 | GAP_ACCEPTANCE_FAILURE_001 | GAP_ACCEPTANCE_FAILURE_001 | dedupe GAP cluster to one representative | same trades-by-window + same total_r-by-window (rounded) under the audit envelope |
| trade_identical_gap_acceptance_failure_opening_trap | TRADE_IDENTICAL | opening_trap | gap_acceptance_failure | GAP_ACCEPTANCE_FAILURE_001,GAP_ACCEPTANCE_FAILURE_002,GAP_ACCEPTANCE_FAILURE_003,GAP_ACCEPTANCE_FAILURE_004 | 4 | GAP_ACCEPTANCE_FAILURE_001 | GAP_ACCEPTANCE_FAILURE_001 | GAP_ACCEPTANCE_FAILURE_001 | dedupe GAP cluster to one representative | entry_ts_utc and session_date sets identical across windows (Jaccard=1.0); treat as one effective signal |
| trade_identical_pa_buy_sell_close_trend_pa | TRADE_IDENTICAL | pa | pa_buy_sell_close_trend | PA_BUY_SELL_CLOSE_TREND_001,PA_BUY_SELL_CLOSE_TREND_002,PA_BUY_SELL_CLOSE_TREND_003 | 3 | PA_BUY_SELL_CLOSE_TREND_001 | PA_BUY_SELL_CLOSE_TREND_001 | PA_BUY_SELL_CLOSE_TREND_003 | best cross-window balance among trade-identical entries | entry_ts_utc and session_date sets identical across windows (Jaccard=1.0); treat as one effective signal |
| cluster_02 | METRIC_IDENTICAL | indicator | cci_extreme_snapback | CCI_EXTREME_SNAPBACK_002 | 1 | CCI_EXTREME_SNAPBACK_002 | CCI_EXTREME_SNAPBACK_002 | CCI_EXTREME_SNAPBACK_002 | default = raw representative | same trades-by-window + same total_r-by-window (rounded) under the audit envelope |
| cluster_03 | METRIC_IDENTICAL | indicator | cci_extreme_snapback | CCI_EXTREME_SNAPBACK_003 | 1 | CCI_EXTREME_SNAPBACK_003 | CCI_EXTREME_SNAPBACK_003 | CCI_EXTREME_SNAPBACK_003 | primary CCI (positive both OOW) | same trades-by-window + same total_r-by-window (rounded) under the audit envelope |
| cluster_04 | METRIC_IDENTICAL | pa | pa_buy_sell_close_trend | PA_BUY_SELL_CLOSE_TREND_001 | 1 | PA_BUY_SELL_CLOSE_TREND_001 | PA_BUY_SELL_CLOSE_TREND_001 | PA_BUY_SELL_CLOSE_TREND_001 | default = raw representative | same trades-by-window + same total_r-by-window (rounded) under the audit envelope |
| cluster_05 | METRIC_IDENTICAL | pa | pa_buy_sell_close_trend | PA_BUY_SELL_CLOSE_TREND_002 | 1 | PA_BUY_SELL_CLOSE_TREND_002 | PA_BUY_SELL_CLOSE_TREND_002 | PA_BUY_SELL_CLOSE_TREND_002 | default = raw representative | same trades-by-window + same total_r-by-window (rounded) under the audit envelope |
| cluster_06 | METRIC_IDENTICAL | pa | pa_buy_sell_close_trend | PA_BUY_SELL_CLOSE_TREND_003 | 1 | PA_BUY_SELL_CLOSE_TREND_003 | PA_BUY_SELL_CLOSE_TREND_003 | PA_BUY_SELL_CLOSE_TREND_003 | default = raw representative | same trades-by-window + same total_r-by-window (rounded) under the audit envelope |
| cluster_07 | METRIC_IDENTICAL | pa | pa_buy_sell_close_trend | PA_BUY_SELL_CLOSE_TREND_004 | 1 | PA_BUY_SELL_CLOSE_TREND_004 | PA_BUY_SELL_CLOSE_TREND_004 | PA_BUY_SELL_CLOSE_TREND_004 | default = raw representative | same trades-by-window + same total_r-by-window (rounded) under the audit envelope |


## 4. Deduplication results
- GAP 001–004 collapsed to one effective cluster by metric identity.
- PA close-trend remains a multi-member cluster (near-duplicate table + optional trade overlap guide caps).
- CCI 003 primary; CCI 002 watchlist/secondary.

## 5. Representative core design
- `primary_representative_core`: 3 names (GAP + PA + CCI).
- `balanced_representative_core`: 5 names (adds PA secondary + CCI secondary).

## 6. Watchlist/drop design
See `core_watchlist_drop_actions.csv` and `core_watchlist_drop_policy.md`.

## 7. Future small Layer2 diagnostic plan (not run)
Design-only ablation candidate sets + small risk-control grid (mtp/day-loss/priority axes).

## 8. What was intentionally not done
No sweeps, WFO, YAML edits, router, short support, or OOW tuning; no raw trades committed.

## 9. Decision
**`RUN_SMALL_ROBUST_CORE_LAYER2_DIAGNOSTIC_DESIGN`**

## 10. Recommended next step
Create runnable (still-not-run) config skeletons and a runbook for a follow-up diagnostic-only execution task.
