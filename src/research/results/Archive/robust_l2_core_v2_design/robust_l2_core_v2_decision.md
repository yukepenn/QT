# Robust l2_core v2 — decision (design-only)

## Decision label (exactly one)

**`RUN_SMALL_ROBUST_CORE_LAYER2_DIAGNOSTIC_DESIGN`**

## Rationale (3–6 bullets)

- Full singleton audit is complete (66/66; 198/198 OK), enabling a clean design step.
- Metric-identical **GAP 001–004** must be treated as **one** effective signal; design needs dedupe rules before any new diagnostics.
- PA close-trend shows multiple robust positives but needs redundancy caps (metrics-only and/or trade-overlap).
- CCI 003 is the primary oscillator rep (positive both OOW); CCI 002 is secondary/watchlist.
- No broad grid / WFO / router is appropriate before validating a small representative core under Layer2 constraints.

## Explicit non-runs

No Layer2 sweep; no mini/full WFO; no live/paper; no SPY; no Global L1; no broad Global L2 grid; no YAML edits; no OOW tuning; no executable side-flip/short research; no heavy artifact commits.

## Recommended next step (exactly one)

Implement **design-only** runnable combiner config(s) that reference the representative candidate sets, plus a small grid outline, but do **not** execute them in this task.
