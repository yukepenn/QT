# exit_overlay_diagnostics_decision

## Decision label (exactly one)

**`RUN_EXIT_OVERLAY_DIAGNOSTICS_V2`**

## Rationale

- `fixed_target_replay` vs panel `r_multiple` mean abs diff up to **0.379** R — reconcile entry bar / intrabar model before trusting overlay deltas.
- Automated label scan over profile×window×overlay rows (N=120).
- Champion v0 entries frozen; simulation uses local panel + QQQ 1m bars only.
- Intrabar ambiguity default `stop_first`; optimistic paths not used for headline metrics.
- Router/quality v2 remains complementary — masks vs exit paths are different controls.
- No production combiner wiring in this commit.

## Recommended next step (exactly one)

Refine overlay rules (ambiguity sensitivity, context eligibility, runner trail parameters) and rerun this harness.

## Explicit non-runs

- No WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global Layer1.
- No production router or exit-management in combiner.
- No strategy / feature / selected-candidate YAML edits.
- No short or scalp strategy code.
- Row-level outputs remain local-only.
