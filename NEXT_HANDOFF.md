# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Layer3 CORE smoke (historical research commit) | **`1735f42493bd40101e8961b9f74f04083ce3edca`** — `Research(layer3): run fixed profile core smoke` |
| Repo tip (this handoff) | **`Research(layer3): run optional smoke ablations`** on `main` — canonical full SHA: run `git log -1 --format=%H` after `git pull --ff-only` (abbrev shown elsewhere: `git log -1 --oneline`). |
| Prior doc-only chain on `main` | `770f050` / `399c7b2` / `388fca2` (handoff + progress around CORE push) |
| Push status | **Re-run** `git pull --ff-only` then `git push origin main`; confirm `git ls-remote origin refs/heads/main` equals local `HEAD` after push. |
| Working tree | Curated optional + complete roots **tracked**; expect **untracked** `layer3_fixed_profile_smoke_optional_v1/local_runs/**`, `local_configs/**`, CORE `layer3_fixed_profile_smoke_v1/local_*` if present. **Do not** `git add .`. |
| Expected untracked local-only | `local_runs/**` (metrics, compact trades), `.cache/qt/candidate_signals/**`, combiner `sweep_*` / `top_runs/`, heavy Layer2 scratch under `src/combiner/results/` |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **438 passed** |
| `python -m src.strategies.loader --list` | **35** strategies |
| Tracked-heavy check | No matches (`git ls-files` vs `top_runs`, raw `trades.csv`, `.parquet`, …) |
| Artifact validation | `layer3_fixed_profile_smoke_v1/layer3_smoke_artifact_validation.csv`; `layer3_fixed_profile_smoke_design_v1/layer3_design_artifact_validation.csv`; `layer3_fixed_profile_smoke_optional_v1/layer3_optional_artifact_validation.csv`; `layer3_fixed_profile_smoke_complete_v1/layer3_complete_artifact_validation.csv` — **0** parse failures, **0** absolute-path hits in scanned CSVs |
| Optional ChatGPT bundle | `src/research/results/layer3_fixed_profile_smoke_optional_v1/CHATGPT_REVIEW_BUNDLE.md` |
| Complete ChatGPT bundle | `src/research/results/layer3_fixed_profile_smoke_complete_v1/CHATGPT_REVIEW_BUNDLE.md` |
| Source maps | `src/research/results/layer3_fixed_profile_smoke_optional_v1/SOURCE_MAP.csv`, `src/research/results/layer3_fixed_profile_smoke_complete_v1/SOURCE_MAP.csv` (repo-relative `file_path` rows) |

## C. Task scope

| | |
|--|--|
| **Requested** | Run **optional** Layer3 baseline/ablation (**3** profiles × **4** windows = **12** runs), postprocess, **merge** with CORE into **complete** review; gates, cost overlay, complementarity, bundles, docs, tests, commit/push. |
| **Completed** | Optional **`primary_mtp2_meta`**, **`pa_gap_mtp1_meta`**, **`pa_only_mtp2_meta`** executed; **`layer3_fixed_profile_smoke_optional_v1/`** + **`layer3_fixed_profile_smoke_complete_v1/`**; `merge-complete`; runner + tests; **`PROCEED_TO_LAYER3_EXPANDED_STABILITY_DESIGN`** on complete decision. |
| **Intentionally not done** | CORE profiles **not** re-run; broad Layer2; mini/full WFO; live/paper; SPY; router; strategy/feature/selected-candidate **YAML** edits; committing `local_runs/**` / raw trades. |

## D. CORE recap (Layer3 smoke v1)

| profile_id | early_oow | insample_ref | late_oow | full_available | maxDD (full) | label (complete rollup) |
|------------|-----------|--------------|----------|----------------|--------------|-------------------------|
| `pa_only_mtp1_meta` | 45.14 | 37.97 | 21.49 | 104.59 | −17.71 | `LAYER3_SMOKE_PASS_WITH_WARNINGS` |
| `pa_gap_mtp2_meta` | 60.95 | 52.27 | 18.77 | 131.99 | −21.27 | `LAYER3_SMOKE_PASS_WITH_WARNINGS` |

*(Rounded; full precision in `complete_profile_window_summary.csv`.)*

## E. Optional execution

| Field | Value |
|-------|--------|
| Profiles | `primary_mtp2_meta`, `pa_gap_mtp1_meta`, `pa_only_mtp2_meta` |
| Windows | `early_oow`, `insample_ref`, `late_oow`, `full_available` |
| Expected runs | **12** |
| Actual | **12** OK (`run_execution_manifest.csv` / `run_discovery_manifest.csv`) |
| Failed / skipped | **0** |
| Raw local run root (untracked) | `src/research/results/layer3_fixed_profile_smoke_optional_v1/local_runs/**` |
| Sanitized manifest | `src/research/results/layer3_fixed_profile_smoke_optional_v1/run_execution_manifest_sanitized.csv` |

## F. Complete results (five profiles, total R)

| profile_id | role | early | insample | late | full | maxDD (full) | label |
|------------|------|------:|----------:|-----:|-----:|-------------:|--------|
| `primary_mtp2_meta` | BREADTH_BASELINE | 61.33 | 62.70 | 11.86 | 135.89 | −25.09 | `OPTIONAL_BASELINE_PASS_WITH_WARNINGS` |
| `pa_gap_mtp2_meta` | PRIMARY_COMBINED | 60.95 | 52.27 | 18.77 | 131.99 | −21.27 | `LAYER3_SMOKE_PASS_WITH_WARNINGS` |
| `pa_gap_mtp1_meta` | ABLATION_MTP1 | 54.00 | 45.28 | 18.12 | 117.40 | −22.34 | `LAYER3_SMOKE_PASS_WITH_WARNINGS` |
| `pa_only_mtp1_meta` | CLEAN_BASELINE | 45.14 | 37.97 | 21.49 | 104.59 | −17.71 | `LAYER3_SMOKE_PASS_WITH_WARNINGS` |
| `pa_only_mtp2_meta` | ABLATION_MTP2 | 45.14 | 37.97 | 21.49 | 104.59 | −17.71 | `LAYER3_SMOKE_PASS_WITH_WARNINGS` |

**`full_available` ranking (total R):** 1 `primary_mtp2_meta` (135.89R) → 2 `pa_gap_mtp2_meta` (131.99R) → 3 `pa_gap_mtp1_meta` (117.40R) → 4–5 PA-only variants (104.59R). **Default recommendation unchanged:** **PA+GAP `pa_gap_mtp2_meta`** as primary combined path; **PA-only** as clean baseline; **`primary_mtp2_meta`** optional breadth (CCI) only — higher full-span R but **weaker late_oow** and **deeper maxDD**.

## G. CORE vs optional interpretation

| Question | Answer |
|----------|--------|
| Does **`primary_mtp2_meta`** justify default CCI? | **No** for default — passes as **`OPTIONAL_BASELINE_PASS_WITH_WARNINGS`**; late_oow **11.86R** vs **18.77R** (`pa_gap_mtp2`) / **21.49R** (`pa_only_mtp1`); **`target_limit_stress`** on `full_available` still **> 0** (~96.33R). |
| **`pa_gap_mtp1_meta`** vs **`pa_gap_mtp2_meta`**? | **mtp2 wins** on full_available (**131.99** vs **117.40**); late_oow similar (**18.77** vs **18.12**). |
| **`pa_only_mtp2_meta`** vs **`pa_only_mtp1_meta`**? | **Numerically identical** on all four windows in this replay (mtp **does not bind** for PA-only here). |
| Optional changes CORE-only decision? | **Yes at complete layer:** move from historical **`RUN_OPTIONAL_LAYER3_BASELINE_ABLATION`** to **`PROCEED_TO_LAYER3_EXPANDED_STABILITY_DESIGN`** after optional evidence merged. |

## H. Gate results / cost / contribution

| Area | Outcome |
|------|---------|
| Window positivity | **PASS** all merged profile×window rows (`complete_gate_results.csv`) |
| **`primary_mtp2_meta` + target-limit stress** | `full_available` **positive**; `late_oow` **5.11R** under **`target_limit_stress`** (thin but **> 0**) |
| Warnings | Drawdown / monthly / quarterly / concentration warnings persist on several profiles — see `complete_risk_flags.md` |
| Contribution | **`complete_candidate_contribution.csv`** — multi-candidate profiles (`pa_gap_*`, `primary_*`); PA-only rows single-candidate |

## I. Decision (complete review)

**Exactly one:** **`PROCEED_TO_LAYER3_EXPANDED_STABILITY_DESIGN`**

- **`pa_gap_mtp2_meta`** still **≥** **`pa_gap_mtp1_meta`** on **`full_available`**; optional ablations **do not** contradict mtp2 choice.
- **`pa_only_mtp1_meta`** vs **`pa_only_mtp2_meta`** ≈ **0** delta — mtp **non-binding** for PA-only in this stack.
- **`primary_mtp2_meta`** stays **optional breadth** (CCI): **`OPTIONAL_BASELINE_PASS_WITH_WARNINGS`**, weaker **late_oow**, larger **maxDD** than CORE paths.
- Merged gates: **no FAIL** rows; cost overlay preserves **positive** economics where gated for **`full_available`**.
- Next design stage is **Layer3 expanded stability** — still **no** WFO/live/SPY until that design.

## J. Explicit non-runs and risks

- No broad Layer2 sweep; no mini-WFO; no full WFO; no live/paper; no **SPY**
- No `regime_router`; no production short support; no side-flip research execution
- No strategy plugins, feature primitives, selected-candidate **YAML** edits, combiner production promotion
- **Research-only** — OOW windows are **not** used to tune YAML parameters

## K. Files changed

- `src/research/run_layer3_fixed_profile_smoke.py` — optional postprocess, **`merge-complete`**, **`_repo_rel_path`**, complete decision rationale
- `tests/test_run_layer3_fixed_profile_smoke.py` — optional plan (12 rows), five-profile union, path hygiene
- `src/research/results/layer3_fixed_profile_smoke_optional_v1/**` (curated only; no `local_runs` / `local_configs`)
- `src/research/results/layer3_fixed_profile_smoke_complete_v1/**`
- Refreshed `layer3_smoke_artifact_validation.*`, `layer3_design_artifact_validation.csv`
- `src/research/results/RESULTS_INDEX.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, **`NEXT_HANDOFF.md`**

## L. Recommended next step

**Exactly one:** **Design Layer3 expanded stability review** (document folds, stress axes, and artifact schema **before** any WFO/live/SPY/router work).


