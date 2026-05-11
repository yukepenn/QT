# Layer3 complete fixed-profile smoke v1 — decision

**Decision (exactly one):** **`PROCEED_TO_LAYER3_EXPANDED_STABILITY_DESIGN`**

## Rationale

- pa_gap mtp2 ≥ mtp1 on full_available (typical expectation).
- CORE profiles remain the recommended defaults; CCI breadth stays optional.
- No optional profile invalidates locked PA+GAP mtp2 economics on merged gates.
- `primary_mtp2_meta` passes as optional breadth baseline with warnings; late_oow is structurally weaker than PA-only / PA+GAP despite strong full_available R.
- `pa_only_mtp1_meta` vs `pa_only_mtp2_meta` shows ~0 delta across windows in this stack (mtp does not bind for PA-only).

## Profile-level labels

- `pa_gap_mtp1_meta`: **LAYER3_SMOKE_PASS_WITH_WARNINGS**
- `pa_gap_mtp2_meta`: **LAYER3_SMOKE_PASS_WITH_WARNINGS**
- `pa_only_mtp1_meta`: **LAYER3_SMOKE_PASS_WITH_WARNINGS**
- `pa_only_mtp2_meta`: **LAYER3_SMOKE_PASS_WITH_WARNINGS**
- `primary_mtp2_meta`: **OPTIONAL_BASELINE_PASS_WITH_WARNINGS**

## Recommended next step (exactly one)

Design Layer3 expanded stability review (no WFO/live/SPY until design).

## Explicit non-runs

- No broad Layer2 sweep; no mini/full WFO; no live/paper; no SPY; no router
- No strategy/feature/selected-candidate YAML edits

- git_tip: 770f050 Docs(progress): record layer3 smoke push SHAs