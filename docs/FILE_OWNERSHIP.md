# File ownership (mainline)

| Area | Owns |
|------|------|
| `src/execution/path.py` | Reference bar-path simulation and PnL |
| `src/backtest/engine.py` | Signal validation → `TradeIntent` → `simulate_trade_path` |
| `src/backtest/sweep*.py` | Layer 1 grid orchestration and artifacts |
| `src/backtest/strategy_runner.py` | Bars → features → signals (no PnL) |
| `src/combiner/reference_simulator.py` | Numba Layer 2 reference (legacy semantics) |
| `src/combiner/bar_arrays.py` | OHLCV → ndarray dict for precompute |
