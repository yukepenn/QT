# Trade Quality Router v1.5 — summary

## 1. Purpose

Extend **Trade Quality Router v1** with **v1.5 diagnostics** on QQQ 2023–2024 enriched combiner trades: decompose **`regime_unknown`**, **calendar holdouts** for VWAP offline quality score, **VWAP trade #2** stability, **indicator `max_trades_per_day` 2 and 3** replays, **target-limit-aware exit/slip attribution** (overlay only), and a **revised offline score** — without changing strategies, features, combiner routing, or simulator PnL.

## 2. What v1 found (recap)

- **VWAP:** `late_trend_climax` dominates count; **`regime_unknown`** and **`trading_range`** remain important **positive** R contributors; **trade #2** positive in aggregate; **offline top80% score** improved full-sample VWAP metrics vs all trades.
- **Indicator (mtp=1):** Similar regime mix; **offline VWAP-style score did not help** (top slices worse than all).
- **Exits:** Large R from **targets** vs drains from **stops**; combiner uses **symmetric per-share slip** on all exits.

## 3. What v1.5 added

| Deliverable | Location |
|-------------|-----------|
| Baseline inventory | `baseline_inventory.md` |
| Unknown decomposition | `unknown_regime/` |
| VWAP holdout + trade#2 | `holdout/` |
| Exit/slip overlay | `exit_slip/` |
| Indicator mtp 2/3 tables | `indicator_mtp_diagnostics/` |
| Offline score v1.5 | `quality_score_v15/` |
| Router readiness | `router_readiness_decision_v15.md` |
| This summary | `trade_quality_router_v1_5_summary.md` |
| Compact table | `trade_quality_router_v1_5_key_findings.csv` |

**Scripts:** `decompose_regime_unknown.py`, `validate_trade_quality_holdout.py`, `analyze_exit_slip_attribution.py`, `build_indicator_mtp_diagnostics.py`, `score_trade_quality_v15.py`, `trade_quality_unknown.py`.

## 4. Unknown regime decomposition

- **Systems:** `vwap_baseline_global_l2`, `vwap_lower_turnover`, `indicator_completion_mtp1`.
- **Finding:** Unknown is **not** “only first 30 minutes” for VWAP baseline in this sample — **`m61_120`** and **`m121_240`** minute buckets carry large shares of unknown trades and unknown PnL (see `vwap_baseline_global_l2_unknown_by_minute_bucket.csv`). Indicator unknown shows a similar **mid-morning** concentration pattern in its CSVs.
- **Implication:** Treat **`regime_unknown` as neutral** in a router until labels or windowing improve; optional **sub-bucket** bonuses need holdout support (not yet present).

## 5. VWAP calendar holdout

- **Method:** Train quantile thresholds on **train** `trade_quality_score` only; apply to **test** (`validate_trade_quality_holdout.py`).
- **2023 → 2024:** Test **all** ≈ **14.37R** / 173 trades vs test **top80 train thr** ≈ **9.59R** / 167 trades — **score filter hurts** on this split (`vwap_quality_holdout_results.csv`).
- **Other splits:** H1→H2 months and odd→even months show **mixed** results; Q1+Q3 train vs Q2+Q4 test is **weak** for top80.
- **Conclusion:** VWAP offline **top80 is not robust** under simple calendar splits in this diagnostic.

## 6. VWAP trade #2 stability

- **43** trades; **~+5.50R** total; **2023 ~+1.45R**, **2024 ~+4.05R** (`vwap_trade_number_stability.md`, `vwap_trade_number_by_year_t2.csv`).
- **Not** single-year-only; monthly counts remain small — interpret month tables cautiously.

## 7. Indicator mtp=2/3 diagnostics

| mtp | trades | total R | avg R | trade2 total R (n) | trade3 total R (n) |
|-----|--------|---------|-------|---------------------|---------------------|
| 1 | 502 | 43.55 | 0.087 | — | — |
| 2 | 1000 | 72.12 | 0.072 | +28.58 (498) | — |
| 3 | 1241 | 79.48 | 0.064 | +28.58 (498) | +7.35 (241) |

- **Trade #2** adds meaningful **positive** R but **dilutes avg R** vs mtp=1.
- **Trade #3** is **positive** but **low avg R** and longer holds (see `indicator_mtp3_trade_number_summary.csv` `avg_bars_held`).
- **Family repeat / prior outcome:** see `indicator_mtp2_by_family_repeat.csv` / `indicator_mtp3_by_family_repeat.csv` and prior-outcome CSVs.

## 8. Target-limit-aware exit/slip attribution

- **Documented:** symmetric `slippage_per_share` on entry and exit in the combiner simulator.
- **Overlay:** `target_limit_stress` vs `symmetric_stress` shows **material recovery** on systems with many target exits; VWAP and indicator both remain **net positive** under the documented scenarios in `exit_slip_scenario_comparison.csv`.
- **Not** a simulator change — **do not** merge into Global L2 published numbers without productizing exit-type slip.

## 9. Revised offline quality score (v1.5)

- **`regime_unknown`:** neutral vs v1 regime table bonuses/penalties; optional small **early-unknown** minute bonus (hypothesis).
- **Indicator repeat penalty:** gated off when mtp evidence shows trade #2 **not** negative (here trade #2 is **positive**, so penalty **not** applied).
- **Holdout:** `vwap_threshold_holdout_v15.csv` — **2023→2024 test top80** still **underperforms** test all on total R in this run.

## 10. Evidence for/against mtp=3/5

- **mtp=3:** adds **~+7.35R** on trade #3 with **lower avg R** than trade #1; **no** case for production mtp=5 from this evidence.
- **mtp=2:** raises total R but **cuts avg R**; “useful vs overtrading” **unsettled** without cost-turnover integration.

## 11. Evidence for/against optional router (score adjustment)

- **Against (now):** VWAP score **fails** primary **year holdout**; indicator offline score remains **weak** at mtp=1 (`indicator_threshold_diagnostics_v15.csv` top80 worse than all); unknown decomposition **incomplete** for confident penalties/bonuses.
- **For (later):** Target-limit overlay suggests **economic stories are slip-sensitive** in a way the current simulator exaggerates for targets — a **future** router could use **labels** derived post-trade until entry-time features exist.

## 12. Decision

**`NEED_MORE_TRADE_ENRICHMENT`** — see `router_readiness_decision_v15.md`.

## 13. Explicit non-runs

mini-WFO; full WFO; live/paper; SPY; Global L1 rerun; large Global L2 grids; strategy changes; feature primitive changes; selected candidate YAML edits; hard regime filters; combiner `regime_router` implementation; heavy artifact commits; `git add .`.

## 14. Recommended next step

**Exactly one:** **`NEED_MORE_TRADE_ENRICHMENT`** — extend scored rows / splits (or additional years locally) until **VWAP** offline score shows **stable** test improvement under at least one **train→test** calendar design **and** indicator behavior at production `mtp` is decided with cost-turnover context.
