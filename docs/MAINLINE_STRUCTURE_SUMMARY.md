# Mainline `src/` summary (structure consolidation)

| Folder | Role |
|--------|------|
| `backtest/` | Six modules only: `engine` (adapter + `BacktestConfig`), `sweep` (CLI + loops + IO), `strategy_runner` (pipeline + grid YAML), `signal_adapter`, `metrics`, `__init__` |
| `combiner/` | `simulator` (lazy legacy + canonical), `adapter` + `trade_intent_adapter` (execution-backed path), `run`/`sweep` (`--engine legacy|canonical`), precompute/selection/state/metrics; extra modules remain for follow-up |
| `execution/` | Types (incl. `TM_*`), policy, path simulator, validators (single source for `validate_trade_setup`) |
| `strategies/` | Loader + strategy plugins (`TM_*` from `execution.types`) |
| `features/`, `data/`, `walkforward/`, etc. | Unchanged roles per `docs/ARCHITECTURE.md` |
