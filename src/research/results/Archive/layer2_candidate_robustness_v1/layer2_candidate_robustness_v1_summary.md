# Layer2 candidate robustness v1 — summary (full l2_core)

## 1. Purpose

Quantify whether **l2_core** singleton Layer2 combiner candidates survive **two OOW windows** plus an **insample reference** window under a **fixed research envelope** (default `layer2_fixed_vwap_mtp2.yaml`), without tuning parameters on OOW.

## 2. Prior fixed-profile OOW failure

Earlier **fixed_profile_oow_v1** work showed **weak** aggregate profiles on OOW for VWAP/indicator stacks. This audit asks whether **individual** YAMLs are broken vs only **combinations**.

## 3. Full candidate root audited

`src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates/` — **66** YAMLs.

## 4. Audit coverage

**66 / 66** candidates × **3** windows = **198** `candidate_oow_metrics.csv` rows, all **`status=OK`**. Raw runs: `local_runs/**` (**not** committed).

## 5. Candidate-level OOW results

| robustness_label | count |
|------------------|------:|
| OOW_MIXED | 40 |
| ROBUST_POSITIVE | 10 |
| INSAMPLE_ONLY | 8 |
| ANTI_PREDICTIVE_CANDIDATE | 5 |
| OOW_NEGATIVE | 3 |

See `candidate_robustness_labels.csv`, `full_candidate_oow_interpretation.md`, and highlight CSVs (`top_robust_candidates.csv`, `worst_oow_candidates.csv`, …).

## 6. Strategy-level results

See `strategy_oow_summary.csv` — strongest robust counts on **`gap_acceptance_failure`**, **`pa_buy_sell_close_trend`**, **`cci_extreme_snapback`**.

## 7. Family-level results

See `family_oow_summary.csv` and `full_family_oow_interpretation.md`.

## 8. VWAP candidate analysis

**Zero** robust-positive; **three** reclaim/reject **`INSAMPLE_ONLY`**; remainder **`OOW_MIXED`**.

## 9. Indicator candidate analysis

Only **CCI** **002**–**003** robust; **MACD/RSI/Stoch/Supertrend** mostly mixed or insample-only; **five** total **`ANTI_PREDICTIVE_CANDIDATE`** including **all** **`MULTI_DAY_LEVEL_TRAP_*`**.

## 10. Opening / trap candidate analysis

**Gap acceptance failure** **001**–**004** robust (**identical** metrics in this audit). **Failed ORB** mixed. **Multi-day level trap** anti-predictive cluster.

## 11. PA candidate analysis

**Buy/sell close trend** robust **001**–**004**. **Failed range breakout trap** and **trading range BLS/HS** mostly weak (including **`OOW_NEGATIVE`** on **001**–**003**). **Climax reversal** mixed.

## 12. Afternoon / other candidate analysis

**Afternoon continuation:** all mixed. **ORB continuation / prior close reclaim:** all mixed.

## 13. High-turnover / anti-predictive analysis

No **`HIGH_TURNOVER_FRAGILE`** labels. **`ANTI_PREDICTIVE_CANDIDATE`:** **5** (see `anti_predictive_candidates.csv`).

## 14. Side-flip status

Non-executable **−R** proxy only; **does not** support inverse production. See `side_flip/side_flip_interpretation.md` and `future_side_flip_watchlist.csv`.

## 15. Robust l2_core policy v2

Counts in `l2_core_policy_v2_action_summary.csv` / `l2_core_policy_v2_candidate_actions.csv`. **KEEP_CORE:** **10**.

## 16. Whether robust core can be formed

**Yes** — gated dry-run: `robust_core_dry_run/selected_candidates_manifest.csv` (**10** candidates, **3** families). **Caveat:** treat **GAP** **001**–**004** as **one** effective signal for diversity.

## 17. Decision

**`CREATE_ROBUST_L2_CORE_V2_DESIGN`** — see `layer2_candidate_robustness_decision.md`.

## 18. Explicit non-runs

mini-WFO; full WFO; live/paper; SPY; Global L1 rerun; broad Global L2 grid; strategy / feature / selected-candidate YAML edits; `regime_router`; hard regime filters; production short support; OOW parameter tuning; heavy artifact commits.

## 19. Recommended next step

Produce **`robust l2_core v2` design doc** from dry-run manifest + dedupe rules (documentation only in the same research lane).
