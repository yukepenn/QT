# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Latest commit before this work | `3f78f41` — verify with `git log -2 --oneline` |
| New commit | Verify with `git log -1 --oneline` after push |
| Push status | Run `git push`; then **Pushed** `main` → `origin` |
| Working tree | Tracked files clean after commit; **expected untracked:** `fixed_profile_oow_v1/local_runs/**`, `trade_quality_router_v1*/local_runs/**`, enriched/scored row CSVs, other heavy diagnostics |
| Expected untracked local-only artifacts | Raw combiner `trades.csv` under `fixed_profile_oow_v1/local_runs/**`; enriched row CSVs — **do not** `git add` |

## B. Task scope

| | |
|--|--|
| Requested | Fixed-profile **out-of-window** validation (VWAP + indicator; mtp 1/2/3; slip overlay; score transfer; regime stability) |
| Completed | `fixed_profile_oow.py`, `fixed_profile_oow_lib.py`; curated `fixed_profile_oow_v1/**` (YAMLs, data availability, postprocess outputs, summaries, decision stub); `test_fixed_profile_oow_lib.py`; docs indexes + handoff |
| Intentionally not done | Combiner replays not executed in this commit (no `local_runs/`); mini/full WFO; live/paper; SPY; Global L1; broad L2 grid; strategy/feature/candidate YAML edits; online `regime_router`; heavy artifact commits |

## C. Files changed

| Area | Paths |
|------|--------|
| Scripts | `src/research/fixed_profile_oow.py`, `src/research/fixed_profile_oow_lib.py` |
| Tests | `tests/test_fixed_profile_oow_lib.py` |
| Curated research results | `src/research/results/fixed_profile_oow_v1/**` (exclude `local_runs/`) |
| Docs / indexes | `src/research/results/RESULTS_INDEX.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `NEXT_HANDOFF.md` |

## D. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **411** passed |
| `python -m src.strategies.loader --list` | **35** strategies |
| New tests | `test_fixed_profile_oow_lib` |
| Tracked-heavy check | `git ls-files \| Select-String -Pattern "top_runs|trades.csv|..."` — **no** matches |

## E. Data / profile inventory

| Item | Status |
|------|--------|
| QQQ parquet | Present locally per `fixed_profile_oow_v1/data_availability.md` (re-run `inspect-data` if partitions change) |
| Windows | `early_oow`, `insample_ref`, `late_oow`, `full_available` (clipped to data) |
| Profiles | `vwap_mtp2`, `vwap_mtp1`, `indicator_mtp1`, `indicator_mtp2`, `indicator_mtp3` — YAMLs under `fixed_profile_oow_v1/configs/` |
| Sanity replay | `insample_sanity_metrics.csv` — `NOT_RUN` until combiner outputs exist |
| Raw runs | `fixed_profile_oow_v1/local_runs/<profile>/<window>/run_*/` — **local-only** |

## F. Research results

| Topic | Status |
|--------|--------|
| VWAP mtp=2 OOW | Pending local combiner + `postprocess` |
| VWAP mtp=1 OOW | Pending |
| Indicator mtp=1/2/3 OOW | Pending |
| Trade-number stability | Populated when `trades.csv` present |
| Target-limit slip overlay | `postprocess` writes `exit_slip/oow_exit_slip_scenario_comparison.csv` when runs exist |
| Quality score transfer | Requires **enriched** trades (`entry_regime_label`) |
| Regime / unknown | Same as enrichment |
| Decision | **`NEED_MORE_FIXED_PROFILE_OOW`** (`fixed_profile_oow_decision.md`) |

## G. Explicit non-runs

mini-WFO; full rolling WFO; live/paper; SPY; Global L1 rerun; broad Global L2 grid; strategy changes; feature primitive changes; selected candidate YAML edits; hard regime filter; combiner `regime_router`; parameter optimization on OOW; OOW-driven YAML selection; `--use-signal-cache` on unsafe OneDrive roots; `git add .`; heavy artifact commits

## H. Risks / caveats

Fixed-profile only; no parameter tuning; OOW limited by data gaps; QQQ long-only; slip overlay is research-only; quality/regime tables need enrichment; indicator mtp=3 turnover risk

## I. Recommended next step

**Exactly one:** **`NEED_MORE_FIXED_PROFILE_OOW`** — run combiner from `run_commands_snippet.md` (or `print-commands`), then `postprocess`; enrich trades if score/regime tables are required.
