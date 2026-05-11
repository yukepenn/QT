# Layer3 fixed-profile smoke v1 — gate design (DESIGN ONLY — NOT RUN)

This defines **pass/fail gates** for a future Layer3 smoke run over the fixed profiles.

Important: thresholds here are **smoke-level sanity gates**, not an optimization spec.

## Gate categories

### 1) Window gates (hard fails)

- **Each window must be net positive**: `total_r > 0` for `early_oow`, `insample_ref`, `late_oow`, `full_available`.

### 2) Drawdown gates (warnings unless catastrophic)

- Flag if `max_dd_r` becomes materially worse than fixed-profile validation.
- Treat large DD as a **warning** unless paired with weak `late_oow` or negative cost-overlay.

### 3) Monthly / quarterly stability gates (warnings)

Smoke should explicitly surface:

- negative month ratio (by window; especially `full_available`)
- worst month and worst quarter (by window)
- special flags for the known pockets:
  - `2022Q4`
  - `2025Q1`

### 4) Cost overlay gates (hard fail for main overlay)

- Under a **target-limit-aware** stress overlay, `full_available` must remain positive for default profiles.

### 5) Exit mechanics gates (warnings)

- Monitor `max_hold` share; high `max_hold` share is a robustness risk.

### 6) Interpretability gates (qualitative)

- `pa_only_mtp1_meta` must remain the clean baseline.
- `pa_gap_mtp2_meta` must not materially harm late OOW vs PA-only.
- `primary_mtp2_meta` can remain optional baseline only if late OOW margin is thin.

### 7) Artifact gates (hard fails)

- All curated CSVs parse with `pd.read_csv`.
- Sanitized manifests exist (no local absolute paths).
- `CHATGPT_REVIEW_BUNDLE.md` present + readable in GitHub raw.

Source-of-truth CSV: `layer3_smoke_gate_design.csv`.

## Suggested future smoke outcome labels

- `LAYER3_SMOKE_READY`
- `LAYER3_SMOKE_READY_WITH_WARNINGS`
- `FAIL_LAYER3_SMOKE`

This design task does **not** assign a run outcome label (no execution).

