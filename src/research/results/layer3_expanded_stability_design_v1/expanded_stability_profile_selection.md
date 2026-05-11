# Expanded stability — profile selection (design v1)

## Principles

1. **Required** profiles are the operational pair: **PA-only baseline** + **PA+GAP default combined**.
2. **`primary_mtp2_meta`** stays in scope as **breadth reference** — not a default candidate unless gates explicitly justify it after context labeling.
3. **Ablation profiles** (`pa_gap_mtp1_meta`, `pa_only_mtp2_meta`) are **reference-only** to confirm prior Layer3 smoke conclusions (mtp2 choice; mtp non-binding for PA-only).

## Table

See `expanded_stability_profile_selection.csv` for the full machine-readable table (roles, flags, candidate ids, knobs, evidence, risks).

## Default vs reference

| include_as_default_candidate | Profiles |
|-----------------------------|----------|
| YES | `pa_only_mtp1_meta`, `pa_gap_mtp2_meta` |
| NO (reference / ablation) | `primary_mtp2_meta`, `pa_gap_mtp1_meta`, `pa_only_mtp2_meta` |
