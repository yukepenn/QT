# Implementation summary — Layer1 config / candidate contract alignment

See **`implementation_summary.csv`**.

Key code paths:

- **`src/backtest/strategy_runner.py`:** `normalize_override_mapping`, `grid_combos_from_document`, `validate_testing_grid_for_strategy`.
- **`src/backtest/engine.py`:** `BacktestConfig.min_risk_per_share`, `_max_trades_per_session_from_dict`, `_bt_cfg_from_dict`, policy wiring in `run_strategy_backtest`.
- **`src/backtest/sweep.py`:** policy construction passes `min_risk_per_share`.
- **`src/strategies/loader.py`:** `grid_size` delegates to `grid_combos_from_document`.
- **`src/research/run_layer1_execution_backed_controlled.py`:** thin promotion + validation CLI.
