# Layer3 fixed-profile smoke v1 — summary (CORE)

## 1. Purpose

Execute CORE Layer3 smoke (2 profiles × 4 windows) against fixed design gates.

## 2. Input design

- Design root: `D:/OneDrive - Washington University in St. Louis/QT/src/research/results/layer3_fixed_profile_smoke_design_v1`

## 3. CORE profiles

- `pa_only_mtp1_meta`
- `pa_gap_mtp2_meta`

## 4. Results

See `profile_window_summary.csv` and `fixed_oow_comparison.csv`.

## 5. Gates / risks / cost overlay

- `gate_results.csv`, `risk_flags.csv`
- `exit_slip/layer3_exit_slip_scenarios.csv`

## 6. Decision

**RUN_OPTIONAL_LAYER3_BASELINE_ABLATION**

## 7. Explicit non-runs

Optional profiles not run; no WFO/live/SPY/router/YAML edits.
