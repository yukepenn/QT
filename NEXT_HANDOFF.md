# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Latest commit before this work | `39c3056` — (verify with `git log -2 --oneline`) |
| New commit | **`ccdd0bb`** — `Research: extend trade quality enrichment diagnostics` (**repo tip** `ed19377` — handoff follow-ups after v1.5 bundle) |
| Push status | **Pushed** `main` → `origin` (`39c3056..ed19377`) |
| Working tree | Tracked files clean after commit; **expected untracked:** `src/research/results/trade_quality_router_v1/local_runs/**`, `trade_quality_router_v1/enriched_trades/*`, `trade_quality_router_v1_5/local_runs/**`, `trade_quality_router_v1_5/enriched_staging/**`, scored row CSVs under v1, other pre-existing heavy diagnostics |
| Expected untracked local-only artifacts | Raw combiner `trades.csv`, row-level enriched/scored CSVs, `local_runs/`, `enriched_staging/` — **do not** `git add` |

## B. Task scope

| | |
|--|--|
| Requested | Trade Quality Router **v1.5** diagnostics (unknown decomposition, VWAP holdout + trade #2, indicator mtp 2/3, exit/slip overlay, offline score v1.5, decision + summary) |
| Completed | Scripts + tests + curated `trade_quality_router_v1_5/**` (no strategy/feature/combiner/candidate changes); diag YAMLs mtp2/mtp3 |
| Intentionally not done | Online `regime_router`; hard regime filters; mini/full WFO; live/paper; SPY; Global L1 / large L2 grids; simulator exit-type slip productization; committing raw trades / enriched rows / `local_runs/` |

## C. Files changed

| Area | Paths |
|------|--------|
| Scripts | `src/research/decompose_regime_unknown.py`, `validate_trade_quality_holdout.py`, `analyze_exit_slip_attribution.py`, `build_indicator_mtp_diagnostics.py`, `score_trade_quality_v15.py`, `trade_quality_unknown.py` |
| Tests | `tests/test_decompose_regime_unknown.py`, `tests/test_validate_trade_quality_holdout.py`, `tests/test_analyze_exit_slip_attribution.py` |
| Curated research results | `src/research/results/trade_quality_router_v1_5/**` (exclude `local_runs/`, `enriched_staging/`) |
| Docs / indexes | `src/research/results/RESULTS_INDEX.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `NEXT_HANDOFF.md` |
| Local-only heavy | `trade_quality_router_v1_5/local_runs/`, `trade_quality_router_v1_5/enriched_staging/`, v1 `enriched_trades/` |

## D. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **404** passed |
| `python -m src.strategies.loader --list` | **35** strategies |
| New tests | `test_decompose_regime_unknown`, `test_validate_trade_quality_holdout`, `test_analyze_exit_slip_attribution` |
| Tracked-heavy check | `git ls-files \| Select-String -Pattern "top_runs|trades.csv|..."` — **no** matches |

## E. Research results

| Topic | Finding |
|--------|--------|
| Unknown decomposition | VWAP unknown **not** “first 30m only”; **m61–m240** buckets matter — see `unknown_regime/*_unknown_by_minute_bucket.csv` |
| VWAP holdout | **2023→2024:** train-threshold **top80** **underperforms** test all on total R (`holdout/vwap_quality_holdout_results.csv`) |
| VWAP trade #2 | **Positive** in **2023** and **2024** (`holdout/vwap_trade_number_stability.md`) |
| Indicator mtp 2/3 | **Trade #2 ~+28.6R** / 498; **trade #3 ~+7.35R** / 241; total R up, **avg R down** (`indicator_mtp_diagnostics/indicator_mtp_comparison.csv`) |
| Exit/slip overlay | Symmetric stress harsh; **target-limit** scenarios recover material R (`exit_slip/exit_slip_scenario_comparison.csv`) |
| Quality score v1.5 | VWAP **2023→2024** top80 still weak (`quality_score_v15/vwap_threshold_holdout_v15.csv`); indicator top80 still worse than all |
| Router readiness | **`NEED_MORE_TRADE_ENRICHMENT`** (`router_readiness_decision_v15.md`) |

## F. Explicit non-runs

mini-WFO; full WFO; live/paper; SPY; Global L1 rerun; large Global L2 grids; `--use-signal-cache` on unsafe roots; strategy changes; feature primitive changes; selected candidate YAML edits; hard regime filter; combiner router code; `git add .`; heavy artifact commits

## G. Risks / caveats

In-sample QQQ 2023–2024; long-only; enriched joins on bar timestamps; holdout is **diagnostic** not WFO; target-limit attribution is **research overlay**; indicator higher **mtp** raises turnover risk; `regime_unknown` labels still ambiguous

## H. Recommended next step

**Exactly one:** **`NEED_MORE_TRADE_ENRICHMENT`**
