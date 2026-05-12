# Mainline `src/` summary (post-cleanup)

| Folder | Role |
|--------|------|
| `backtest/` | Reference adapter (`engine`, `metrics`), sweep modules, `strategy_runner`, `signal_adapter`, `config`, `constants` |
| `combiner/` | Selection/state/precompute; `reference_simulator` + `bar_arrays`; `run.py` CLI |
| `execution/` | Types, policy, path simulator, validators (incl. `validate_trade_setup`) |
| `strategies/` | Loader + strategy plugins (import `TM_*` from `backtest.constants`) |
| `features/`, `data/`, `walkforward/`, etc. | Unchanged roles per `docs/ARCHITECTURE.md` |
