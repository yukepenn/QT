# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Latest commit before this work | `fda3deb` |
| New commit | **`dbd2817`** — `Research: run fixed profile out-of-window validation`; repo tip **`8337d7f`** |
| Push status | **Pushed** `main` → `origin` |
| Working tree | Tracked files clean after commit; **expected untracked:** `fixed_profile_oow_v1/local_runs/**`, `.cache/qt/candidate_signals/**`, other heavy diagnostics |
| Expected untracked local-only artifacts | Raw `trades.csv`, `trades_enriched.csv`, `config_resolved.yaml`, large logs under `fixed_profile_oow_v1/local_runs/**` — **do not** `git add` |

## B. Task scope

| | |
|--|--|
| Requested | Execute fixed-profile **out-of-window** combiner replays (QQQ), postprocess, selective enrichment, commit **curated** metrics only |
| Completed | `run` / `enrich` subcommands; `run_discovery_manifest.csv`; merged `run_execution_manifest.csv`; populated `oow/`, `insample_sanity/`, `exit_slip/`, `trade_number/`, `quality_score_transfer/`, `regime_stability/`; `execution_runbook.md`, multiline run docs; indicator insample reference rows anchored to **this** replay; decision **`REVISIT_LAYER2_CANDIDATE_SELECTION`** |
| Intentionally not done | mini/full WFO; live/paper; SPY; Global L1 rerun; broad Global L2 grid; strategy/feature/selected-candidate YAML edits; online `regime_router`; enrich **full_available** + **indicator_mtp3** (optional follow-up); committing `local_runs/` |

## C. Files changed

| Area | Paths |
|------|-------|
| Scripts | `src/research/fixed_profile_oow.py`, `src/research/fixed_profile_oow_lib.py` |
| Tests | `tests/test_fixed_profile_oow_lib.py` |
| Curated research results | `src/research/results/fixed_profile_oow_v1/**` except `local_runs/` |
| Docs / indexes | `src/research/results/RESULTS_INDEX.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `NEXT_HANDOFF.md` |
| Local-only raw outputs | `fixed_profile_oow_v1/local_runs/**` |

## D. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **412** passed |
| `python -m src.strategies.loader --list` | **35** strategies |
| New tests | `test_combiner_argv_has_no_signal_cache_flag`, `test_load_window_bounds_from_csv` |
| Tracked-heavy check | `git ls-files \| Select-String -Pattern "top_runs|trades.csv|..."` — **no** matches |

## E. Execution inventory

| Item | Value |
|------|--------|
| Profiles run | `vwap_mtp2`, `vwap_mtp1`, `indicator_mtp1`, `indicator_mtp2`, `indicator_mtp3` |
| Windows run | `insample_ref`, `early_oow`, `late_oow`, `full_available` |
| Local combiner runs | **20** (5×4) under `local_runs/<profile>/<window>/run_*` |
| Run manifest | `run_execution_manifest.csv` (execution log) + **`run_discovery_manifest.csv`** (filesystem truth from `postprocess`) |
| Raw local run root | `src/research/results/fixed_profile_oow_v1/local_runs/` |
| Sanity replay | **All five** `sanity_pass=True` on 2023–2024 (VWAP vs L2 refs; indicator vs **replay-anchored** refs — see `insample_sanity/insample_sanity_failure.md`) |
| Enrichment | `trades_enriched.csv` for VWAP + indicator mtp1/2 on **insample_ref**, **early_oow**, **late_oow** only |
| Missing / incomplete | No enrichment for **full_available** or **indicator_mtp3** windows (runtime); regime/score tables lean on enriched rows |

## F. Research results (headlines)

| Topic | Result |
|--------|--------|
| VWAP mtp=2 OOW | **Negative** early_oow (~−43R) and late_oow (~−14R); insample OK |
| VWAP mtp=1 OOW | **Negative** both OOW windows; slightly fewer trades than mtp2 |
| Indicator mtp=1 OOW | **Negative** early; **small negative** late (~−3.3R); insample **+18.8R** (not legacy ~43.5R doc) |
| Indicator mtp=2 OOW | **Worse** than mtp=1 on early_oow; late still negative |
| Indicator mtp=3 | Diagnostic — **large negative** OOW + very high turnover |
| Trade-number | VWAP #2 **not** reliably + OOW; indicator #2 **negative** OOW for mtp2/3 |
| Target-limit slip overlay | Softens vs symmetric stress; **does not** flip go/no-go |
| Quality score transfer | **Not** router-ready (threshold collapse / empty test cohorts on insample file) |
| Regime / unknown | CSVs populated where **enriched** trades exist |
| Decision | **`REVISIT_LAYER2_CANDIDATE_SELECTION`** |

## G. Explicit non-runs

mini-WFO; full rolling WFO; live/paper; SPY; Global L1 rerun; broad Global L2 grid; strategy changes; feature primitive changes; selected candidate YAML edits; hard regime filter; combiner `regime_router`; parameter optimization on OOW; OOW-driven YAML selection; `--use-signal-cache` on unsafe OneDrive roots; `git add .`; heavy artifact commits

## H. Risks / caveats

Fixed-profile only; no parameter tuning; QQQ long-only evidence; raw trades local-only; slip overlay research-only; indicator legacy headline R **not** reproduced — anchor to this replay for sanity checks; indicator mtp=3 turnover risk; partial enrichment coverage

## I. Recommended next step

**Exactly one:** **`REVISIT_LAYER2_CANDIDATE_SELECTION`**
