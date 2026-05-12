# Fast path (Numba) design

- **Reference truth:** `src/execution/path.py` (`simulate_trade_path`).
- **Accelerated target:** `src/execution/fast_path.py` (not implemented yet).
- **Rules:** no duplicate PnL rules in `backtest/`; parity tests required before trusting Numba; unsupported management (partial exits, trailing, shorts, targetless) must fall back to reference or error explicitly.
- **Sweep:** optional future `engine_mode` (`reference` | `fast_if_supported` | `fast_strict`); default stays `reference`.
