# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Main research commit | **`1735f42493bd40101e8961b9f74f04083ce3edca`** — `Research(layer3): run fixed profile core smoke` |
| Repo tip (handoff file) | **`Docs(handoff): layer3 CORE smoke next handoff`** — the commit on `main` immediately **after** the research commit above (touches only `NEXT_HANDOFF.md`). |
| Push status | Run `git push origin main` then confirm `git ls-remote origin refs/heads/main` matches local `HEAD`. |
| Working tree status | Curated `layer3_fixed_profile_smoke_v1/**` tracked; expect **untracked** `layer3_fixed_profile_smoke_v1/local_runs/**`, `local_configs/**`, and other research scratch under `src/research/results/` (do not `git add .`). |
| Expected untracked local-only artifacts | `src/research/results/layer3_fixed_profile_smoke_v1/local_runs/**` (incl. `compact_trades.csv`, `metrics.json`), `local_configs/**`, `.cache/qt/candidate_signals/**`, combiner `sweep_*` / `top_runs/` |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **435 passed** |
| `python -m src.strategies.loader --list` | **35** strategies |
| Tracked-heavy check | No matches (`top_runs`, raw `trades.csv`, `.parquet`, etc.) |
| Artifact validation | `layer3_fixed_profile_smoke_v1/layer3_smoke_artifact_validation.csv` — curated CSVs OK; design + fixed OOW validation CSVs refreshed in research commit |
| ChatGPT bundle | `src/research/results/layer3_fixed_profile_smoke_v1/CHATGPT_REVIEW_BUNDLE.md` |
| Source map | `src/research/results/layer3_fixed_profile_smoke_v1/SOURCE_MAP.csv` |

## C. Task scope

| | |
|--|--|
| **Requested** | Execute **Layer3 fixed-profile CORE smoke v1** (2 profiles × 4 windows = **8** runs), gates, cost overlay, complementarity, handoff refresh. |
| **Completed** | Design v1 already **`RUN_LAYER3_FIXED_PROFILE_SMOKE`**; **CORE smoke executed** (`pa_only_mtp1_meta`, `pa_gap_mtp2_meta`); runner `run_layer3_fixed_profile_smoke.py` + tests; curated summaries, gates, risk flags, exit/slip, comparison vs `fixed_robust_profile_oow_v1`; decision **`RUN_OPTIONAL_LAYER3_BASELINE_ABLATION`**. |
| **Intentionally not done** | Optional profiles (`primary_mtp2_meta`, `pa_gap_mtp1_meta`, `pa_only_mtp2_meta`); broad Layer2; WFO; live/paper; SPY; router; strategy/feature/YAML edits; committing `local_runs/**` / raw trades. |

## D. Input design recap

| Item | Detail |
|------|--------|
| Design root | `src/research/results/layer3_fixed_profile_smoke_design_v1/` (**design complete**; decision **`RUN_LAYER3_FIXED_PROFILE_SMOKE`**) |
| CORE profiles | `pa_only_mtp1_meta`, `pa_gap_mtp2_meta` |
| Windows | `early_oow`, `insample_ref`, `late_oow`, `full_available` |
| Expected runs | **8** |
| Gates | Window positivity, drawdown warnings, monthly/quarterly weakness, target-limit stress positivity on `full_available`, max_hold share, artifact sanity (see `gate_results.csv`) |

## E. Execution

| Field | Value |
|-------|--------|
| Profiles | `pa_only_mtp1_meta`, `pa_gap_mtp2_meta` |
| Windows | `early_oow`, `insample_ref`, `late_oow`, `full_available` |
| Expected runs | **8** |
| Actual completed | **8** OK (`run_execution_manifest.csv` / `run_discovery_manifest.csv`) |
| Failed / skipped | **0** (no `failed_runs.csv`) |
| Raw local run root (untracked) | `src/research/results/layer3_fixed_profile_smoke_v1/local_runs/**` |
| Sanitized manifest | `src/research/results/layer3_fixed_profile_smoke_v1/run_execution_manifest_sanitized.csv` |

## F. Results (total R by window; maxDD on full_available)

| profile_id | early_oow | insample_ref | late_oow | full_available | maxDD (full) | label |
|------------|-----------|----------------|----------|------------------|--------------|--------|
| `pa_only_mtp1_meta` | 45.14 | 37.97 | 21.49 | 104.59 | −17.71 | `LAYER3_CORE_SMOKE_PASS_WITH_WARNINGS` |
| `pa_gap_mtp2_meta` | 60.95 | 52.27 | 18.77 | 131.99 | −21.27 | `LAYER3_CORE_SMOKE_PASS_WITH_WARNINGS` |

*(Rounded to two decimals; full precision in `profile_window_summary.csv`.)*

## G. Gate results and risk flags

| Area | Outcome |
|------|---------|
| Window positivity (`win_positive_all`) | **PASS** all 8 profile×window rows |
| Cost (`limit_stress_positive_full` on `full_available`) | **PASS** both profiles (target-limit-aware stress total R > 0) |
| Drawdown (`dd_*_warning`) | **WARNING** tiers only (no FAIL); see `gate_results.csv` |
| Monthly / quarterly | Worst-month / worst-quarter **WARNING** on `full_available` for both; neg-month cap **PASS** |
| Exit mechanics | `max_hold_share_warning` **PASS** both (< 0.60) |
| Quarterly pockets | **2025Q1** and **2022Q4** negative R pockets flagged in `risk_flags.md` (WARNING/INFO) |
| Profile concentration | `R_PA_CONCENTRATION`, `R_GAP_DEPENDENCE`, `R_LATE_OOW_GAP_VS_PA` documented in `risk_flags.md` |

## H. Cost overlay and contribution

| Topic | Finding |
|-------|---------|
| Target-limit stress | `full_available` **target_limit_stress** total R **> 0** for both profiles (see `exit_slip/layer3_exit_slip_scenarios.csv` / `gate_results.csv`). |
| Symmetric stress / ranking | PA+GAP stays ahead in total R under overlay scenarios on the same windows; see `exit_slip/layer3_exit_slip_summary.md`. |
| Stop sensitivity | Higher stop share on PA+GAP vs PA-only; documented in exit-reason tables and risk notes. |
| PA vs GAP | `complementarity/profile_candidate_contribution.*` — GAP adds most of incremental R in early/insample; late_oow PA-only slightly ahead on total R (see `risk_flags.md` `R_LATE_OOW_GAP_VS_PA`). |

## I. Decision

**Exactly one:** **`RUN_OPTIONAL_LAYER3_BASELINE_ABLATION`**

- Both CORE profiles pass smoke gates with **manageable WARNING** levels (no FAIL gates).
- Economics align with **`fixed_robust_profile_oow_v1`** reference within floating-point noise (`fixed_oow_comparison.csv`).
- Cost overlay preserves **positive** economics under **target_limit_stress** on `full_available`.
- PA+GAP remains the stronger **absolute R** combined profile; PA-only remains the **cleaner single-candidate** baseline; late_oow shows **PA-only slightly higher R** than PA+GAP (interpretation in complementarity + risk flags).
- Optional breadth / MTP ablations are the **next incremental evidence** before any expanded stability design.

## J. Explicit non-runs and risks

- No **`primary_mtp2_meta`**, **`pa_gap_mtp1_meta`**, **`pa_only_mtp2_meta`** in this task  
- No broad Layer2 sweep; no mini/full WFO; no live/paper; no SPY  
- No strategy plugins, feature primitives, selected-candidate YAML edits, combiner production config promotion  
- No `regime_router`, no production short support, no side-flip research  
- Research-only; **no** cross-symbol / live robustness claims  

## K. Files changed (research commit)

- `src/research/run_layer3_fixed_profile_smoke.py` — Layer3 smoke runner (`--dry-run`, `run`, `postprocess`; `--data-dir` default `data/raw/ibkr`)  
- `tests/test_run_layer3_fixed_profile_smoke.py`  
- `src/research/results/layer3_fixed_profile_smoke_v1/**` — curated CSV/MD (excludes `local_runs`, `local_configs`)  
- `src/research/results/RESULTS_INDEX.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`  

## L. Recommended next step

**Exactly one:** **`RUN_OPTIONAL_LAYER3_BASELINE_ABLATION`** — add optional profiles `primary_mtp2_meta`, `pa_gap_mtp1_meta`, and/or `pa_only_mtp2_meta` in a **new** Layer3 smoke task using the same runner flags (`--include-optional-baseline`, `--include-ablations` as designed), still **no** WFO/live/SPY/router/strategy/YAML edits.
