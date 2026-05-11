# Robust l2_core v2 diagnostic v1 — summary (RUN)

## 1) Purpose

Run a *small* combined-system Layer2 diagnostic for the robust l2_core v2 representative sets (PA/GAP/CCI pockets), without broad grids, without WFO, and without any YAML/strategy changes.

## 2) Inputs

- Design root: `src/research/results/robust_l2_core_v2_design/`
- Candidate sets: `candidate_sets_design.csv`
- Representative manifest: `representative_candidate_manifest.csv`

## 3) Candidate sets tested

1. `primary_representative_core` = GAP_001 + PA_003 + CCI_003
2. `balanced_representative_core` = GAP_001 + PA_003 + PA_004 + CCI_003 + CCI_002
3. `pa_gap_core`
4. `pa_cci_core`
5. `gap_cci_core`
6. `pa_only_core`
7. `cci_only_core`

## 4) Windows

- `insample_ref` (2023–2024)
- `early_oow` (2020–2022)
- `late_oow` (2025–2026)

## 5) Grid (tiny)

- `max_trades_per_day`: 1, 2
- `daily_max_loss_r`: -1.5, -2.0
- `priority_policy`: metadata_priority, score_adjusted_priority

Total: **168** runs = 7 sets × 3 windows × 2 × 2 × 2.

## 6) Headline results (best per set/window)

See `candidate_set_summary.csv` for the authoritative table. High-level:

- **early_oow:** strongest sets are `primary_representative_core` (~61 R) and `pa_gap_core` (~61 R)
- **insample_ref:** strongest is `balanced_representative_core` (~72 R)
- **late_oow:** strongest is `pa_only_core` (~21.5 R), then `pa_gap_core` (~18.8 R)

## 7) Grid-axis effects

See `grid_axis_summary.csv`.

- **max_trades_per_day**: `2` materially improves **late_oow** relative to `1`.
- **daily_max_loss_r**: minimal impact in this tiny grid (cap not binding).
- **priority_policy**: minimal impact for these candidate sets.

## 8) Complementarity / conflict

See `complementarity/candidate_contribution_by_set.csv`.

Key pattern:

- PA contributes the majority of trades/total R in most combined sets.
- GAP adds meaningful contribution in `pa_gap_core` / `primary_representative_core`.
- CCI contributes positively overall, but secondary additions can dilute some windows.

## 9) Cost overlay (target-limit-aware)

See `exit_slip/robust_core_exit_slip_scenarios.csv`.

The overlay reduces totals under stress but preserves the sign for top configurations (i.e., conclusions are not purely a slippage artifact under this overlay).

## 10) Decision

See `robust_l2_core_v2_diagnostic_decision.md`.

## 11) Explicit non-runs

- No broad Layer2 sweep
- No mini/full WFO
- No live/paper
- No SPY
- No strategy/feature/candidate-YAML edits
- No signal cache

