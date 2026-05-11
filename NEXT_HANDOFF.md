# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Latest commit before this work | `4c77f4c` — Docs(handoff): avoid stale tip SHA in table |
| New commit | **Research: add trade quality router diagnostics** — verify tip with `git log -1 --oneline` |
| Push status | Run `git push`; then confirm **Pushed** `main` → `origin` |
| Working tree | Tracked files clean after commit; **expected untracked:** `src/research/results/trade_quality_router_v1/local_runs/**`, `src/research/results/trade_quality_router_v1/enriched_trades/*_enriched.csv`, `src/research/results/trade_quality_router_v1/quality_score/scored_trades_*.csv`, `src/combiner/results/layer2_qqq_global_2023_2024_v2_cost_turnover/**`, other pre-existing heavy diagnostics |
| Expected untracked local-only artifacts | Regenerated combiner `trades.csv` under `trade_quality_router_v1/local_runs/`; do **not** `git add` these |

## B. Task scope

| | |
|--|--|
| Requested | Trade-level regime/context enrichment + setup taxonomy + offline trade-quality analysis for Global L2 systems (no trading logic changes) |
| Completed | `enrich_combiner_trades.py`, `analyze_trade_quality.py`, `score_trade_quality_offline.py`, `trade_quality_helpers.py`; tests ×3; curated `trade_quality_router_v1/` (analysis buckets, quality score thresholds, taxonomy, design + summary); diag YAMLs for lower-turnover VWAP + indicator @ mtp=1 |
| Intentionally not done | Combiner `regime_router` implementation; hard regime filter; mini/full WFO; live/paper; SPY; strategy/feature primitives; candidate YAML edits; committing raw trades / enriched rows / scored rows / sweep / top_runs |

## C. Files changed

| Area | Paths |
|------|--------|
| Scripts | `src/research/enrich_combiner_trades.py`, `src/research/analyze_trade_quality.py`, `src/research/score_trade_quality_offline.py`, `src/research/trade_quality_helpers.py` |
| Tests | `tests/test_enrich_combiner_trades.py`, `tests/test_analyze_trade_quality.py`, `tests/test_score_trade_quality_offline.py` |
| Curated research results | `src/research/results/trade_quality_router_v1/**` except local-only paths below |
| Docs / indexes | `src/research/results/RESULTS_INDEX.md`, `src/combiner/results/RESULTS_INDEX.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `NEXT_HANDOFF.md` |
| Local-only heavy | `trade_quality_router_v1/local_runs/`, `enriched_trades/*_enriched.csv`, `quality_score/scored_trades_*.csv` |

## D. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `pytest -q` | **390** passed |
| `python -m src.strategies.loader --list` | **35** strategies |
| New tests | `test_enrich_combiner_trades`, `test_analyze_trade_quality`, `test_score_trade_quality_offline` |
| Tracked-heavy check | Run `git ls-files \| Select-String -Pattern "top_runs|trades.csv|compact_trades|\.parquet"` — expect **no** matches |

## E. Manifest / local inventory

- **git tip:** verify `git log -1 --oneline`
- **Result roots:** `layer2_qqq_global_2023_2024_v2/`, `trade_quality_router_v1/`
- **Local sweep/top_runs:** `layer2_qqq_global_2023_2024_v2_cost_turnover/` (untracked typical)
- **Trades:** regenerated for three systems; paths under `trade_quality_router_v1/local_runs/run_*` (machine-specific timestamps)
- **Missing files:** none for curated docs; raw trades absent from git by policy
- **Paste to ChatGPT (if external review):** `src/research/results/trade_quality_router_v1/trade_quality_router_v1_summary.md`, `regime_router_design_from_evidence_v1.md`

## F. Research results

| Topic | Finding |
|--------|---------|
| Systems | VWAP baseline, VWAP lower-turnover, indicator five-pack @ **mtp=1** (502 trades — matches tuned comparison) |
| Enriched trade counts | 337 / 294 / 502 (local regenerations) |
| Profitable / unprofitable regimes | No single regime owns all edge; `late_trend_climax` frequent; `trading_range` + `regime_unknown` remain important positive contributors in replays |
| Trade #2 (VWAP mtp=2) | Bucket **#2** **+5.5R** aggregate (43 trades) — not harmful in-sample |
| Same-family repeat / prior outcome | Small second-trade cohorts — interpret cautiously |
| Cost / slip | Symmetric proxy documented; combiner uses single slip for all exits — limitation |
| Quality score thresholds | VWAP: **top 80%** by score improves total R / DD proxy; indicator: **no** improvement; **`score_ge_60`** on VWAP very small **n** |
| max_trades_per_day 3/5 | **No** evidence; indicator diagnostics used **mtp=1** to match economics |
| Router design decision | **`NEED_MORE_TRADE_ENRICHMENT`** |

## G. Explicit non-runs

mini-WFO; full WFO; live/paper; SPY; Global L1 rerun; large L2 grids; `--use-signal-cache` on unsafe roots; strategy changes; feature primitive additions; selected candidate YAML edits; hard regime filter; combiner router code; `git add .`; heavy artifact commits

## H. Risks / caveats

In-sample QQQ 2023–2024; long-only; enrichment join on bar close timestamps; optional columns may be missing; `regime_unknown` bucket large; offline score **not** proven predictive; indicator replay **requires mtp=1** to match published **502**-trade economics (mtp=2 → ~1000 trades).

## I. Recommended next step

**Exactly one:** **`NEED_MORE_TRADE_ENRICHMENT`**
