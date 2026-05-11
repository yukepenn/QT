# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Main research commit (audit baseline) | **`3fd30b7`** — `Research: complete layer2 candidate robustness audit` |
| Main research commit (robust v2 design cleanup) | **`530c293`** — `Chore(research): harden robust v2 design` |
| Repo tip | (this handoff update commit) run `git log -1 --oneline` |
| Push status | Pending until `git push` |
| Working tree status | Expect docs + curated design-only changes; keep untracked heavy artifacts uncommitted |
| Expected untracked local-only artifacts | `src/research/results/layer2_candidate_robustness_v1/local_runs/**`, `src/research/results/fixed_profile_oow_v1/local_runs/**`, `.cache/qt/candidate_signals/**`, combiner `sweep_*` / `top_runs/` |

## B. Validation

| Check | Expected |
|--------|----------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | Pass (428 tests) |
| `python -m src.strategies.loader --list` | 35 strategies |
| Tracked-heavy check | No matches for `top_runs|trades.csv|...` patterns |
| Artifact CSV validation | `design_artifact_validation.csv` shows 0 failures / 0 abs paths |

## C. Task scope

- **Requested:** clean/harden `robust_l2_core_v2_design/` artifacts and create design-only runnable skeletons + runbook.
- **Completed:** CSV hygiene (pandas-readable, multi-line, repo-relative paths), expanded candidate-set schema, full 66-row core/watchlist/drop actions, clarified raw vs design representatives, added deterministic artifact validator + tests, and added future diagnostic runbook/command draft (**NOT RUN**).
- **Intentionally not done:** no Layer2 sweep, no WFO, no live/SPY, no router, no strategy/feature/YAML edits, no OOW tuning, no heavy artifact commits.

## D. Input evidence (from full 66/66 audit)

- Coverage: **66/66** candidates, **198/198** candidate-window metric rows `OK`.
- Robust-positive (nominal): **10**
  - `CCI_EXTREME_SNAPBACK_002`, `CCI_EXTREME_SNAPBACK_003`
  - `GAP_ACCEPTANCE_FAILURE_001`–`004`
  - `PA_BUY_SELL_CLOSE_TREND_001`–`004`
- Anti-predictive: **5**
  - `MACD_MOMENTUM_TURN_003`
  - `MULTI_DAY_LEVEL_TRAP_001`–`004`
- Family robust counts: indicator **2**, opening_trap **4**, pa **4**, vwap **0**, afternoon **0**, other **0**.

## E. Dedupe / effective clusters

| cluster_id | members | representative | reason | include? |
|-----------|---------|----------------|--------|----------|
| gap_cluster | `GAP_ACCEPTANCE_FAILURE_001`–`004` | `GAP_ACCEPTANCE_FAILURE_001` | **metric-identical** + **trade-identical** (Jaccard=1.0) | keep **one** |
| pa_close_trend_core | `PA_BUY_SELL_CLOSE_TREND_001`–`003` | `PA_BUY_SELL_CLOSE_TREND_003` | **trade-identical** (Jaccard=1.0); pick best cross-window totals | keep **one** |
| pa_close_trend_secondary | `PA_BUY_SELL_CLOSE_TREND_004` | `PA_BUY_SELL_CLOSE_TREND_004` | partial overlap vs 001–003 | optional |
| cci_primary | `CCI_EXTREME_SNAPBACK_003` | `CCI_EXTREME_SNAPBACK_003` | positive both OOW; low overlap vs CCI_002 | keep |
| cci_secondary | `CCI_EXTREME_SNAPBACK_002` | `CCI_EXTREME_SNAPBACK_002` | weaker early OOW; low overlap vs CCI_003 | optional |

## F. Representative core design

| candidate_set | candidates | purpose | caveats |
|--------------|------------|---------|---------|
| primary_representative_core | `GAP_001`, `PA_003`, `CCI_003` | minimal redundancy / interpretability | GAP and PA deduped by overlap |
| balanced_representative_core | `GAP_001`, `PA_003`, `PA_004`, `CCI_003`, `CCI_002` | slightly broader but still capped | CCI_002 has weak early_oow |
| extended_robust_watchlist | all 10 robust-positive | documentation only | do not treat as core |
| exclude_from_core | DROP + SIDE_FLIP | diagnostic contrasts only | includes VWAP reclaim cluster + anti-predictive |

## G. Watchlist / drop design

- **Core representatives:** see sets above.
- **Secondary candidates:** PA_004, CCI_002 (balanced-only).
- **Watchlist diagnostics:** all `WATCHLIST_DIAGNOSTIC` plus KEEP-but-deduped equivalents.
- **Drop from core:** `DROP_FROM_CORE` (e.g. VWAP reclaim/reject 001–003; PA_TRADING_RANGE_BLS_HS_005; RSI_002; ST_004; MACD_001–002).
- **Side-flip research-only:** `REQUIRES_SIDE_FLIP_RESEARCH` (`MACD_003`, `MULTI_DAY_LEVEL_TRAP_001`–`004`).

## H. Future diagnostic design (NOT RUN)

- Candidate-set axis: primary, balanced, PA-only, GAP-only, CCI-only, and pairwise mixes (PA+GAP, PA+CCI, GAP+CCI).
- Small grid axes: `max_trades_per_day` ∈ {1,2}; `daily_max_loss_r` ∈ {−1.5, −2.0}; `priority_policy` ∈ {metadata_priority, score_adjusted_priority}.
- Risk controls: `max_open_positions=1`, `no_new_after_minute=360`, baseline `slippage=0.01`, `commission=0`.
- No router; no broad grid.

## I. Decision

**Exactly one:** **`RUN_SMALL_ROBUST_CORE_LAYER2_DIAGNOSTIC_DESIGN`**

- Dedupe ambiguity is resolved by overlap: **GAP 001–004** and **PA 001–003** are **trade-identical**.
- Representative sets are now well-defined and low-redundancy.
- Next task should be config/runbook design only; do not execute in this design pass.

## J. Explicit non-runs and risks

No Layer2 sweep; no mini/full WFO; no live/paper; no SPY; no Global L1 rerun; no broad Global L2 grid; no strategy changes; no feature primitive changes; no selected YAML edits; no router; no production short support; no OOW parameter tuning; no heavy artifact commits. **Singleton OOW ≠ combination OOW**; redundancy can still dominate combined systems.

## K. Files changed (this v2 design task)

- Script: `src/research/design_robust_l2_core_v2.py`
- Validator: `src/research/validate_research_artifacts.py`
- Test: `tests/test_design_robust_l2_core_v2.py`
- Curated root: `src/research/results/robust_l2_core_v2_design/` (clean CSVs, `design_artifact_validation.*`, `design_cleanup_inventory.md`, expanded config skeletons, runbook + command draft; all **DESIGN ONLY — NOT RUN**)
- Docs/indexes: `RESULTS_INDEX.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `NEXT_HANDOFF.md`

## L. Recommended next step

**Exactly one:** `RUN_SMALL_ROBUST_CORE_LAYER2_DIAGNOSTIC_DESIGN`
