# Architecture after combiner adapter v1

- **Layer1:** unchanged — `backtest/sweep.py` + `execution.path`.
- **Layer2:** dual engine — `legacy` (archived Numba) vs `canonical` (`adapter.simulate_combiner_canonical`).
- **Layer3:** still calls `run_combiner_fixed_config` with default `engine="legacy"` until parity harness promotes canonical.

Future hooks: router adjusts allowed strategies / priorities before selection; exit-management feeds `ExitPlan` into `simulate_trade_path` (not implemented here).
