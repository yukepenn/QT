# Robust l2_core v2 diagnostic v1 — baseline inventory

- **git tip:** `09c40d7 Docs(handoff): update robust v2 cleanup`
- **handoff decision:** `RUN_SMALL_ROBUST_CORE_LAYER2_DIAGNOSTIC_DESIGN`

## Inputs

- **design_root:** `D:/OneDrive - Washington University in St. Louis/QT/src/research/results/robust_l2_core_v2_design`
- design files:
  - `candidate_sets_design.csv`
  - `representative_candidate_manifest.csv`
  - `core_watchlist_drop_actions.csv`
  - `design_artifact_validation.csv`

- **artifact validation status:** `OK`

## Planned scope

- **windows:** `insample_ref,early_oow,late_oow`
- **candidate_sets:** `primary_representative_core,balanced_representative_core,pa_gap_core,pa_cci_core,gap_cci_core,pa_only_core,cci_only_core`

## Planned grid

- **max_trades_per_day:** `[1, 2]`
- **daily_max_loss_r:** `[-1.5, -2.0]`
- **priority_policy:** `['metadata_priority', 'score_adjusted_priority']`

## Output layout (local-only raw runs)

- raw runs: `D:/OneDrive - Washington University in St. Louis/QT/src/research/results/robust_l2_core_v2_diagnostic_v1/local_runs/<candidate_set>/<window>/<grid_id>/run_*`
- materialized configs: `D:/OneDrive - Washington University in St. Louis/QT/src/research/results/robust_l2_core_v2_diagnostic_v1/local_configs`

## Explicit non-runs

- No broad Layer2 sweep
- No mini/full WFO
- No live/paper
- No SPY
- No strategy changes / feature changes
- No candidate YAML edits
- No signal cache
