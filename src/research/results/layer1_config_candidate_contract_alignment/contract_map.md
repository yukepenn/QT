# Contract map — YAML → runtime consumers

Machine-readable rows: **`contract_map.csv`**.

**Principle:** `src/execution/` is the only fill / risk / stop / target / exit / PnL / R truth. Strategies emit **`sig_*`**; **`risk.min_risk_per_share`** now reaches **`ExecutionPolicy`** for Layer1 backtests via **`BacktestConfig`**.
