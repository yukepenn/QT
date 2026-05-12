# Min risk (`min_risk_per_share`) — execution contract

**Policy field:** `ExecutionPolicy.min_risk_per_share` (default `0.0`).

**Population:** `execution_policy_from_combiner_cfg(cfg, min_risk_per_share_floor=...)` sets  
`min_risk_per_share = max(float(cfg.min_risk_per_share or 0), float(floor or 0))`  
where `floor` is `min_risk_per_candidate[ci]` from Layer2 arrays (YAML/strategy min merged upstream in `run._build_execution_arrays`).

**Enforcement:** `materialize_trade_levels` rejects when materialized `risk_per_share < policy.min_risk_per_share` with **`risk_too_small`** — `simulate_trade_path` returns `ok=False` with that reason (no bar walk).

**Tests:** `tests/test_execution_backed_hardening.py` (materialize, path, `simulate_selected_trade`, policy max).
