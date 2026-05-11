# CHATGPT_REVIEW_BUNDLE — layer3_fixed_profile_smoke_design_v1 (DESIGN ONLY — NOT RUN)

## 1) Current state

- Input decision (from fixed robust-profile OOW v1): `PROCEED_TO_LAYER3_FIXED_PROFILE_SMOKE_DESIGN`
- This root is **design-only**. No Layer3 execution is performed here.

## 2) Fixed robust-profile OOW v1 recap (inputs)

Source: `src/research/results/fixed_robust_profile_oow_v1/profile_window_summary.csv` and the fixed-profile bundle.

Headline window totals (total_r / max_dd_r):

- `pa_only_mtp1_meta`:
  - early_oow: **45.14** / -10.54
  - insample_ref: **37.97** / -9.83
  - late_oow: **21.49** / -12.69
  - full_available: **104.59** / -17.71
- `pa_gap_mtp2_meta`:
  - early_oow: **60.95** / -13.56
  - insample_ref: **52.27** / -11.24
  - late_oow: **18.77** / -11.96
  - full_available: **131.99** / -21.27
- `primary_mtp2_meta`:
  - early_oow: **61.33** / -21.26
  - insample_ref: **62.70** / -14.91
  - late_oow: **11.86** / -16.49
  - full_available: **135.89** / -25.09

Important caveat: do not treat sums across overlapping windows (including `full_available`) as independent economics.

## 3) Selected Layer3 smoke profiles

Source: `layer3_smoke_profile_selection.csv`.

- **CORE (default smoke)**:
  - `pa_only_mtp1_meta` (CLEAN_BASELINE)
  - `pa_gap_mtp2_meta` (PRIMARY_COMBINED)
- **OPTIONAL**:
  - baseline: `primary_mtp2_meta`
  - ablations: `pa_gap_mtp1_meta`, `pa_only_mtp2_meta`

## 4) Gate design (pass/fail)

Source: `layer3_smoke_gate_design.md` / `.csv`.

- Hard fails:
  - `total_r > 0` for each window
  - target-limit-aware cost overlay preserves sign for default profiles (esp. `full_available`)
- Warnings:
  - DD expansion vs validation
  - worst month / worst quarter pockets (flag `2022Q4`, `2025Q1`)
  - high `max_hold` share (exit-mechanics dependence)
- Artifact gates:
  - sanitized manifests
  - CSV parse + no abs paths
  - bundle + source map present

## 5) Run plan (DESIGN ONLY — NOT RUN)

Source: `layer3_smoke_run_plan.csv` / `.md`.

- **Core plan:** 2 profiles × 4 windows = **8 runs**
- **With optional baseline:** +4 = **12**
- **With ablations:** +8 = **20**

Fixed settings:

- commission 0; slippage 0.01
- no router; no short side
- max_open_positions 1; no_new_after_minute 360
- no signal cache by default

## 6) Risk register (what smoke must inspect)

Source: `layer3_smoke_risk_register.csv` / `.md`.

Top risks:

- cost-overlay sign flip
- late-OOW fragility pockets (notably `2025Q1`)
- reporting overlap caveat (`full_available`)

## 7) Expected outputs (future run contract)

Source: `layer3_smoke_expected_outputs.csv`.

ChatGPT-critical:

- `profile_window_summary.csv` (per-window economics)
- monthly/quarterly/yearly stability tables
- drawdown and exit-reason summaries
- gate results + risk flags
- `CHATGPT_REVIEW_BUNDLE.md` + `SOURCE_MAP.csv`

## 8) Explicit non-runs (this task)

- No Layer3 execution / backtests
- No broad Layer2
- No WFO
- No live/paper
- No SPY
- No router
- No strategy/feature/YAML edits

## 9) Decision (design-level)

Source: `layer3_fixed_profile_smoke_design_decision.md`.

**Decision:** `RUN_LAYER3_FIXED_PROFILE_SMOKE`

## 10) Recommended next step

Implement and execute the **CORE** smoke only (8 runs) in a follow-up task, using `future_layer3_smoke_commands_draft.md` as the starting point.

