# Layer3 expanded stability design v1 — decision

**Decision (exactly one):** **`RUN_LAYER3_EXPANDED_STABILITY`**

## Rationale

- Profile roles are explicit in **`expanded_stability_profile_selection.csv`** (required vs reference vs ablation).
- Weak-period analysis is **operationally defined** in **`weak_period_diagnostic_design.*`** with **data-derived** context labels (**no** hard-coded “2025Q1 = down market” semantics).
- Market context vocabulary is fixed in **`market_context_label_design.*`** with fallbacks and misclassification notes.
- Gate taxonomy covers windows, monthly/quarterly, drawdown, cost, exits, contribution, market context, and artifacts in **`expanded_stability_gate_design.*`**.
- Future outputs and derivation paths are listed in **`expanded_stability_expected_outputs.*`** and phased in **`expanded_stability_run_plan.*`**.
- Risks from complete smoke are mapped to diagnostics in **`expanded_stability_risk_register.*`**.

## Recommended next step (exactly one)

Execute **`RUN_LAYER3_EXPANDED_STABILITY`** — implement the phased plan under `src/research/results/layer3_expanded_stability_v1/` (reuse monthly/quarterly where possible; add QQQ context + weak-period slices; optional detailed trade replay **local-only**).

## Explicit non-runs (this design commit)

- No expanded stability execution, no WFO / mini-WFO, no live/paper, no SPY, no broad Layer2, no Global Layer1 re-run.
- No strategy plugins, feature primitives, selected-candidate YAML edits, router, or production short support.
- No raw `trades.csv`, `local_runs/`, caches, or heavy combiner artifacts committed.
