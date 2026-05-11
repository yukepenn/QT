# Layer3 optional smoke v1 — decision

**Decision (exactly one):** **`OPTIONAL_SMOKE_BATCH_COMPLETE`**

## Rationale

- Optional baseline/ablation profiles executed (12 runs).
- Merged review is produced under `layer3_fixed_profile_smoke_complete_v1/` via `merge-complete`.

## Profile-level labels

- `pa_gap_mtp1_meta`: **LAYER3_SMOKE_PASS_WITH_WARNINGS**
- `pa_only_mtp2_meta`: **LAYER3_SMOKE_PASS_WITH_WARNINGS**
- `primary_mtp2_meta`: **OPTIONAL_BASELINE_PASS_WITH_WARNINGS**

## Recommended next step (exactly one)

Run `python -m src.research.run_layer3_fixed_profile_smoke merge-complete ...` to build `layer3_fixed_profile_smoke_complete_v1/`.

## Explicit non-runs

- No CORE re-runs in this optional batch (use existing `layer3_fixed_profile_smoke_v1/`).
- No broad Layer2, WFO, live/paper, SPY, router
- No strategy/feature/YAML edits

- git_tip: 770f050 Docs(progress): record layer3 smoke push SHAs