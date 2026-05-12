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
| `min_risk_per_share` | **`risk.min_risk_per_share`** (fallback **`backtest.min_risk_per_share`**) → **`BacktestConfig.min_risk_per_share`** → **`default_intraday_policy(..., min_risk_per_share=...)`** in `run_strategy_backtest` and sweep policy construction | Enforced in **`materialize_trade_levels`** (`risk_too_small`) alongside signal risk. |
| Scale-out / trailing / NFT | **Disabled** unless explicitly in `ExitPlan` / future config | Default `exit_plan=None`. |
| Target | **`fixed_r`** via signals (`sig_target_mode`, `sig_target_r`, stops) | Strategy YAML `risk.target_mode: fixed_r`. |
| Short | **`allow_short=False`** | Long-only strategies. |
| **Max trades / session** | **`backtest.max_trades_per_session`** > **`backtest.max_trades_per_day`** > **`risk.max_trades_per_session`** > **`risk.max_trades_per_day`** > default **1** | Implemented in **`_max_trades_per_session_from_dict`**. |

## Stamping for reproducibility

- Record **`execution_semantics_version`** from policy (sweep already captures this).
- Record **`execution_policy_hash`** in candidate YAML (new field in postprocess).
- Promotion YAML uses top-level **`execution.execution_engine: execution_backed`**; sweep CSV may still print `engine=reference` (see `layer1_pipeline_state.md`).

## Risk definition

Initial risk from **`materialize_trade_levels`** using signal stop + entry reference price; R-multiples from **`TradeResult`** — single accounting path in **`src/execution`**.
