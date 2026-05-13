# Layer flow (Layer 1 / 2 / 3) — architecture reset

**Date:** 2026-05-11

This document ties **research layers** to **module ownership** after the execution reset. Machine-readable rows: `docs/LAYER_FLOW.csv`.

## Layer 1 — Candidate factory

**Purpose:** Per-strategy parameter exploration and candidate library construction.

**Pipeline (mainline target):**

1. Load validated bars (`src/data`).
2. Build no-lookahead features (`src/features`).
3. Load strategy; generate raw signals aligned to the standard signal contract (`src/strategies`, `docs/SIGNAL_CONTRACT.md`).
4. **`run_strategy_backtest`** (`src/backtest/engine.py`) maps rows → `TradeIntent` → **`simulate_trade_path`** (`src/execution/path.py`).
5. Aggregate metrics (`src/backtest/metrics.py`); emit configs / YAML / metadata for Layer 2.

**Current status:** Layer 1 is the **mainline** path: `read_bars` → `strategy_runner` → `run_strategy_backtest` → `simulate_trade_path` → `metrics`. Testing YAMLs under **`src/strategies/testing_parameters/`** resolve **`fixed:`** then **`grid:`** into one flat override map per combo (overlap between fixed and grid keys is an error; **`params_json`** in sweep rows carries the merged map). **`risk.min_risk_per_share`** and max-trades aliases are read into **`BacktestConfig`** and threaded into **`default_intraday_policy`** for Layer1 runs. Real-symbol sweeps with **`--output-root`** support **checkpoint/resume** (`sweep_results_partial.csv`, `sweep_progress.json`, `--checkpoint-every`, `--resume`) and **per-combo timing** columns on results. Parameter sweep and CLI live in **`src/backtest/sweep.py`** (synthetic `--smoke`, real-symbol sweep, `--validate-pipeline`; **`python -m src.backtest.sweep`** invokes **`main()`**). **Controlled rebuild design** lives under **`src/research/results/layer1_execution_backed_controlled/`** (minimal proof runs + **`fast_path_numba_readiness`** design). **Promotion / validation** (no sweep inside): **`python -m src.research.run_layer1_execution_backed_controlled`**. **Runtime candidate root** for selected Layer1 YAMLs: **`src/strategies/testing_parameters_results/l1_execution_backed_controlled/`** (flat `*.yaml` only; combiner **`load_candidates`**). Contract-alignment audit: **`src/research/results/layer1_config_candidate_contract_alignment/`**. Historical Numba sweep code is under **`archive/legacy_backtest/`** (not a mainline import).

**Future acceleration:** Numba only under `src.execution.fast_path` **after** parity tests vs `simulate_trade_path` — never a second PnL definition in `backtest.fast`.

**Must not:** Own fill/PnL semantics outside `src/execution`.

## Layer 2 — Combiner / candidate competition

**Purpose:** When multiple candidates can fire, choose one under guards (priority, cooldown, daily loss, max trades).

**Pipeline (mainline target):**

1. Load candidate configs / precomputed signal matrices (`precompute`, `signal_cache`) — **cache only**, no accounting.
2. `combiner.selection` — deterministic arbitration.
3. `combiner.state` — day/session guards.
4. (Future) router adjusts allowed / priority / `management_mode`.
5. Build `TradeIntent` → **`simulate_trade_path`** → aggregate `TradeResult`.

**Current status:** Mainline Layer 2 has **two simulation engines**, selectable at CLI / API via `normalize_combiner_engine_label`:

- **`legacy_reference` (default token `legacy`):** lazy-loads the archived Numba reference under ``archive/legacy_combiner/reference_simulator.py`` (``simulate_combiner_numba`` / ``simulate_combiner_legacy_logs``). Owns **legacy** accounting only.
- **`execution_backed` (alias `canonical`):** ``simulate_combiner_canonical`` / ``simulate_combiner_execution_backed`` in ``src/combiner/adapter.py`` walks bars sequentially, uses ``selection`` / ``state`` for coarse guards, builds :class:`src.execution.types.TradeIntent`, and calls :func:`src.execution.path.simulate_trade_path` per selected trade. **Hardening:** next-bar entry requires the same ``session_date`` on signal and entry bars; ``reset_day`` clears loss cooldown when the session calendar day changes; ``ExecutionPolicy.min_risk_per_share`` is populated from combiner config + candidate floor and enforced during materialization.

Synthetic parity and drift notes: ``src/research/results/combiner_adapter_parity/parity/`` (toy matrix: legacy vs execution-backed is **not** an exact match — documented). **Real QQQ slice (Jan 2024)** dual-engine smoke + metrics use repo-local bars under ``data/raw/ibkr/`` (committed intentionally as a small reproducible dataset; see ``combiner_adapter_parity`` smoke + ``real_data_parity_*`` files).

**Must not:** Implement independent intrabar fill/exit/PnL in combiner selection code.

## Layer 3 — Fixed profile / OOW / WFO validation

**Purpose:** Evaluate **frozen** systems across calendar windows (smoke, OOW, full WFO when enabled).

**Pipeline (mainline target):**

1. Load frozen Layer 2 + policy + semantics version stamps.
2. Walkforward harness (`src/walkforward`) orchestrates runs; each trade path should go through **`simulate_trade_path`** when Layer 2 uses the **execution_backed** engine.

**Current status:** Harnesses (`runner.py`, `fixed_system.py`, `folds.py`) call **`src.combiner.run.run_combiner_fixed_config`**. Default engine may still be **`legacy_reference`** in some callers for backward compatibility; **imports are not blocked** by `NotImplementedError`. Repo-local **execution_backed** real smoke on QQQ is **green** (`combiner_adapter_parity/smoke/`). Layer 3 full dry-runs were **not** executed in this task (no mini-WFO).

**Must not:** Tune parameters inside fixed OOW checks; must not own trade accounting.

## research/

Thin runners and curated aggregates only; no canonical accounting. **Exit overlay (execution path):** ``src/research/run_exit_overlay_execution_path.py`` replays baseline ``simulate_combiner_canonical`` trades with modified ``ExitPlan`` / ``TradeIntent`` via ``simulate_trade_path`` only (see ``src/research/results/exit_overlay_execution_path/``).

## portfolio/

Sizing, daily risk, equity curve — **after** per-trade results from execution; does not redefine fill/PnL.
