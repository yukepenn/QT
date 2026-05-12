# Decision — Layer1 config / candidate contract alignment

## Label (exactly one)

**`RUN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`**

## Rationale

- **Fixed/grid merge** is unified for validation and sweep; overlap is explicit `ValueError`; **`params_json`** in sweeps reflects resolved overrides once combos include fixed.
- **`risk.min_risk_per_share`** threads to **`ExecutionPolicy`** via **`BacktestConfig`** and sweep policy construction.
- **Max-trades aliases** (`risk.max_trades_per_day`, etc.) resolve with documented precedence.
- **Candidate YAML** matches **`load_candidate_yaml`** (`strategy`, `config`, `metrics`, `metadata`, `selection`, `source`, `execution.execution_engine=execution_backed`).
- **Active root** `src/strategies/testing_parameters_results/l1_execution_backed_controlled/` exists with README; promotion script has **temp-dir** tests and **`--write`** is opt-in.
- **No real sweep** was executed in this task.

## Recommended next step

**`RUN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`**

## Non-runs

No real controlled Layer1 sweep, no Layer2/3, WFO, live/paper, SPY, router, new strategies, semantics edits, Archive moves, legacy delete, Numba, heavy artifacts.
