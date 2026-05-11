# CHATGPT_REVIEW_BUNDLE — local_detailed_trade_context_replay_v1

## 1) Git / validation

- Baseline validations: `compileall` OK, `pytest` OK, loader **35** strategies (see repo `NEXT_HANDOFF.md` for the baseline snapshot).

## 2) Why this task was needed

- Prior cycle aggregates lacked row-level trade timestamps/IDs and decision-time market context fields, preventing no-lookahead router/quality attribution.

## 3) Champion v0 freeze recap

- `pa_only_mtp1_meta` (PA only) — CLEAN_BASELINE
- `pa_gap_mtp2_meta` (PA + GAP) — DEFAULT_COMBINED
- `primary_mtp2_meta` (PA + GAP + CCI) — BREADTH_REFERENCE_ONLY

## 4) Local row-level replay coverage

- Local-only row panel built: **10,628** trades
- Window coverage: early/insample/late/full for all 3 profiles
- Local-only paths (not committed): `local_runs/**`, `local_rows/**`

## 5) Context join coverage (no lookahead)

- Decision timestamp source: `signal_ts_utc` (signal bar; entry occurs next-bar open)
- Join method: backward `merge_asof` from `decision_context_ts_utc` to feature `ts_utc`
- Coverage: see `aggregates/trade_context_coverage.csv`

## 6) PA-only / PA+GAP / primary context findings (aggregate slices)

- Regime/context buckets and market-context label slices are available under `aggregates/`.
- Key takeaway: monthly `market_context_label` breakdown shows dispersion in total_r across uptrend/downtrend/range_chop.

## 7) Router diagnostic results (offline only)

- Results: `router_diagnostics_v1/router_filter_results.csv`
- Summary: `router_diagnostics_v1/router_diagnostics_summary.md`
- Note: `max_dd_r_proxy` is a cumulative-R proxy, not a capital-constrained equity reconstruction.

## 8) Trade-quality score v2 results (offline only; proxy components)

- Bucket distribution: `quality_score_v2/quality_bucket_distribution.csv`
- Group results: `quality_score_v2/quality_group_results.csv`
- Current proxy scoring yields **very sparse A-only**; A+B retains ~28% of trades with reduced worst-quarter drawdown vs baseline, but with large total-R reduction.

## 9) PA/GAP/CCI attribution (observed, non-counterfactual)

- Overall and sliced attribution under `attribution_v1/`.
- Attribution is **observed** realized PnL by candidate; it does not infer counterfactual “would-have-traded” outcomes under conflicts.

## 10) Trade number / freshness results

- Tables under `freshness_v1/` for trade # and prior-loss / repeat flags.

## 11) Exit overlay readiness (feasibility only)

- Heuristic exit-mode preview under `exit_overlay_readiness_v1/` (no exit simulation).

## 12) Scalp / short roadmap update

- Lightweight evidence summaries under `roadmap_update_v1/` (no new strategy implementation).

## 13) Decision

- See `local_trade_context_replay_decision.md`

## 14) Explicit non-runs

- No WFO / mini-WFO / live / paper
- No SPY / broad Layer2 / Global Layer1 rerun
- No strategy/feature/YAML/combiner semantics changes
- No production router wiring
- No row-level artifacts committed

## 15) Recommended next step

- Refine offline router filters + quality score component definitions using the available decision-time features, then rerun aggregate-only diagnostics.

