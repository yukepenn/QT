# Baseline inventory — Layer1 config / candidate contract alignment

**Pre-work git tip:** `afc4461`  
**Prior handoff intent:** `RUN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD` — this task inserts a **contract alignment** pass before that run.

## Runtime vs research

- **Runtime truth:** strategy YAML under `src/strategies/parameters/`, testing grids under `src/strategies/testing_parameters/`, **active candidates** under `src/strategies/testing_parameters_results/l1_execution_backed_controlled/` (YAML only at promotion time).
- **Research / audit:** `src/research/results/layer1_config_candidate_contract_alignment/` and existing `layer1_execution_backed_controlled/` design docs.

## Gaps closed (summary)

| Gap | Resolution |
|-----|------------|
| `fixed` + `grid` merge | `grid_combos_from_document` returns **fixed ∪ grid** per combo; overlap → `ValueError`; `validate_testing_grid_for_strategy` uses same resolution |
| `risk.min_risk_per_share` → policy | `BacktestConfig.min_risk_per_share` + `run_strategy_backtest` passes into `default_intraday_policy` |
| `risk.max_trades_per_day` alias | `_max_trades_per_session_from_dict` precedence documented in code |
| Candidate schema | YAML uses **`strategy`**, **`config`**, **`metrics`**, **`metadata`**, **`selection`**, **`source`**, **`execution.execution_engine`** per `combiner.candidate.load_candidate_yaml` |
| Promotion | `src/research/run_layer1_execution_backed_controlled.py` — `promote` / `validate-candidates` |

## Non-runs

No real controlled sweep, no broad Layer1/Layer2/Layer3, WFO, live/paper, SPY sweeps, router, new strategy families, signal semantics edits, Archive moves, legacy delete, Numba, forbidden heavy artifacts.
