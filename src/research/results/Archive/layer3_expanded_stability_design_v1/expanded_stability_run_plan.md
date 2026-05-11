# Expanded stability run plan (design only — not executed)

## Future output root

`src/research/results/layer3_expanded_stability_v1/` (**create only when executing** expanded stability).

## Profiles

- **Required:** `pa_only_mtp1_meta`, `pa_gap_mtp2_meta`
- **Reference:** `primary_mtp2_meta`
- **Optional reference:** `pa_gap_mtp1_meta`, `pa_only_mtp2_meta`

## Windows and decomposition

- Windows: `early_oow`, `insample_ref`, `late_oow`, `full_available` (align with Layer3 smoke).
- Decomposition: monthly, quarterly, yearly; explicit **weak-period** slices from data-driven list.

## New trading runs?

| Situation | Action |
|-----------|--------|
| Monthly/quarterly CSVs from `layer3_fixed_profile_smoke_complete_v1/` suffice for Phase A–B | **No** combiner re-run |
| Exit mix / candidate slice / cost-by-period needs trade-level rows | **Yes** — local detailed replay under `layer3_expanded_stability_v1/local_runs/**` (**not committed**) |

## Machine-readable plan

See **`expanded_stability_run_plan.csv`**.
