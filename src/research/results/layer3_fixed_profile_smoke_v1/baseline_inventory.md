# Layer3 fixed-profile smoke v1 — baseline inventory

- **git_tip (at postprocess):** `7063b68 Research(layer3): design fixed smoke v1`
- **git_branch:** `main`
- **sync vs origin (at postprocess):** upstream: commits behind origin=0, ahead of origin=0
- **design decision (from `layer3_fixed_profile_smoke_design_decision.md`):** RUN_LAYER3_FIXED_PROFILE_SMOKE
- **NEXT_HANDOFF:** prior tip still described fixed-profile OOW only; updated in this task to Layer3 CORE smoke execution + A–L handoff.
- **CORE profiles executed:** `pa_only_mtp1_meta`, `pa_gap_mtp2_meta`
- **Optional profiles excluded:** `primary_mtp2_meta`, `pa_gap_mtp1_meta`, `pa_only_mtp2_meta`
- **windows:** `early_oow`, `insample_ref`, `late_oow`, `full_available`
- **expected run count:** 8 (2 × 4)
- **discovered runs (metrics.json):** 8
- **local raw run root (do not commit):** `src/research/results/layer3_fixed_profile_smoke_v1/local_runs/**`
- **local configs (do not commit):** `src/research/results/layer3_fixed_profile_smoke_v1/local_configs/**`
- **missing curated files:** none required by postprocess (if postprocess completed)

## Smoke outcome

- **decision:** `RUN_OPTIONAL_LAYER3_BASELINE_ABLATION`
