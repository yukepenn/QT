# Execution policy design — controlled Layer1

**Engine path:** `run_strategy_backtest` → **`default_intraday_policy`** (unless overridden) → **`simulate_trade_path`**.

## Defaults (aligned with `src/execution/policy.py` + types)

| Parameter | Controlled Layer1 value | Notes |
|-----------|---------------------------|--------|
| Entry | **Next bar open** after signal bar (engine walks `i+1` same session) | Matches hardening mental model; same-session enforced in engine loop. |
| `same_bar_policy` | **`STOP_FIRST`** (`AmbiguityPolicy.STOP_FIRST`) | Default `ExecutionPolicy`. |
| Slippage | **`backtest.slippage_per_share`** from strategy YAML (focused grids use **0.01**) | Passed into `default_intraday_policy`. |
| Commission | **`backtest.commission_per_trade`** (typically **0.0** in grids) | Same. |
| EOD | **`eod_exit_minute`** = **389** (from YAML) | Passed to policy. |
| `min_risk_per_share` | **Gap to close in Layer1:** `default_intraday_policy` is **not** currently passed `min_risk_per_share` from `risk.min_risk_per_share` in `engine.run_strategy_backtest` | **Run task:** thread `float(cfg["risk"].get("min_risk_per_share", 0.0))` into `default_intraday_policy(...)` OR document reliance on signal-derived risk only. |
| Scale-out / trailing / NFT | **Disabled** unless explicitly in `ExitPlan` / future config | Default `exit_plan=None`. |
| Target | **`fixed_r`** via signals (`sig_target_mode`, `sig_target_r`, stops) | Strategy YAML `risk.target_mode: fixed_r`. |
| Short | **`allow_short=False`** | Long-only strategies. |

## Stamping for reproducibility

- Record **`execution_semantics_version`** from policy (sweep already captures this).
- Record **`execution_policy_hash`** in candidate YAML (new field in postprocess).
- Prefer YAML field **`execution_engine: execution_backed`** even if sweep CSV still prints `engine=reference` (see `layer1_pipeline_state.md`).

## Risk definition

Initial risk from **`materialize_trade_levels`** using signal stop + entry reference price; R-multiples from **`TradeResult`** — single accounting path in **`src/execution`**.
