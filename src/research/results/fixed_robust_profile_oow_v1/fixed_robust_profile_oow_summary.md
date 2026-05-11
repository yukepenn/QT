# Fixed robust-profile OOW v1 — summary (RUN)

## Purpose

Validate whether **locked robust-core profiles** (fixed candidates + fixed knobs) remain positive across windows, without “best-per-window” leakage.

## Profiles tested

See `fixed_profile_definitions.csv`:

- `pa_only_mtp1_meta`
- `pa_only_mtp2_meta`
- `pa_gap_mtp2_meta`
- `primary_mtp2_meta`
- `pa_gap_mtp1_meta` (optional but executed)

## Windows tested

- `early_oow` (2020–2022)
- `insample_ref` (2023–2024)
- `late_oow` (2025–2026-04)
- `full_available` (2020–2026-04)

## Headline results (total_r)

From `profile_window_summary.csv`:

- **pa_only_mtp1_meta**: early ~45.14R, insample ~37.97R, late ~21.49R, full ~104.59R
- **pa_gap_mtp2_meta**: early ~60.95R, insample ~52.27R, late ~18.77R, full ~131.99R
- **primary_mtp2_meta**: early ~61.33R, insample ~62.70R, late ~11.86R, full ~135.89R

## Stability by month / quarter / year

Curated tables:

- `monthly_summary.csv`
- `quarterly_summary.csv`
- `yearly_summary.csv`

## Drawdown / exit / trade-number

- `drawdown_summary.csv`
- `exit_reason_summary.csv`
- `trade_number_summary.csv`

## Cost overlay (target-limit-aware)

See `exit_slip/fixed_profile_exit_slip_scenarios.csv`.

## Decision

See `fixed_robust_profile_oow_decision.md`.

## Explicit non-runs

No broad Layer2 / WFO / live / SPY / router / YAML edits / signal cache.

