# Commit D — Combiner/postprocess diagnostics (implementation record)

## HEAD

`75bb620` — Add behavior dedupe and cost-aware diagnostics (pushed to `main`).

## Files touched

- `src/combiner/behavior.py` — stable `behavior_hash_from_trades`, summaries, `dedupe_behavior_rows`
- `src/backtest/metrics.py` — `profit_factor_r`, cost-as-R, `summarize_daily`, `period_breakdown`, extended `summarize_trades`
- `src/combiner/metrics.py` — `execution_config_from_parts`, `summarize_combiner(..., execution_config=)`, daily_trade_number + family/candidate JSON, rejection counters
- `src/combiner/run.py`, `src/combiner/sweep.py` — pass execution into `summarize_combiner`
- `src/combiner/postprocess.py` — period CSV writer, behavior-unique outputs, rank leaderboards, cost-robust filter, fixed vs sweep comparison, CLI flags
- `tests/test_combiner_behavior.py`, `tests/test_cost_as_r_metrics.py`, `tests/test_daily_metrics.py`, `tests/test_combiner_postprocess.py`

## Tests run

- `python -m pytest -q` (full suite)
- `python -m compileall -q src`
- Smoke: `loader --list`, `read_bars`, `check_strategy_fast_parity`, `combiner/run.py --no-save` (short window)

## Caveats

- **Behavior dedupe** needs detailed **`top_runs/rank_*/trades.csv`** matched via **`top_unique_run_map.csv`**; sweep rows without detailed reruns are skipped for behavior CSVs.
- **`behavior_hash_quality`** can be **weak** if id/entry/exit columns are missing — check `behavior_unique_systems.md`.
- **Cost-robust** filters are **research thresholds**, not live-trading approval; if **`cost_stress_results.csv`** is missing, robust tables are empty with an explanatory note.
- **SPY** data incomplete; **Layer 3** not built; historical Layer 1/Layer 2 **artifacts remain stale** until rerun after hardening.

## Next

Commit E — consolidation, closeout docs, post-hardening rerun plan.
