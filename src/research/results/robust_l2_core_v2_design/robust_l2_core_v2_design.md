# Robust l2_core v2 — design-only plan

## 1. Purpose

Convert the **10** nominal `ROBUST_POSITIVE` singleton candidates into a **deduped** set of **effective signals** for a future small Layer2 diagnostic.

## 2. Non-goals

- no Layer2 sweep
- no WFO
- no live/paper
- no SPY
- no strategy/feature/YAML edits
- no router
- no production short support
- no OOW tuning

## 3. Source evidence (full 66/66 audit)

- Robust-positive: **10**
- Anti-predictive: **5**
- Family winners: `pa` (close trend), `opening_trap` (gap acceptance), `indicator` (CCI pocket)

## 4. Effective signal clusters

| cluster_id | cluster_kind | audit_family | strategy | members | n_members | representative_candidate_id | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cluster_01 | METRIC_IDENTICAL | opening_trap | gap_acceptance_failure | GAP_ACCEPTANCE_FAILURE_001,GAP_ACCEPTANCE_FAILURE_002,GAP_ACCEPTANCE_FAILURE_003,GAP_ACCEPTANCE_FAILURE_004 | 4 | GAP_ACCEPTANCE_FAILURE_001 | same trades-by-window + same total_r-by-window (rounded) under the audit envelope |
| trade_identical_gap_acceptance_failure_opening_trap | TRADE_IDENTICAL | opening_trap | gap_acceptance_failure | GAP_ACCEPTANCE_FAILURE_001,GAP_ACCEPTANCE_FAILURE_002,GAP_ACCEPTANCE_FAILURE_003,GAP_ACCEPTANCE_FAILURE_004 | 4 | GAP_ACCEPTANCE_FAILURE_001 | entry_ts_utc and session_date sets identical across windows (Jaccard=1.0); treat as one effective signal |
| trade_identical_pa_buy_sell_close_trend_pa | TRADE_IDENTICAL | pa | pa_buy_sell_close_trend | PA_BUY_SELL_CLOSE_TREND_001,PA_BUY_SELL_CLOSE_TREND_002,PA_BUY_SELL_CLOSE_TREND_003 | 3 | PA_BUY_SELL_CLOSE_TREND_001 | entry_ts_utc and session_date sets identical across windows (Jaccard=1.0); treat as one effective signal |
| cluster_02 | METRIC_IDENTICAL | indicator | cci_extreme_snapback | CCI_EXTREME_SNAPBACK_002 | 1 | CCI_EXTREME_SNAPBACK_002 | same trades-by-window + same total_r-by-window (rounded) under the audit envelope |
| cluster_03 | METRIC_IDENTICAL | indicator | cci_extreme_snapback | CCI_EXTREME_SNAPBACK_003 | 1 | CCI_EXTREME_SNAPBACK_003 | same trades-by-window + same total_r-by-window (rounded) under the audit envelope |
| cluster_04 | METRIC_IDENTICAL | pa | pa_buy_sell_close_trend | PA_BUY_SELL_CLOSE_TREND_001 | 1 | PA_BUY_SELL_CLOSE_TREND_001 | same trades-by-window + same total_r-by-window (rounded) under the audit envelope |
| cluster_05 | METRIC_IDENTICAL | pa | pa_buy_sell_close_trend | PA_BUY_SELL_CLOSE_TREND_002 | 1 | PA_BUY_SELL_CLOSE_TREND_002 | same trades-by-window + same total_r-by-window (rounded) under the audit envelope |
| cluster_06 | METRIC_IDENTICAL | pa | pa_buy_sell_close_trend | PA_BUY_SELL_CLOSE_TREND_003 | 1 | PA_BUY_SELL_CLOSE_TREND_003 | same trades-by-window + same total_r-by-window (rounded) under the audit envelope |
| cluster_07 | METRIC_IDENTICAL | pa | pa_buy_sell_close_trend | PA_BUY_SELL_CLOSE_TREND_004 | 1 | PA_BUY_SELL_CLOSE_TREND_004 | same trades-by-window + same total_r-by-window (rounded) under the audit envelope |


## 5. Dedupe rules

- Metric-identical candidates (same trades + same total_r across windows) count as **one** effective signal cluster.
- Near-duplicates are capped; prefer candidates with **positive both OOW** and better cross-window balance.
- Catastrophic OOW candidates stay **out** of core sets.

## 6. Candidate-set design

| candidate_set | candidate_id | purpose |
| --- | --- | --- |
| primary_representative_core | GAP_ACCEPTANCE_FAILURE_001 | minimum redundancy; maximum interpretability |
| primary_representative_core | PA_BUY_SELL_CLOSE_TREND_003 | minimum redundancy; maximum interpretability |
| primary_representative_core | CCI_EXTREME_SNAPBACK_003 | minimum redundancy; maximum interpretability |
| balanced_representative_core | GAP_ACCEPTANCE_FAILURE_001 | slightly broader core; still deduped |
| balanced_representative_core | PA_BUY_SELL_CLOSE_TREND_003 | slightly broader core; still deduped |
| balanced_representative_core | PA_BUY_SELL_CLOSE_TREND_004 | slightly broader core; still deduped |
| balanced_representative_core | CCI_EXTREME_SNAPBACK_003 | slightly broader core; still deduped |
| balanced_representative_core | CCI_EXTREME_SNAPBACK_002 | slightly broader core; still deduped |
| extended_robust_watchlist | CCI_EXTREME_SNAPBACK_002 | all nominal robust-positive (doc-only) |
| extended_robust_watchlist | CCI_EXTREME_SNAPBACK_003 | all nominal robust-positive (doc-only) |
| extended_robust_watchlist | GAP_ACCEPTANCE_FAILURE_001 | all nominal robust-positive (doc-only) |
| extended_robust_watchlist | GAP_ACCEPTANCE_FAILURE_002 | all nominal robust-positive (doc-only) |
| extended_robust_watchlist | GAP_ACCEPTANCE_FAILURE_003 | all nominal robust-positive (doc-only) |
| extended_robust_watchlist | GAP_ACCEPTANCE_FAILURE_004 | all nominal robust-positive (doc-only) |
| extended_robust_watchlist | PA_BUY_SELL_CLOSE_TREND_001 | all nominal robust-positive (doc-only) |
| extended_robust_watchlist | PA_BUY_SELL_CLOSE_TREND_002 | all nominal robust-positive (doc-only) |
| extended_robust_watchlist | PA_BUY_SELL_CLOSE_TREND_003 | all nominal robust-positive (doc-only) |
| extended_robust_watchlist | PA_BUY_SELL_CLOSE_TREND_004 | all nominal robust-positive (doc-only) |
| exclude_from_core | MACD_MOMENTUM_TURN_001 | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets |
| exclude_from_core | MACD_MOMENTUM_TURN_002 | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets |
| exclude_from_core | MACD_MOMENTUM_TURN_003 | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets |
| exclude_from_core | MULTI_DAY_LEVEL_TRAP_001 | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets |
| exclude_from_core | MULTI_DAY_LEVEL_TRAP_002 | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets |
| exclude_from_core | MULTI_DAY_LEVEL_TRAP_003 | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets |
| exclude_from_core | MULTI_DAY_LEVEL_TRAP_004 | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets |
| exclude_from_core | PA_TRADING_RANGE_BLS_HS_005 | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets |
| exclude_from_core | RSI_FAILURE_SWING_002 | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets |
| exclude_from_core | SUPERTREND_ATR_FLIP_004 | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets |
| exclude_from_core | VWAP_RECLAIM_REJECT_001 | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets |
| exclude_from_core | VWAP_RECLAIM_REJECT_002 | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets |
| exclude_from_core | VWAP_RECLAIM_REJECT_003 | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets |


## 7. Future Layer2 diagnostic design (NOT RUN here)

- Candidate-set axis (design buckets): primary vs balanced vs ablations (PA-only, GAP-only, CCI-only, pairwise mixes).
- Risk control axis (design only): `max_trades_per_day` ∈ {1, 2}; `daily_max_loss_r` ∈ {−1.5, −2.0}; `priority_policy` ∈ {metadata_priority, score_adjusted_priority}.
- No router; no broad grid.

## 8. Interpretation

- Singleton OOW robustness does **not** guarantee combination robustness.
- This is a design transition from broad l2_core to a deduped robust pocket for diagnostics.

## 9. Recommended next step

**`RUN_SMALL_ROBUST_CORE_LAYER2_DIAGNOSTIC_DESIGN`** (produce runnable configs in a follow-up task; do not execute here).
