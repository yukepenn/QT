# Layer3 fixed-profile smoke v1 — run plan (DESIGN ONLY — NOT RUN)

## Goal

Run a minimal smoke to verify stability and failure modes for the best fixed robust profiles identified in fixed-profile OOW v1.

## Default (core) plan

- **Profiles:** `pa_only_mtp1_meta`, `pa_gap_mtp2_meta`
- **Windows:** `early_oow`, `insample_ref`, `late_oow`, `full_available`
- **Core run count:** 2 profiles × 4 windows = **8**

## Optional expansions

- Optional baseline: `primary_mtp2_meta` → +4 runs (total 12)
- Optional ablations: `pa_gap_mtp1_meta`, `pa_only_mtp2_meta` → +8 runs (total 20)

## Fixed settings (must remain fixed)

- `commission = 0`
- `slippage = 0.01`
- `no_new_after_minute = 360`
- `max_open_positions = 1`
- no router
- no short side
- no signal cache unless explicitly proven safe (default **off**)

## Required period slices (reporting)

For each profile+window, postprocess must include:

- yearly aggregates
- quarterly aggregates (explicitly flag `2022Q4` and `2025Q1`)
- monthly aggregates

Source-of-truth CSV: `layer3_smoke_run_plan.csv`.

