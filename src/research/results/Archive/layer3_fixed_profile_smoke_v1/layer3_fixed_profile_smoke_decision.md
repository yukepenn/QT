# Layer3 fixed-profile smoke v1 — decision (CORE only)

**Decision (exactly one):** **`RUN_OPTIONAL_LAYER3_BASELINE_ABLATION`**

## Rationale

- Both CORE profiles passed smoke gates (warnings acceptable).
- Next step: add optional baseline/ablation profiles for breadth and mtp checks.

## Profile-level labels

- `pa_gap_mtp2_meta`: **LAYER3_CORE_SMOKE_PASS_WITH_WARNINGS**
- `pa_only_mtp1_meta`: **LAYER3_CORE_SMOKE_PASS_WITH_WARNINGS**

## Recommended next step (exactly one)

Run optional Layer3 baseline/ablation (`primary_mtp2_meta`, `pa_gap_mtp1_meta`, `pa_only_mtp2_meta`) in a follow-on task.

## Explicit non-runs

- No optional profiles in this CORE task
- No broad Layer2, WFO, live/paper, SPY, router
- No strategy/feature/YAML edits

- git_tip: 7063b68 Research(layer3): design fixed smoke v1