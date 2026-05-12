# File ownership (mainline)

| Area | Owns |
|------|------|
| `src/execution/path.py` | Reference bar-path simulation and PnL |
| `src/execution/types.py` | `TradeIntent`, `TradeResult`, execution policy types, `TM_*` int8 signal labels |
| `src/execution/validators.py` | `validate_trade_setup` and related helpers |
| `src/backtest/engine.py` | `BacktestConfig`; signal validation → `TradeIntent` → `simulate_trade_path` |
| `src/backtest/sweep.py` | Layer 1 grid orchestration, synthetic/real sweep loops, CLI, sweep artifacts |
| `src/backtest/strategy_runner.py` | Bars → features → signals; YAML/grid merge helpers; `FeatureFrameCache`; `validate_pipeline` |
| `src/backtest/signal_adapter.py` | Standard `sig_*` column mapping and validation |
| `src/backtest/metrics.py` | Trade-table summaries for Layer 1 |
| `src/combiner/adapter.py` | Execution-backed sequential Layer2 loop → `simulate_trade_path` |
| `src/combiner/trade_intent_adapter.py` | `TradeIntent` construction + `TradeResult` → trade row (stamps `engine`, semantics versions) |
| `src/combiner/simulator.py` | `CombinerConfig`, rejection/exit constants; lazy `legacy_reference` + `simulate_combiner_canonical` / `simulate_combiner_execution_backed`; `normalize_combiner_engine_label` |
| `archive/legacy_combiner/reference_simulator.py` | Historical Numba Layer 2 reference |
