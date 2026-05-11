# Layer3 fixed-profile smoke optional v1 — baseline inventory

- **git_tip (at postprocess):** `770f050 Docs(progress): record layer3 smoke push SHAs`
- **git_branch:** `main`
- **sync vs origin (at postprocess):** upstream: commits behind origin=0, ahead of origin=0
- **design decision (from `layer3_fixed_profile_smoke_design_decision.md`):** RUN_LAYER3_FIXED_PROFILE_SMOKE
- **CORE smoke recap:** `pa_only_mtp1_meta` / `pa_gap_mtp2_meta` completed under `layer3_fixed_profile_smoke_v1/` (decision was `RUN_OPTIONAL_LAYER3_BASELINE_ABLATION`).
- **Optional profiles executed:** `primary_mtp2_meta`, `pa_gap_mtp1_meta`, `pa_only_mtp2_meta`
- **Not expanded beyond these three** (no VWAP, no PA_004/CCI_002 balanced profiles, no side-flip).
- **windows:** `early_oow`, `insample_ref`, `late_oow`, `full_available`
- **expected run count:** 12 (3 × 4)
- **discovered runs (metrics.json):** 12
- **local raw run root (do not commit):** `src/research/results/layer3_fixed_profile_smoke_optional_v1/local_runs/**`
- **local configs (do not commit):** `src/research/results/layer3_fixed_profile_smoke_optional_v1/local_configs/**`
- **CORE artifacts present:** read from `layer3_fixed_profile_smoke_v1/profile_window_summary.csv` (parseable).
- **missing curated files:** none required by postprocess (if postprocess completed)

## Smoke outcome

- **decision:** `OPTIONAL_SMOKE_BATCH_COMPLETE`
