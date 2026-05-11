# Layer2 candidate robustness v1 — summary

## 1. Purpose

Quantify **per-candidate** out-of-window behavior for l2_core YAMLs after fixed-profile OOW failure, without tuning parameters on OOW.

## 2. Prior fixed-profile OOW failure

Five fixed profiles × four windows (`fixed_profile_oow_v1`) showed **negative** VWAP OOW, **weak/negative** indicator OOW (mtp1 least bad on late OOW; mtp2 worse early; mtp3 diagnostic/high turnover). Decision: **`REVISIT_LAYER2_CANDIDATE_SELECTION`**.

## 3. Candidate root audited

`src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates` (**66** YAMLs total; **27** audited in this pack).

## 4. Candidate-level OOW results

See `candidate_oow_summary.md` and `candidate_robustness_labels.csv`. Headline counts (audited slice): **2** `ROBUST_POSITIVE`, **7** `INSAMPLE_ONLY`, **17** `OOW_MIXED`, **1** `ANTI_PREDICTIVE_CANDIDATE`, **0** `OOW_NEGATIVE` / `TOO_SPARSE` / `HIGH_TURNOVER_FRAGILE` under current thresholds (all 81 rows `status=OK`).

## 5. Strategy / family-level results

See `family_oow_summary.csv` and `strategy_oow_summary.csv`. VWAP audit-family: **0** robust positives. Indicator audit-family: **2** robust positives.

## 6. VWAP candidate analysis

All eight VWAP-class singletons fail the robust-positive heuristic; reclaim-reject **001–003** are **`INSAMPLE_ONLY`**. Matches fixed-profile VWAP OOW weakness being **candidate-level**, not only combiner weighting.

## 7. Indicator candidate analysis

Two CCI snapback candidates are **`ROBUST_POSITIVE`**; MACD/RSI/supertrend/stochastic mostly mixed or insample-only; **`MACD_MOMENTUM_TURN_003`** anti-predictive under rules.

## 8. High-turnover analysis

No `HIGH_TURNOVER_FRAGILE` labels in this slice; mtp3 combination turnover pathology remains a **profile-level** concern (see fixed-profile pack).

## 9. Side-flip diagnostic

**Non-executable sign proxy only** (`side_flip/side_flip_metrics.csv` + interpretation). **Inverse hypothesis not supported.**

## 10. Robust l2_core policy v2

See `l2_core_policy_v2.md` and `l2_core_policy_v2_candidate_actions.csv`.

## 11. Candidate action table

Derived from `candidate_robustness_labels.csv` (`policy_action` column).

## 12. Whether a robust core can be formed

**No** for a credible dry-run — see `robust_core_not_enough_candidates.md`.

## 13. Decision

**`RUN_MORE_CANDIDATE_OOW_AUDIT`** — `layer2_candidate_robustness_decision.md`.

## 14. Explicit non-runs

mini-WFO; full WFO; live/paper; SPY; Global L1 rerun; broad Global L2 grid; strategy/feature changes; selected YAML edits; `regime_router`; hard regime filters; production short support; OOW parameter optimization; heavy artifact commits; `git add .`

## 15. Recommended next step

Complete singleton audits for **`opening_trap`**, **`pa`**, **`afternoon`**, and **`other`** families on the same three windows, then refresh aggregates (still no OOW tuning).
