# CHATGPT_REVIEW_BUNDLE — fixed_robust_profile_oow_v1

This bundle is intended to be **readable in GitHub raw** and to contain the headline tables needed for review.

## 1) Git / validation

- **Repo tip:** `fc9b065`
- **Validation (baseline):**
  - `python -m compileall -q src`: OK
  - `python -m pytest -q`: 428 passed
  - strategy loader: 35 strategies

## 2) Profiles tested (fixed; no per-window best selection)

See `fixed_profile_definitions.csv`.

| profile_id | candidate_ids | mtp | daily_max_loss_r | priority_policy |
| --- | --- | --- | --- | --- |
| pa_only_mtp1_meta | PA_BUY_SELL_CLOSE_TREND_003 | 1 | -1.5 | metadata_priority |
| pa_only_mtp2_meta | PA_BUY_SELL_CLOSE_TREND_003 | 2 | -1.5 | metadata_priority |
| pa_gap_mtp2_meta | PA_BUY_SELL_CLOSE_TREND_003, GAP_ACCEPTANCE_FAILURE_001 | 2 | -1.5 | metadata_priority |
| primary_mtp2_meta | PA_BUY_SELL_CLOSE_TREND_003, GAP_ACCEPTANCE_FAILURE_001, CCI_EXTREME_SNAPBACK_003 | 2 | -1.5 | metadata_priority |
| pa_gap_mtp1_meta | PA_BUY_SELL_CLOSE_TREND_003, GAP_ACCEPTANCE_FAILURE_001 | 1 | -1.5 | metadata_priority |

## 3) Windows

| window | start | end |
| --- | --- | --- |
| early_oow | 2020-01-01 | 2022-12-31 |
| insample_ref | 2023-01-01 | 2024-12-31 |
| late_oow | 2025-01-01 | 2026-04-30 |
| full_available | 2020-01-01 | 2026-04-30 |

## 4) Overall results (total_r / trades / maxDD)

Source: `profile_window_summary.csv`.

| profile_id | window | trades | total_r | max_dd_r | pf_r |
| --- | --- | --- | --- | --- | --- |
| pa_only_mtp1_meta | early_oow | 650 | 45.14 | -10.54 | 1.189 |
| pa_only_mtp1_meta | insample_ref | 443 | 37.97 | -9.83 | 1.230 |
| pa_only_mtp1_meta | late_oow | 286 | 21.49 | -12.69 | 1.206 |
| pa_only_mtp1_meta | full_available | 1379 | 104.59 | -17.71 | 1.205 |
| pa_gap_mtp2_meta | early_oow | 818 | 60.95 | -13.56 | 1.191 |
| pa_gap_mtp2_meta | insample_ref | 563 | 52.27 | -11.24 | 1.234 |
| pa_gap_mtp2_meta | late_oow | 366 | 18.77 | -11.96 | 1.127 |
| pa_gap_mtp2_meta | full_available | 1747 | 131.99 | -21.27 | 1.191 |
| primary_mtp2_meta | early_oow | 1024 | 61.33 | -21.26 | 1.151 |
| primary_mtp2_meta | insample_ref | 694 | 62.70 | -14.91 | 1.235 |
| primary_mtp2_meta | late_oow | 470 | 11.86 | -16.49 | 1.061 |
| primary_mtp2_meta | full_available | 2188 | 135.89 | -25.09 | 1.157 |

Notes:
- `pa_only_mtp1_meta` and `pa_only_mtp2_meta` are identical here (mtp not binding for single-candidate profile).
- `pa_gap_mtp1_meta` was also executed and is positive across windows (see CSVs).

## 5) Monthly / quarterly / yearly stability

Curated CSVs:

- `monthly_summary.csv`
- `quarterly_summary.csv`
- `yearly_summary.csv`

## 6) Drawdown summary

- `drawdown_summary.csv` (month-level maxDD estimates from per-month trade sequences)

## 7) Contribution summary

This fixed-profile runner does **not** attribute per-candidate contributions for multi-candidate profiles (it is available in the diagnostic v1 root). For fixed-profile review, focus on locked profile totals + stability tables.

## 8) Cost overlay summary (target-limit-aware)

- `exit_slip/fixed_profile_exit_slip_scenarios.csv`

## 9) Decision + next step

- Decision: `fixed_robust_profile_oow_decision.md`
- Summary: `fixed_robust_profile_oow_summary.md`
- Key findings: `fixed_robust_profile_oow_key_findings.csv`

## 10) Explicit non-runs

- No broad Layer2
- No WFO (mini/full)
- No live/paper
- No SPY
- No router
- No strategy / feature / YAML edits
- No signal cache

