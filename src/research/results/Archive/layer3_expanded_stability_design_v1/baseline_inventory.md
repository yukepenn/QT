# Layer3 expanded stability design v1 — baseline inventory

## Git tip (before this design commit)

- Parent `main` tip at design start: **`8f910a2693612fa433aab863de5af5fd03abf9ae`** — `Research(layer3): run optional smoke ablations` (Layer3 complete smoke merged).

## Complete Layer3 smoke decision (input)

- **`PROCEED_TO_LAYER3_EXPANDED_STABILITY_DESIGN`** (`layer3_fixed_profile_smoke_complete_v1/layer3_complete_smoke_decision.md`).

## Files inspected

- `NEXT_HANDOFF.md`
- `src/research/results/layer3_fixed_profile_smoke_complete_v1/CHATGPT_REVIEW_BUNDLE.md`
- `layer3_complete_smoke_decision.md`, `layer3_complete_smoke_summary.md`
- `complete_profile_window_summary.csv`, `complete_profile_full_available_summary.csv`
- `complete_ranking.csv`, `core_vs_optional_comparison.csv`
- `complete_gate_results.csv`, `complete_risk_flags.csv`
- `complete_exit_slip_comparison.csv`, `complete_candidate_contribution.csv`
- `complete_monthly_summary.csv`, `complete_quarterly_summary.csv` (worst months/quarters)
- `src/research/results/layer3_fixed_profile_smoke_v1/CHATGPT_REVIEW_BUNDLE.md`
- `src/research/results/fixed_robust_profile_oow_v1/CHATGPT_REVIEW_BUNDLE.md`
- `fixed_robust_profile_oow_v1/fixed_profile_definitions.csv` (candidate ids / knobs)

## Default profile recommendation (unchanged)

- **Clean baseline:** `pa_only_mtp1_meta`
- **Default combined:** `pa_gap_mtp2_meta`
- **Breadth / interpretability reference only:** `primary_mtp2_meta`

## Profiles selected for expanded stability (design scope)

| Tier | profile_id | In expanded stability |
|------|------------|------------------------|
| Required | `pa_only_mtp1_meta`, `pa_gap_mtp2_meta` | YES |
| Reference | `primary_mtp2_meta` | YES (comparison) |
| Optional reference | `pa_gap_mtp1_meta`, `pa_only_mtp2_meta` | YES (ablation / equivalence checks) |

## Excluded

- No VWAP-only or balanced alternate cores in this design v1 (out of scope for robust-core PA/GAP/CCI story).
- No SPY, router, or new strategies.

## Weak periods flagged in existing results (evidence anchors, not labels)

- **`R_2025Q1`**, **`R_2022Q4`** in `complete_risk_flags.csv` (quarterly PnL pockets; magnitudes vary by profile).
- Worst **`worst_month_r`** / **`worst_quarter_r`** columns in `complete_profile_window_summary.csv` for `full_available`.
- Example monthly negatives (from `complete_monthly_summary.csv`): e.g. `pa_gap_mtp2_meta` **2022-11**, **2025-01**/**02**; `pa_only_mtp1_meta` **2025-02** — used only as **candidates for slice analysis**, not as pre-assigned “market regime” names.

## Missing files

- None required for **design-only** completion. Future execution root `layer3_expanded_stability_v1/` is **not** created in this task.
