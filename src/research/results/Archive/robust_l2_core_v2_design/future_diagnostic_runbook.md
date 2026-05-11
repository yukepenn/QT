# Future small robust-core Layer2 diagnostic (DESIGN ONLY — NOT RUN)

This runbook describes how the **next task** should run a *small* Layer2 diagnostic for the robust l2_core v2 representative sets.

**Status:** design-only scaffolding. **Nothing in this folder was executed in this task.**

## Inputs (already curated)

- Candidate sets: `candidate_sets_design.csv`
- Representative roles + paths: `representative_candidate_manifest.csv`
- Action table (all 66): `core_watchlist_drop_actions.csv`
- Dedupe/cluster evidence: `effective_signal_clusters.csv`, `robust_candidate_overlap_matrix.csv`

## Candidate sets to test (small axis)

- `primary_representative_core`
- `balanced_representative_core`
- `pa_gap_core`
- `pa_cci_core`
- `gap_cci_core`
- `pa_only_core`
- `cci_only_core`

## Windows (match prior research conventions)

- `insample_ref`
- `early_oow`
- `late_oow`
- Optional: `full_available` (only if the runner supports it cleanly without extra data assumptions)

## Small risk grid (intentionally tiny)

- `max_trades_per_day`: 1, 2
- `daily_max_loss_r`: -1.5, -2.0
- `priority_policy`: `metadata_priority`, `score_adjusted_priority`

Fixed controls (hold constant across the diagnostic):

- `max_open_positions = 1`
- `commission_per_trade = 0`
- `slippage_per_share = 0.01`
- `no_new_after_minute = 360`
- **No router**

## Output root (future task)

Write all new diagnostic outputs under:

- `src/research/results/robust_l2_core_v2_diagnostic_v1/`

Do **not** write into `robust_l2_core_v2_design/` (that root is the static design pack).

## Explicit non-runs (this task)

- No Layer2 diagnostic run
- No Layer2 sweep
- No mini-WFO / full WFO
- No live/paper
- No SPY
- No candidate YAML edits
- No strategy/feature changes

