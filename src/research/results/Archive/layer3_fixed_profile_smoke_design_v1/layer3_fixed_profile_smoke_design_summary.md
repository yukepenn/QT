# Layer3 fixed-profile smoke v1 — design summary (DESIGN ONLY — NOT RUN)

## 1) Purpose

Design a small, fixed-profile **Layer3 smoke** around the best fixed robust profiles from fixed-profile OOW v1, with explicit pass/fail gates and ChatGPT-reviewable artifacts.

## 2) Input evidence (fixed robust-profile OOW v1)

Headline per-window results are in `fixed_robust_profile_oow_v1/profile_window_summary.csv` (see also the fixed-profile ChatGPT bundle).

## 3) Selected profiles

- Default: `pa_only_mtp1_meta`, `pa_gap_mtp2_meta`
- Optional baseline: `primary_mtp2_meta`
- Optional ablations: `pa_gap_mtp1_meta`, `pa_only_mtp2_meta`

## 4) Gate design

Defined in `layer3_smoke_gate_design.csv` / `.md`:

- hard fail on window sign (`total_r > 0`)
- hard fail on target-limit-aware cost overlay sign (default profiles)
- stability and DD checks as warnings
- artifact hygiene gates (sanitized manifests; CSV parse; bundle present)

## 5) Run plan (not executed)

Defined in `layer3_smoke_run_plan.csv` / `.md`.

- core = **8 runs**
- full (with optionals) = **20 runs**

## 6) Risk register

Defined in `layer3_smoke_risk_register.csv` / `.md`.

## 7) Expected output schema (for future execution task)

Defined in `layer3_smoke_expected_outputs.csv` / `.md`.

## 8) Artifact / handoff quality

Design root includes:

- `CHATGPT_REVIEW_BUNDLE.md`
- `SOURCE_MAP.csv`
- machine-readable CSVs with `\n` newlines and no local absolute paths

## 9) Decision

See `layer3_fixed_profile_smoke_design_decision.md`.

## 10) Explicit non-runs

No execution; no combiner runs; no WFO/live/SPY/router; no strategy/feature/YAML edits.

## 11) Recommended next step

Execute **CORE** smoke only in a future task, using the draft command shapes in `future_layer3_smoke_commands_draft.md`.

