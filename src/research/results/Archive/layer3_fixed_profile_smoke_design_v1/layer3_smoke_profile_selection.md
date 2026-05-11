# Layer3 fixed-profile smoke v1 — profile selection (DESIGN ONLY — NOT RUN)

This selects which fixed robust profiles should be included in a Layer3 smoke run.

## Default smoke set (required)

- `pa_only_mtp1_meta` (**CLEAN_BASELINE**) — PA-only, simplest baseline.
- `pa_gap_mtp2_meta` (**PRIMARY_COMBINED**) — PA+GAP, best combined candidate.

## Optional profiles

- `primary_mtp2_meta` (**BREADTH_BASELINE**) — PA+GAP+CCI interpretability baseline (late OOW weaker; DD higher).
- `pa_gap_mtp1_meta` (**ABLATION_MTP1**) — mtp sensitivity for PA+GAP.
- `pa_only_mtp2_meta` (**ABLATION_MTP2**) — expected identical to PA-only mtp1 (mtp not binding).

Source-of-truth CSV: `layer3_smoke_profile_selection.csv`.

