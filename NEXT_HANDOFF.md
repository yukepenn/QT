# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Main research commit (fixed-profile OOW anchor) | `dbd2817` — `Research: run fixed profile out-of-window validation` |
| Main research commit (candidate audit) | **`7e5da17b89c91e01f7eb3a8f5743eda015ed0da3`** — `Research: audit layer2 candidate robustness` |
| Repo tip | **`df25a6c`** — `Docs(handoff): consolidate git rows` (doc-only chain after `7e5da17`) |
| Push status | **Pushed** `main` → `origin` |
| Working tree | Expect **clean** tracked tree after explicit `git add`; **untracked:** `layer2_candidate_robustness_v1/local_runs/**`, `.cache/qt/candidate_signals/**`, `fixed_profile_oow_v1/local_runs/**` |
| Expected untracked local-only artifacts | Raw `trades.csv`, `config_resolved.yaml`, logs under `layer2_candidate_robustness_v1/local_runs/**` — **do not** `git add` |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK (re-run after edits) |
| `python -m pytest -q` | **421** passed |
| `python -m src.strategies.loader --list` | **35** strategies |
| New tests | `test_audit_l2_candidates_oow.py`, `test_side_flip_diagnostic.py`, `test_l2_core_policy_v2.py` |
| Tracked-heavy check | `git ls-files \| Select-String -Pattern "top_runs|trades.csv|compact_trades|enriched.csv|scored_trades|\.parquet|\.npy|\.npz|\.memmap"` — **no** matches |

## C. Execution

| Item | Value |
|------|-------|
| Audit command style | `python -m src.research.audit_l2_candidates_oow run --candidate-root src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates --output-root src/research/results/layer2_candidate_robustness_v1 --windows-root src/research/results/fixed_profile_oow_v1 --families vwap,indicator --skip-existing` |
| Postprocess | `python -m src.research.audit_l2_candidates_oow postprocess --candidate-root …/selected_candidates --output-root …/layer2_candidate_robustness_v1` |
| Families audited | **vwap** (8), **indicator** (19) |
| Windows audited | **early_oow**, **insample_ref**, **late_oow** |
| Local combiner runs | **81** (27×3) under `layer2_candidate_robustness_v1/local_runs/<candidate>/<window>/run_*` |
| Raw local run root | `src/research/results/layer2_candidate_robustness_v1/local_runs/` |
| Manifests | `candidate_audit_run_manifest.csv`, `run_execution_manifest.csv`, `run_discovery_manifest.csv` |
| Side-flip diagnostic | **`side_flip_diagnostic.py`** → `side_flip/side_flip_metrics.csv` (**`non_executable_sign_proxy`**, not a simulator flip) |

## D. Candidate-level OOW audit

| Metric | Count (audited slice **n=27**) |
|--------|--------------------------------:|
| total candidates audited | 27 |
| ROBUST_POSITIVE | 2 |
| INSAMPLE_ONLY | 7 |
| OOW_NEGATIVE (label) | 0 |
| OOW_MIXED | 17 |
| TOO_SPARSE | 0 |
| HIGH_TURNOVER_FRAGILE | 0 |
| ANTI_PREDICTIVE_CANDIDATE | 1 |

**ROBUST_POSITIVE:** `CCI_EXTREME_SNAPBACK_002`, `CCI_EXTREME_SNAPBACK_003`  
**ANTI_PREDICTIVE:** `MACD_MOMENTUM_TURN_003`  
**Worst cluster (insample-only VWAP):** `VWAP_RECLAIM_REJECT_001`–`003`

## E. Family-level summary

| audit_family | candidates_audited | robust_positive | insample_only | oow_mixed | oow_negative | too_sparse | high_turnover_fragile | anti_predictive | comment |
|----------------|-------------------:|----------------:|--------------:|----------:|---------------:|-------------:|----------------------:|----------------:|---------|
| indicator | 19 | 2 | 4 | 12 | 0 | 0 | 0 | 1 | CCI pocket only “robust” under heuristic |
| vwap | 8 | 0 | 3 | 5 | 0 | 0 | 0 | 0 | no robust-positive singletons |

## F. VWAP / indicator failure analysis

- **VWAP:** fixed-profile OOW negatives align with **candidate-level** weakness (zero robust-positive; reclaim-reject insample-only cluster).
- **Indicator:** fixed-profile failure is **broad** among audited names; **two** CCI variants pass heuristic robust-positive; **MACD_003** anti-predictive.
- **Combination vs single:** combinations still risky (overlap, mtp caps), but **single-name** evidence is already weak for most VWAP/indicator YAMLs audited here.
- **Turnover:** mtp3 profile stress remains **profile-level**; singleton slice did not populate `HIGH_TURNOVER_FRAGILE` under current thresholds.

## G. Side-flip / inverse diagnostic

| Question | Answer |
|----------|--------|
| Executable replay run? | **No** — combiner has no inversion flag |
| Artifact | `side_flip/side_flip_metrics.csv` with `diagnostic_kind=non_executable_sign_proxy` |
| Indicator mtp1/2/3 proxy (total_r → −total_r) | See compact table |

| profile_id | window_id | total_r (long profile) | side_flip_proxy_total_r |
|------------|------------|------------------------:|-------------------------:|
| indicator_mtp1 | early_oow | −29.81 | 29.81 |
| indicator_mtp1 | insample_ref | 18.76 | −18.76 |
| indicator_mtp1 | late_oow | −3.29 | 3.29 |
| indicator_mtp2 | early_oow | −104.17 | 104.17 |
| indicator_mtp2 | insample_ref | 46.51 | −46.51 |
| indicator_mtp2 | late_oow | −14.74 | 14.74 |
| indicator_mtp3 | early_oow | −163.73 | 163.73 |
| indicator_mtp3 | insample_ref | 58.01 | −58.01 |
| indicator_mtp3 | late_oow | −33.49 | 33.49 |

**Inverse hypothesis supported?** **No** for production or research promotion — proxy flips insample positives to negative; not an executable contrarian path (`side_flip_interpretation.md`).

## H. Robust l2_core policy v2

| Item | Value |
|------|-------|
| Policy doc | `l2_core_policy_v2.md` |
| Candidate actions CSV | `l2_core_policy_v2_candidate_actions.csv` |
| policy_action counts | KEEP_CORE **2**, DROP_FROM_CORE **7**, WATCHLIST_DIAGNOSTIC **17**, REQUIRES_SIDE_FLIP_RESEARCH **1** |
| Robust core dry-run | **Not created** — see `robust_core_not_enough_candidates.md` |
| Enough candidates survive? | **No** (only **2** robust-positive; single strategy family among them) |

## I. Decision

**Exactly one:** **`RUN_MORE_CANDIDATE_OOW_AUDIT`**

- **Rationale:** **39 / 66** l2_core YAMLs (**opening_trap**, **pa**, **afternoon**, **other**) not yet replayed; cannot conclude “all core fails” vs “VWAP/indicator only.”
- **Rationale:** audited slice shows **broad** VWAP weakness and **narrow** CCI strength only.
- **Rationale:** side-flip is **non-executable** proxy — does **not** unlock short/contrarian track.
- **Rationale:** robust-core dry-run thresholds **not met**.
- **Rationale:** defer **`REVISIT_LAYER1_SELECTION_CRITERIA`** until extended audit still shows pervasive failure.

## J. Explicit non-runs

mini-WFO; full WFO; live/paper; SPY; Global L1 rerun; broad Global L2 grid; strategy changes; feature primitive changes; selected candidate YAML edits; `regime_router`; hard regime filter; production short support; OOW parameter optimization; heavy artifact commits; `git add .`

## K. Risks / caveats

QQQ only; long-only candidate root; singleton audit envelope (`layer2_fixed_vwap_mtp2.yaml`) for execution fields; **partial** l2_core coverage in v1 pack; side-flip **research-only** proxy; raw trades **local-only**; no WFO; OOW not used for parameter tuning.

## L. Recommended next step

**Exactly one:** run singleton audit for **`opening_trap,pa,afternoon,other`** on **early_oow,insample_ref,late_oow**, then re-postprocess into the same result root (still **no** OOW tuning).
