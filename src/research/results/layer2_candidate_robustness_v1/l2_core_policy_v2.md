# l2_core policy v2 (post **full** singleton OOW audit, 66 YAMLs)

## Principles

1. **Singleton OOW evidence** is a **hard gate** for “core” promotion under the fixed audit envelope — no OOW parameter retuning to pass the gate.
2. **`ROBUST_POSITIVE`** → **`KEEP_CORE_CANDIDATE`** for **design** purposes; production promotion still requires **dedupe**, **turnover**, and **overlap** review.
3. **`INSAMPLE_ONLY`** / strong negative OOW with good counts → **`DROP_FROM_CORE`** (long-only core).
4. **`ANTI_PREDICTIVE_CANDIDATE`** → **`REQUIRES_SIDE_FLIP_RESEARCH`** (non-executable proxy only today).
5. **`OOW_MIXED`** / **`OOW_NEGATIVE`** → default **`WATCHLIST_DIAGNOSTIC`** unless a documented overlay contract exists (overlays are **not** rescues for catastrophic baselines).
6. **Family quotas:** at least **two** non-degenerate families for any “robust core v2” narrative; **dedupe** identical metric stems (**GAP** quadruplet; near-duplicate **PA close trend** IDs).
7. **VWAP / indicator mtp stacks:** remain **high risk** in core unless future audits change the contract.
8. **Target-limit / router overlays** remain **secondary** to baseline singleton stability.

## Candidate actions

Authoritative per-row actions: `l2_core_policy_v2_candidate_actions.csv` (mirrors `candidate_robustness_labels.csv`).

## Action summary (full audit)

| policy_action | count |
|---------------|------:|
| WATCHLIST_DIAGNOSTIC | 43 |
| KEEP_CORE_CANDIDATE | 10 |
| DROP_FROM_CORE | 8 |
| REQUIRES_SIDE_FLIP_RESEARCH | 5 |

See also `l2_core_policy_v2_action_summary.csv` and `l2_core_policy_v2_action_summary_by_family.csv`.

## Robust core dry-run

`robust_core_dry_run/selected_candidates_manifest.csv` — **PASS** (research-only; **not** copied to production).
