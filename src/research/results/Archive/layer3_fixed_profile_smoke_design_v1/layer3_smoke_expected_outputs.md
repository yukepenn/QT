# Layer3 fixed-profile smoke v1 — expected outputs (DESIGN ONLY — NOT RUN)

This defines the **artifact contract** for a future Layer3 smoke run.

## Future output root

- `src/research/results/layer3_fixed_profile_smoke_v1/`

## Required curated outputs

See `layer3_smoke_expected_outputs.csv` for per-file details, including:

- purpose
- required columns (if CSV)
- curated / should-commit / ChatGPT-critical flags

## Key review rule

For economics, prefer **`profile_window_summary.csv`** rows (especially `full_available`) and do not treat sums across overlapping windows as independent.

