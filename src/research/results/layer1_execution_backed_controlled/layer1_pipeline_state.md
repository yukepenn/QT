# Layer1 pipeline state (design snapshot)

**Date:** 2026-05-11

## Confirmed architecture

1. **Accounting ownership:** Only **`src/execution/`** (especially **`materialize_trade_levels`** + **`simulate_trade_path`**) defines fills, stops, targets, max-hold, EOD, scale-out, and R/PnL. **`src/backtest/engine.py`** is a thin adapter: signals → **`TradeIntent`** → **`simulate_trade_path`** → flatten → **`summarize_trades`**.

2. **Layer1 does not own PnL:** **`strategy_runner`** builds features and **`sig_*`** frames only. **`strategies/*`** emit signals, not executed legs.

3. **No hidden PnL in features:** **`build_features_from_config`** produces indicators and structure columns only.

4. **`fast_path.py`:** Not a second truth — acceleration only after parity vs **`simulate_trade_path`** (per **`execution_backed_hardening/fast_path_acceleration_plan.md`**).

## Sweep CLI nuance

- **`src/backtest/sweep.py`** sets **`ENGINE_LABEL = "reference"`** on result rows. That label means **mainline reference implementation** wired to **`simulate_trade_path`**, not the combiner’s **`legacy_reference`** Numba engine.
- For **candidate YAML / research lineage**, prefer stamping **`execution_engine: execution_backed`** (or `mainline_path`) to align vocabulary with Layer2 **`execution_backed`** — document in artifacts, even if the sweep CSV column stays `reference` until a small CLI rename.

## Machine-readable map

See **`layer1_pipeline_state.csv`**.
