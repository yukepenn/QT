# Layer3 fixed-profile smoke design v1 — baseline inventory (2026-05-11)

## Git / decision state

- **git tip:** `eb291d0`
- **input decision:** `PROCEED_TO_LAYER3_FIXED_PROFILE_SMOKE_DESIGN` (from fixed robust-profile OOW v1)

## Files inspected (inputs)

- `src/research/results/fixed_robust_profile_oow_v1/CHATGPT_REVIEW_BUNDLE.md`
- `src/research/results/fixed_robust_profile_oow_v1/fixed_robust_profile_oow_decision.md`
- `src/research/results/fixed_robust_profile_oow_v1/profile_window_summary.csv`
- `src/research/results/fixed_robust_profile_oow_v1/monthly_summary.csv`
- `src/research/results/fixed_robust_profile_oow_v1/quarterly_summary.csv`
- `src/research/results/fixed_robust_profile_oow_v1/drawdown_summary.csv`
- `src/research/results/fixed_robust_profile_oow_v1/exit_slip/fixed_profile_exit_slip_scenarios.csv`

## Fixed profiles available

From `fixed_robust_profile_oow_v1/fixed_profile_definitions.csv`:

- `pa_only_mtp1_meta` (PA-only baseline)
- `pa_gap_mtp2_meta` (PA+GAP combined candidate)
- `primary_mtp2_meta` (PA+GAP+CCI breadth baseline)
- Optional ablations: `pa_gap_mtp1_meta`, `pa_only_mtp2_meta`

## Selected profiles for Layer3 smoke (design-only)

- **Required (default smoke)**:
  - `pa_only_mtp1_meta`
  - `pa_gap_mtp2_meta`
- **Optional baseline**:
  - `primary_mtp2_meta`
- **Optional ablations**:
  - `pa_gap_mtp1_meta`
  - `pa_only_mtp2_meta`

## Profiles excluded from default smoke (and why)

- Balanced core profiles (e.g. PA_004, CCI_002) — late-OOW dilution risk.
- Any VWAP / indicator five-pack / side-flip research-only candidates — out of scope.

## Known risk points Layer3 smoke must inspect

- late-OOW thin margin for CCI-including profile (`primary_mtp2_meta`)
- drawdown sensitivity (especially full-period)
- exit-mechanics mix (stop / target / max_hold shares)
- cost overlay sensitivity (target-limit-aware stress)
- **full_available overlap caveat**: do not treat sums across overlapping windows as independent economics

## This task’s scope

Design only: profiles, gates, run plan, expected outputs, review bundle. **Do not execute smoke.**

