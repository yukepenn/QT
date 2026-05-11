# CHATGPT_REVIEW_BUNDLE — local_detailed_trade_context_replay_v1

## 1. Purpose

Produce a **local-only, decision-time enriched trade panel** for Champion v0 so offline diagnostics can join **backward `merge_asof`** context (no lookahead) and compute **router / quality / attribution / freshness / exit-readiness** aggregates that are safe to commit.

## 2. Champion v0 recap

- `pa_only_mtp1_meta` — **CLEAN_BASELINE** (PA only)
- `pa_gap_mtp2_meta` — **DEFAULT_COMBINED** (PA + GAP)
- `primary_mtp2_meta` — **BREADTH_REFERENCE_ONLY** (PA + GAP + CCI)

## 3. Local row-level coverage

- **10,628** enriched trades in the local-only panel (see `aggregates/trade_context_coverage.csv` for join coverage counts).
- Profiles × windows replayed locally; **row-level outputs are not committed** (`local_rows/**`, `local_runs/**`).

## 4. Context join coverage

- `aggregates/trade_context_coverage.csv` reports **10,628 / 10,628** rows with `signal_ts_utc`, decision regime window 20 labels, and `market_context_label`.
- Join uses **decision bar** timestamps and **backward** as-of merges only.

## 5. PA / GAP / CCI contribution headline

From `attribution_v1/candidate_contribution_overall.csv` (observed realized attribution, not counterfactual conflict outcomes):

- **PA (`PA_BUY_SELL_CLOSE_TREND_003`):** **7,782** trades, **~510.81** total R — dominant driver.
- **GAP (`GAP_ACCEPTANCE_FAILURE_001`):** **1,612** trades, **~166.25** total R — additive but context-sensitive.
- **CCI (`CCI_EXTREME_SNAPBACK_003`):** **1,234** trades, **~67.89** total R — positive but **breadth/reference** scale.

## 6. Router v1 headline

- `router_diagnostics_v1/router_filter_results.csv` shows v1 includes **very aggressive** masks (e.g. `preferred_or_neutral_only` ~**0.187** trade retention) alongside smaller-impact cuts.
- **Interpretation:** v1 demonstrates “filters can move PF / drawdown proxies” but **default combined** needs **softer** v2-style guards.

## 7. Quality v2 headline

- `quality_score_v2/quality_group_results.csv`: **A-only** remains **sparse**; **A+B** improves some risk proxies but with **large total-R reductions** vs “all trades”.
- **Interpretation:** fixed buckets are not sufficient without **recalibration** (percentile / profile-aware schemes) — executed further in `router_quality_refinement_v2/`.

## 8. Freshness / trade #2 headline

- `freshness_v1/trade_number_by_profile.csv`: trade **#1** is higher quality than trade **#2** for `pa_gap_mtp2_meta` (lower avg R on #2).

## 9. Exit overlay readiness headline

- `exit_overlay_readiness_v1/exit_mode_assignment_preview.csv` (heuristic preview only): **`trend_swing`** and **`runner`** show materially higher **avg R** than **`reversal`** / **`scalp`** buckets in this run.

## 10. Decision (v1 formal label)

- `local_trade_context_replay_decision.md` — formal decision was **`REFINE_ROUTER_QUALITY_SCORE`** (superseded by the v2 cycle decision in `router_quality_refinement_v2/router_quality_refinement_v2_decision.md`).

## 11. Explicit non-runs

- No WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global Layer1 reruns.
- No production router wiring; no strategy signal semantics changes; no selected-candidate YAML edits.
- No committing raw trades or row-level `trade_context_panel.csv`.

## 12. Recommended next step (historical v1 text)

- Original v1 bundle recommended refining offline router + quality using the panel fields — **done** in `router_quality_refinement_v2/`; the updated formal recommendation is **`RUN_EXIT_OVERLAY_DIAGNOSTICS`**.
