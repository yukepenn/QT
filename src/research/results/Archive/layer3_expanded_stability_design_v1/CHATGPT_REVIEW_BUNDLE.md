# CHATGPT_REVIEW_BUNDLE — layer3_expanded_stability_design_v1

## 1. Current project state

- **Branch:** `main` (research-only QT).
- **Layer3 complete smoke** exists under `src/research/results/layer3_fixed_profile_smoke_complete_v1/` with decision **`PROCEED_TO_LAYER3_EXPANDED_STABILITY_DESIGN`** (superseded operationally by this design’s follow-on **`RUN_LAYER3_EXPANDED_STABILITY`**).
- **This folder** (`layer3_expanded_stability_design_v1/`) is **design-only** — no expanded stability execution, no WFO, no live/SPY, no strategy/feature/YAML changes.

## 2. Complete Layer3 smoke recap (full_available headline)

| profile_id | total_r (approx) | max_dd_r (approx) | rollup label |
|------------|-----------------:|------------------:|----------------|
| `primary_mtp2_meta` | 135.89 | −25.09 | OPTIONAL_BASELINE_PASS_WITH_WARNINGS |
| `pa_gap_mtp2_meta` | 131.99 | −21.27 | LAYER3_SMOKE_PASS_WITH_WARNINGS |
| `pa_gap_mtp1_meta` | 117.40 | −22.34 | LAYER3_SMOKE_PASS_WITH_WARNINGS |
| `pa_only_mtp1_meta` | 104.59 | −17.71 | LAYER3_SMOKE_PASS_WITH_WARNINGS |
| `pa_only_mtp2_meta` | 104.59 | −17.71 | LAYER3_SMOKE_PASS_WITH_WARNINGS |

**late_oow total_r (approx):** `pa_only_mtp1` **21.49** > `pa_gap_mtp2` **18.77** > `primary` **11.86**.

## 3. Recommended profile roles (expanded stability)

| Role | profile_id |
|------|--------------|
| CLEAN_BASELINE | `pa_only_mtp1_meta` |
| DEFAULT_COMBINED | `pa_gap_mtp2_meta` |
| BREADTH_BASELINE (reference) | `primary_mtp2_meta` |
| ABLATION (reference) | `pa_gap_mtp1_meta`, `pa_only_mtp2_meta` |

## 4. Why 2025Q1 / 2022Q4 need data-derived diagnosis

- `complete_risk_flags.csv` flags **`R_2025Q1`** and **`R_2022Q4`** as **WARNING** pockets with **profile-specific total_r** — these are **hypothesis anchors**, not semantic market labels.
- **Forbidden:** naming them a priori as “global down” or “chop”.
- **Required:** compute QQQ return/vol/trend-efficiency/range proxies **inside each slice**, then compare profile PnL, exit mix, and candidate contribution **in the same slice**.

## 5. Weak-period diagnostic design

- See **`weak_period_diagnostic_design.md`** + **`weak_period_diagnostic_design.csv`** for diagnostic groups, inputs, planned outputs (`weak_period_context.csv`, `weak_period_profile_pnl.csv`, etc.), and `pass_fail_use` notes.
- Additional **data-driven** weak quarter example: **`primary_mtp2_meta` 2023Q3** (negative in `complete_quarterly_summary.csv`) — candidate for slice list, not a named regime.

## 6. Market context label design

- Labels: `uptrend_low_vol`, `uptrend_high_vol`, `downtrend_low_vol`, `downtrend_high_vol`, `range_chop`, `high_gap_environment`, `late_trend_climax_like`, `unknown_mixed`.
- See **`market_context_label_design.md`** + **`.csv`** — thresholds versioned at execution time; fallbacks if inputs missing.

## 7. Expanded stability gates

- Window positivity (hard for defaults); monthly/quarterly (mostly warning); drawdown; cost (**target-limit stress** hard for defaults); exit mechanics; contribution; market-context; artifact gates.
- See **`expanded_stability_gate_design.md`** + **`.csv`**.

## 8. Future run plan

- Future root: **`src/research/results/layer3_expanded_stability_v1/`**.
- Phases A–J: **`expanded_stability_run_plan.md`** + **`.csv`** — prefer **reuse** of `complete_monthly_summary.csv` / `complete_quarterly_summary.csv` before any combiner re-run.

## 9. Expected outputs

- **`expanded_stability_expected_outputs.md`** + **`.csv`** — includes mandatory **`CHATGPT_REVIEW_BUNDLE.md`** and **`SOURCE_MAP.csv`** for the execution root.

## 10. Risk register

- **`expanded_stability_risk_register.md`** + **`.csv`** — maps 2025Q1/2022Q4, max_hold, stops, PA concentration, GAP late_oow, primary/CCI margin, no SPY/WFO/live, misclassification, overlap caveat.

## 11. Decision

**`RUN_LAYER3_EXPANDED_STABILITY`** — **`layer3_expanded_stability_design_decision.md`**.

## 12. Explicit non-runs

- No expanded stability **execution** in this commit; no mini/full WFO; no live/paper; no SPY; no broad Layer2; no Global Layer1; no strategy/feature/YAML/router/short-support changes; no raw trades or `local_runs` committed.

## 13. Recommended next step

**Single next step:** implement and run **`RUN_LAYER3_EXPANDED_STABILITY`** per the run plan, writing curated outputs under **`layer3_expanded_stability_v1/`** (and keeping any trade tape **local-only**).
