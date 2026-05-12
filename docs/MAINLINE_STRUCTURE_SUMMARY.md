# Mainline `src/` summary (structure consolidation)

| Folder | Role |
|--------|------|
| `backtest/` | Six modules only: `engine` (adapter + `BacktestConfig`), `sweep` (CLI + loops + IO), `strategy_runner` (pipeline + grid YAML), `signal_adapter`, `metrics`, `__init__` |
| `combiner/` | Selection/state/precompute/signal_cache; `simulator` stub; `run`/`sweep`/`metrics` (Layer 2 wiring; some extra modules remain for a follow-up trim); archived Numba in `archive/legacy_combiner/` |
| `execution/` | Types (incl. `TM_*`), policy, path simulator, validators (single source for `validate_trade_setup`) |
| `strategies/` | Loader + strategy plugins (`TM_*` from `execution.types`) |
| `features/`, `data/`, `walkforward/`, etc. | Unchanged roles per `docs/ARCHITECTURE.md` |
