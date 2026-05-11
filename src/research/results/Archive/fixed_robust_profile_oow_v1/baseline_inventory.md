# Fixed robust-profile OOW v1 — baseline inventory (2026-05-11)

## Git / decision state

- **git tip:** `fc9b065` (robust-core diagnostic v1 executed)
- **current decision:** `PROCEED_TO_FIXED_ROBUST_PROFILE_OOW_VALIDATION`

## Input evidence (from robust-core diagnostic v1)

- Diagnostic root: `src/research/results/robust_l2_core_v2_diagnostic_v1/`
- Design root: `src/research/results/robust_l2_core_v2_design/`
- Headline best-per-set/window (from `candidate_set_summary.csv`):
  - `pa_only_core`: insample ~37.97R, early ~45.14R, late ~21.49R
  - `pa_gap_core`: insample ~52.27R, early ~60.95R, late ~18.77R
  - `primary_representative_core`: insample ~62.70R, early ~61.33R, late ~11.86R

## Goal of this task

Run a **fixed-profile** (locked knobs + locked candidate IDs) OOW validation without per-window best leakage:

- Profiles: PA-only, PA+GAP, primary core (PA+GAP+CCI), plus PA-only mtp=2 and optional PA+GAP mtp=1.
- Windows: `insample_ref`, `early_oow`, `late_oow`, `full_available`.

## Planned windows (fixed)

- `early_oow`: 2020-01-01 → 2022-12-31
- `insample_ref`: 2023-01-01 → 2024-12-31
- `late_oow`: 2025-01-01 → 2026-04-30
- `full_available`: 2020-01-01 → 2026-04-30

## Planned fixed knobs (hold constant unless explicitly varied)

- `max_open_positions`: 1
- `commission_per_trade`: 0
- `slippage_per_share`: 0.01
- `no_new_after_minute`: 360
- `eod_exit_minute`: 389
- `priority_policy`: metadata_priority (fixed)
- `daily_max_loss_r`: -1.5 (fixed)
- variable: `max_trades_per_day` (mtp=1 vs mtp=2 for PA-only; mtp=2 default for combos)

## Raw outputs (local-only; not committed)

- Materialized configs: `src/research/results/fixed_robust_profile_oow_v1/local_configs/**`
- Raw runs: `src/research/results/fixed_robust_profile_oow_v1/local_runs/<profile>/<window>/run_*`

## Curated outputs (committed)

This root will contain compact CSV/MD summaries + `CHATGPT_REVIEW_BUNDLE.md`.

