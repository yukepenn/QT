# router_quality_refinement_v2_decision

## Decision label (exactly one)

**`RUN_EXIT_OVERLAY_DIAGNOSTICS`**

## Rationale (3–6 bullets)

- Router v2 shows **actionable-but-narrow** improvements (e.g., `late_climax_guard` improves PF with **~80–90%** retention on several profiles), but **total R tradeoffs** remain material for **`primary_mtp2_meta`** and some combined masks still look like **implicit curve-fit** without a held-out discipline.
- Quality v2 demonstrates that **fixed A/B thresholds remain too sparse/over-filtering**, while **percentile / bottom-cut** schemes can reach **~80% retention** with PF / maxDD proxy improvements — but these thresholds are explicitly **`IN_SAMPLE_DIAGNOSTIC`** on the same panel.
- Exit readiness aggregates already prioritize **`trend_swing`** and **`runner`** over **`scalp`** under the v1 heuristic preview — this is a **higher expected information gain** next step than further score tinkering alone.
- Champion v0 remains **frozen**; the next increment should add **simulation harnessing** (exit overlays) **without** combiner wiring or strategy/YAML edits.

## Recommended next step (exactly one)

Run an **offline exit-overlay diagnostic harness** starting with **`trend_swing`**, then **`runner`**, producing **aggregate-only** tables comparable to router/quality outputs.

## Explicit non-runs

- No WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global Layer1 reruns.
- No production router wiring; no short/scalp strategy implementations; no selected-candidate YAML edits; no signal semantics edits.
- No committing row-level `trade_context_panel.csv` or `local_rows/**`.
