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


## 5. Dedupe rules

- Metric-identical candidates (same trades + same total_r across windows) count as **one** effective signal cluster.
- Near-duplicates are capped; prefer candidates with **positive both OOW** and better cross-window balance.
- Catastrophic OOW candidates stay **out** of core sets.

## 6. Candidate-set design

| candidate_set | candidate_id | strategy | family | role_in_set | source_yaml_path | purpose | caveat | run_recommended | design_only |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| balanced_representative_core | CCI_EXTREME_SNAPBACK_002 | cci_extreme_snapback | indicator | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/CCI_EXTREME_SNAPBACK_002.yaml | slightly broader core; still deduped | adds PA_004 partial-overlap and CCI_002 secondary (weaker early OOW) | yes | yes |
| balanced_representative_core | CCI_EXTREME_SNAPBACK_003 | cci_extreme_snapback | indicator | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/CCI_EXTREME_SNAPBACK_003.yaml | slightly broader core; still deduped | adds PA_004 partial-overlap and CCI_002 secondary (weaker early OOW) | yes | yes |
| balanced_representative_core | GAP_ACCEPTANCE_FAILURE_001 | gap_acceptance_failure | opening_trap | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/GAP_ACCEPTANCE_FAILURE_001.yaml | slightly broader core; still deduped | adds PA_004 partial-overlap and CCI_002 secondary (weaker early OOW) | yes | yes |
| balanced_representative_core | PA_BUY_SELL_CLOSE_TREND_003 | pa_buy_sell_close_trend | pa | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/PA_BUY_SELL_CLOSE_TREND_003.yaml | slightly broader core; still deduped | adds PA_004 partial-overlap and CCI_002 secondary (weaker early OOW) | yes | yes |
| balanced_representative_core | PA_BUY_SELL_CLOSE_TREND_004 | pa_buy_sell_close_trend | pa | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/PA_BUY_SELL_CLOSE_TREND_004.yaml | slightly broader core; still deduped | adds PA_004 partial-overlap and CCI_002 secondary (weaker early OOW) | yes | yes |
| cci_only_core | CCI_EXTREME_SNAPBACK_002 | cci_extreme_snapback | indicator | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/CCI_EXTREME_SNAPBACK_002.yaml | single-family ablation | CCI_002 is secondary (early OOW weak) | yes | yes |
| cci_only_core | CCI_EXTREME_SNAPBACK_003 | cci_extreme_snapback | indicator | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/CCI_EXTREME_SNAPBACK_003.yaml | single-family ablation | CCI_002 is secondary (early OOW weak) | yes | yes |
| exclude_from_core | MACD_MOMENTUM_TURN_001 | macd_momentum_turn | indicator | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/MACD_MOMENTUM_TURN_001.yaml | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets | research contrasts only; do not promote to core | no | yes |
| exclude_from_core | MACD_MOMENTUM_TURN_002 | macd_momentum_turn | indicator | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/MACD_MOMENTUM_TURN_002.yaml | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets | research contrasts only; do not promote to core | no | yes |
| exclude_from_core | MACD_MOMENTUM_TURN_003 | macd_momentum_turn | indicator | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/MACD_MOMENTUM_TURN_003.yaml | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets | research contrasts only; do not promote to core | no | yes |
| exclude_from_core | MULTI_DAY_LEVEL_TRAP_001 | multi_day_level_trap | opening_trap | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/MULTI_DAY_LEVEL_TRAP_001.yaml | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets | research contrasts only; do not promote to core | no | yes |
| exclude_from_core | MULTI_DAY_LEVEL_TRAP_002 | multi_day_level_trap | opening_trap | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/MULTI_DAY_LEVEL_TRAP_002.yaml | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets | research contrasts only; do not promote to core | no | yes |
| exclude_from_core | MULTI_DAY_LEVEL_TRAP_003 | multi_day_level_trap | opening_trap | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/MULTI_DAY_LEVEL_TRAP_003.yaml | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets | research contrasts only; do not promote to core | no | yes |
| exclude_from_core | MULTI_DAY_LEVEL_TRAP_004 | multi_day_level_trap | opening_trap | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/MULTI_DAY_LEVEL_TRAP_004.yaml | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets | research contrasts only; do not promote to core | no | yes |
| exclude_from_core | PA_TRADING_RANGE_BLS_HS_005 | pa_trading_range_bls_hs | pa | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/PA_TRADING_RANGE_BLS_HS_005.yaml | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets | research contrasts only; do not promote to core | no | yes |
| exclude_from_core | RSI_FAILURE_SWING_002 | rsi_failure_swing | indicator | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/RSI_FAILURE_SWING_002.yaml | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets | research contrasts only; do not promote to core | no | yes |
| exclude_from_core | SUPERTREND_ATR_FLIP_004 | supertrend_atr_flip | indicator | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/SUPERTREND_ATR_FLIP_004.yaml | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets | research contrasts only; do not promote to core | no | yes |
| exclude_from_core | VWAP_RECLAIM_REJECT_001 | vwap_reclaim_reject | vwap | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/VWAP_RECLAIM_REJECT_001.yaml | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets | research contrasts only; do not promote to core | no | yes |
| exclude_from_core | VWAP_RECLAIM_REJECT_002 | vwap_reclaim_reject | vwap | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/VWAP_RECLAIM_REJECT_002.yaml | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets | research contrasts only; do not promote to core | no | yes |
| exclude_from_core | VWAP_RECLAIM_REJECT_003 | vwap_reclaim_reject | vwap | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/VWAP_RECLAIM_REJECT_003.yaml | DROP_FROM_CORE + SIDE_FLIP_RESEARCH_ONLY buckets | research contrasts only; do not promote to core | no | yes |
| extended_robust_watchlist | CCI_EXTREME_SNAPBACK_002 | cci_extreme_snapback | indicator | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/CCI_EXTREME_SNAPBACK_002.yaml | all nominal robust-positive (documentation only) | contains deduped equivalents; not recommended for immediate diagnostic | no | yes |
| extended_robust_watchlist | CCI_EXTREME_SNAPBACK_003 | cci_extreme_snapback | indicator | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/CCI_EXTREME_SNAPBACK_003.yaml | all nominal robust-positive (documentation only) | contains deduped equivalents; not recommended for immediate diagnostic | no | yes |
| extended_robust_watchlist | GAP_ACCEPTANCE_FAILURE_001 | gap_acceptance_failure | opening_trap | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/GAP_ACCEPTANCE_FAILURE_001.yaml | all nominal robust-positive (documentation only) | contains deduped equivalents; not recommended for immediate diagnostic | no | yes |
| extended_robust_watchlist | GAP_ACCEPTANCE_FAILURE_002 | gap_acceptance_failure | opening_trap | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/GAP_ACCEPTANCE_FAILURE_002.yaml | all nominal robust-positive (documentation only) | contains deduped equivalents; not recommended for immediate diagnostic | no | yes |
| extended_robust_watchlist | GAP_ACCEPTANCE_FAILURE_003 | gap_acceptance_failure | opening_trap | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/GAP_ACCEPTANCE_FAILURE_003.yaml | all nominal robust-positive (documentation only) | contains deduped equivalents; not recommended for immediate diagnostic | no | yes |
| extended_robust_watchlist | GAP_ACCEPTANCE_FAILURE_004 | gap_acceptance_failure | opening_trap | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/GAP_ACCEPTANCE_FAILURE_004.yaml | all nominal robust-positive (documentation only) | contains deduped equivalents; not recommended for immediate diagnostic | no | yes |
| extended_robust_watchlist | PA_BUY_SELL_CLOSE_TREND_001 | pa_buy_sell_close_trend | pa | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/PA_BUY_SELL_CLOSE_TREND_001.yaml | all nominal robust-positive (documentation only) | contains deduped equivalents; not recommended for immediate diagnostic | no | yes |
| extended_robust_watchlist | PA_BUY_SELL_CLOSE_TREND_002 | pa_buy_sell_close_trend | pa | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/PA_BUY_SELL_CLOSE_TREND_002.yaml | all nominal robust-positive (documentation only) | contains deduped equivalents; not recommended for immediate diagnostic | no | yes |
| extended_robust_watchlist | PA_BUY_SELL_CLOSE_TREND_003 | pa_buy_sell_close_trend | pa | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/PA_BUY_SELL_CLOSE_TREND_003.yaml | all nominal robust-positive (documentation only) | contains deduped equivalents; not recommended for immediate diagnostic | no | yes |
| extended_robust_watchlist | PA_BUY_SELL_CLOSE_TREND_004 | pa_buy_sell_close_trend | pa | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/PA_BUY_SELL_CLOSE_TREND_004.yaml | all nominal robust-positive (documentation only) | contains deduped equivalents; not recommended for immediate diagnostic | no | yes |
| gap_cci_core | CCI_EXTREME_SNAPBACK_003 | cci_extreme_snapback | indicator | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/CCI_EXTREME_SNAPBACK_003.yaml | pairwise ablation |  | yes | yes |
| gap_cci_core | GAP_ACCEPTANCE_FAILURE_001 | gap_acceptance_failure | opening_trap | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/GAP_ACCEPTANCE_FAILURE_001.yaml | pairwise ablation |  | yes | yes |
| pa_cci_core | CCI_EXTREME_SNAPBACK_003 | cci_extreme_snapback | indicator | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/CCI_EXTREME_SNAPBACK_003.yaml | pairwise ablation |  | yes | yes |
| pa_cci_core | PA_BUY_SELL_CLOSE_TREND_003 | pa_buy_sell_close_trend | pa | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/PA_BUY_SELL_CLOSE_TREND_003.yaml | pairwise ablation |  | yes | yes |
| pa_gap_core | GAP_ACCEPTANCE_FAILURE_001 | gap_acceptance_failure | opening_trap | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/GAP_ACCEPTANCE_FAILURE_001.yaml | pairwise ablation |  | yes | yes |
| pa_gap_core | PA_BUY_SELL_CLOSE_TREND_003 | pa_buy_sell_close_trend | pa | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/PA_BUY_SELL_CLOSE_TREND_003.yaml | pairwise ablation |  | yes | yes |
| pa_only_core | PA_BUY_SELL_CLOSE_TREND_003 | pa_buy_sell_close_trend | pa | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/PA_BUY_SELL_CLOSE_TREND_003.yaml | single-family ablation | optionally add PA_004 in a separate set | yes | yes |
| primary_representative_core | CCI_EXTREME_SNAPBACK_003 | cci_extreme_snapback | indicator | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/CCI_EXTREME_SNAPBACK_003.yaml | minimum redundancy; maximum interpretability | GAP deduped (001–004 identical); PA 001–003 trade-identical (use 003) | yes | yes |
| primary_representative_core | GAP_ACCEPTANCE_FAILURE_001 | gap_acceptance_failure | opening_trap | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/GAP_ACCEPTANCE_FAILURE_001.yaml | minimum redundancy; maximum interpretability | GAP deduped (001–004 identical); PA 001–003 trade-identical (use 003) | yes | yes |
| primary_representative_core | PA_BUY_SELL_CLOSE_TREND_003 | pa_buy_sell_close_trend | pa | member | src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/PA_BUY_SELL_CLOSE_TREND_003.yaml | minimum redundancy; maximum interpretability | GAP deduped (001–004 identical); PA 001–003 trade-identical (use 003) | yes | yes |


## 7. Future Layer2 diagnostic design (NOT RUN here)

- Candidate-set axis (design buckets): primary vs balanced vs ablations (PA-only, GAP-only, CCI-only, pairwise mixes).
- Risk control axis (design only): `max_trades_per_day` ∈ {1, 2}; `daily_max_loss_r` ∈ {−1.5, −2.0}; `priority_policy` ∈ {metadata_priority, score_adjusted_priority}.
- No router; no broad grid.

## 8. Interpretation

- Singleton OOW robustness does **not** guarantee combination robustness.
- This is a design transition from broad l2_core to a deduped robust pocket for diagnostics.

## 9. Recommended next step

**`RUN_SMALL_ROBUST_CORE_LAYER2_DIAGNOSTIC_DESIGN`** (produce runnable configs in a follow-up task; do not execute here).
