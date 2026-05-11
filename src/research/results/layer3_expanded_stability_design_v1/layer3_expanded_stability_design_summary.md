# Layer3 expanded stability design v1 — summary

## 1. Purpose

Design how to run a **Layer3 expanded stability review** for the locked PA/GAP robust-core system, grounded in **`layer3_fixed_profile_smoke_complete_v1/`** evidence, **before** any WFO or paper-readiness work.

## 2. Input complete Layer3 smoke result

- Five profiles reviewed; decision **`PROCEED_TO_LAYER3_EXPANDED_STABILITY_DESIGN`** led to complete smoke; ranking and gates documented under `layer3_fixed_profile_smoke_complete_v1/`.

## 3. Profile roles

- **Default baseline:** `pa_only_mtp1_meta`
- **Default combined:** `pa_gap_mtp2_meta`
- **Breadth reference:** `primary_mtp2_meta` (not default)
- **Ablation reference:** `pa_gap_mtp1_meta`, `pa_only_mtp2_meta`

## 4. Weak-period design

- Start from **`R_2025Q1`**, **`R_2022Q4`**, worst months/quarters from **`complete_*`** tables, and **data-mined** weak quarters (e.g. `primary_mtp2_meta` **2023Q3**).
- Classify slices using **computed** QQQ metrics + profile PnL + exits + contribution — see **`weak_period_diagnostic_design.md`**.

## 5. Market context label design

- Eight-label vocabulary with **`unknown_mixed`** fallback; thresholds to be versioned with the future execution root — see **`market_context_label_design.md`**.

## 6. Gate design

- Hard vs warning split documented in **`expanded_stability_gate_design.csv`**; maps to readiness labels including **`NEED_WEAK_PERIOD_DIAGNOSTICS`** and **`REFINE_COMBINATION_RULES`**.

## 7. Future run plan

- Phases A–J in **`expanded_stability_run_plan.csv`**; prefer **reuse** of complete smoke rollups before any combiner re-run.

## 8. Risk register

- **`expanded_stability_risk_register.csv`** ties each known concern to a diagnostic and a conditional next action.

## 9. Expected outputs

- **`expanded_stability_expected_outputs.csv`** lists committed vs trade-derived artifacts for `layer3_expanded_stability_v1/`.

## 10. Decision

**`RUN_LAYER3_EXPANDED_STABILITY`** — see **`layer3_expanded_stability_design_decision.md`**.

## 11. Explicit non-runs

- No execution in this task; no WFO/live/SPY/broad L2/strategy/feature/YAML/router changes.

## 12. Recommended next step

**Implement and run** expanded stability Phase A–J per **`expanded_stability_run_plan.md`**, producing `layer3_expanded_stability_v1/` with **`CHATGPT_REVIEW_BUNDLE.md`** + **`SOURCE_MAP.csv`**.
