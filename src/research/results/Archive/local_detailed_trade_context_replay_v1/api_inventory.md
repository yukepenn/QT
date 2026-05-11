# api_inventory — local_detailed_trade_context_replay_v1

## Goal

Build a **local-only** row-level trade-context panel for Champion v0 and commit only **aggregated** diagnostics.

## Existing APIs reused

- **Combiner replay (generates detailed trades)**:
  - `src/combiner/run.py` (CLI) writes `trades.csv` with:
    - `signal_ts_utc`, `signal_idx` (decision-time bar)
    - `entry_ts_utc`, `entry_idx` (execution is next-bar open)
    - `exit_ts_utc`, `exit_idx`
    - `candidate_id`, `strategy`, `strategy_family`, `daily_trade_number`, `exit_reason`, `bars_held`, `risk_per_share`, `r_multiple`
  - Simulator guarantee: `entry_idx = signal_idx + 1` for normal next-bar entry (see `src/combiner/simulator.py`).

- **Feature build**:
  - `src/data/read_bars.py:read_bars` → reads QQQ 1‑min bars from local parquet partitions.
  - `src/features/build_features.py:build_basic_features` → produces `ts_utc` plus regime/VWAP/ORB/levels columns.

- **No-lookahead join helpers**:
  - `src/research/trade_quality_helpers.py:merge_features_asof_backward` → `pd.merge_asof(direction="backward")`.
  - `src/research/trade_quality_helpers.py:add_prior_trade_columns` → prior-trade linkage within session.
  - Enum label maps for PA regime/trade mode/always-in:
    - `REGIME_LABEL_MAP`, `TRADE_MODE_MAP`, `ALWAYS_IN_MAP`.

- **Reference runners (patterns, not executed directly)**:
  - `src/research/fixed_profile_oow.py` (run/enrich/postprocess patterns).
  - `src/research/run_layer3_fixed_profile_smoke.py` (profile/window planning patterns).
  - `src/research/enrich_combiner_trades.py` (entry-time enrichment; this replay uses **decision-time** enrichment).

## Decision-time context rule (critical)

- Backtest: signal on completed bar \(t\), enter at next bar \(t+1\) open.
- Router/quality context must use **decision-time** information:
  - Prefer `signal_ts_utc` (from trades) as `decision_context_ts_utc`.
  - Fallback (if needed): previous completed bar before `entry_ts_utc` (approx \(entry\_ts - 1\) minute).
- All joins: **backward** `merge_asof` only (no lookahead).

## What new code is added

- `src/research/run_local_trade_context_replay.py`
  - Generates a local replay plan for Champion v0 profiles × windows.
  - Runs combiner CLI into `output_root/local_runs/**` (local-only).
  - Builds local-only row panel under `output_root/local_rows/trade_context_panel.csv` (gitignored).
  - Writes committed aggregates under `output_root/aggregates/**`.

