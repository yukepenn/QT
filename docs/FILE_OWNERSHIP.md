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
| `src/combiner/precompute.py` | Signal-matrix prep; includes `prepare_backtest_arrays` |
| `src/combiner/simulator.py` | Constants + stub entry points (mainline accounting pending) |
| `archive/legacy_combiner/reference_simulator.py` | Historical Numba Layer 2 reference |
