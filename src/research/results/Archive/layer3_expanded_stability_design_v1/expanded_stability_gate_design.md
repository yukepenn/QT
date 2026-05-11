# Expanded stability gate design (v1)

## Philosophy

- **Hard** gates: window positivity for default candidates; cost **target-limit stress** positivity on `full_available` for **PA-only** and **PA+GAP**; PA contribution positive where combined; curated artifact presence.
- **Warning** gates: monthly/quarterly pockets, drawdown tiers, exit-mix concentration, market-context interpretability, optional **primary** profile economics.
- **Failure actions** map to labels: `EXPANDED_STABILITY_READY`, `EXPANDED_STABILITY_READY_WITH_WARNINGS`, `NEED_WEAK_PERIOD_DIAGNOSTICS`, `REFINE_COMBINATION_RULES`, `FAIL_EXPANDED_STABILITY`, `HOLD_BEFORE_STABILITY`.

## Special review quarters

- Any calendar quarter appearing in **`complete_risk_flags.csv`** as `R_2025Q1` / `R_2022Q4` (or additional worst quarters from data) must receive a **`weak_period_interpretation.md`** subsection with: context metrics, profile PnL, exit mix, candidate contribution, and classification (**market-context** vs **profile-specific** vs **normal drawdown**).
- **Do not** name the quarter as “global down” or “chop” in the gate CSV — only require **documentation** after metrics.

## Full gate table

See **`expanded_stability_gate_design.csv`**.
