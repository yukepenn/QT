## Hardening Audit Plan (P0/P1/P2/P3) — Pre–Layer 3

- **Branch**: `main`
- **Remote**: `origin` configured (`https://github.com/yukepenn/QT`)
- **Current HEAD**: verify with **`git log -1`** on `main` after pulling. Commit **E** closeout bundle: **`a37cca4`** *Document hardening closeout and rerun plan* (+ small hash-pointer commits may follow). **Commit D** `75bb620`; **Commit C** `a1b995f`.
- **Working tree**: clean (`git status --short` is empty)
- **Python**: 3.11.4

### Data status (current, confirmed)

- **QQQ (RTH 1-min)**: usable for 2020-01-01 → 2026-04-30
  - coverage artifacts: `src/research/results/data_backfill_spy_qqq_2020_20260430/`
  - summary shows: ~617,160 rows, ~1,588 sessions, duplicates dropped by `read_bars`: 0
- **SPY**: incomplete (many missing months) → **do not use for robustness yet**
- **Raw data policy**: `data/raw/` is ignored and must remain immutable (never modify raw parquet; never commit it)

---

## Issues confirmed present (from Phase 0 inspection)

Reference: `src/research/results/hardening_audit_20260505.md`

### P0 (execution correctness)

**Status:** Commit A (P0) completed at `6bc1c7c`:

- drawdown baseline starts at 0 (pandas + numba)
- stop-side correctness enforced before risk computation
- fixed_r / fixed_price target validation enforced + finite price checks
- combiner cooldown resets at session boundary
- fast combiner emits real `daily_trade_number`
- combiner explicitly guards `max_open_positions != 1`
- opposite-direction conflicts separated from lower-priority conflicts (rejection reasons + counts)

**Remaining P0 follow-ups (still worth hardening):**

- legacy/detailed combiner path parity: ensure `simulate_combiner_legacy_logs` has the same entry validation + rejection reason codes as the fast path (avoid drift)
- centralized “shared config validation” across Layer 1 engine / Layer 1 sweep / Layer 2 precompute (avoid scattered, inconsistent validation)

### P1 (no-lookahead + cache)

- lookahead footguns exist (`session_high/low/close` are full-session aggregates)
- ORB levels are broadcast; safe only if explicitly gated
- feature_key/cache duplicated & incomplete across backtest sweep + combiner precompute
- per-strategy `context_key` must be audited for params used inside `prepare_signal_context`

### P2 (strategy validation + hidden behavior)

- `gap_acceptance_failure` is effectively long-only; should validate unsupported sides
- `prior_day_level_trap` is effectively prior-day-low long trap; should validate unsupported levels/sides
- `afternoon_continuation` includes `features.midday_window` (currently appears unused / fake uniqueness)
- rolling helper inclusive/prior semantics need clarification/aliases to avoid accidental lookahead

### P3 (diagnostics)

**Status:** Commit D implemented (behavior-level dedupe, cost-as-R, R distribution, daily/period breakdowns, leaderboards).

- Config-level **`top_unique_systems.*`** remains for backward compatibility; **`behavior_unique_systems.*`** dedupes on trade-sequence hashes from detailed **`trades.csv`**.
- Pre-hardening Layer 1/Layer 2 **saved CSV rankings remain stale** until intentional reruns.

---

## Files to edit (planned)

### Backtest / execution

- `src/backtest/metrics.py` (drawdown baseline; extend metrics later)
- `src/backtest/fast.py` (drawdown baseline; execution validation in fast path)
- `src/backtest/engine.py` (execution validation in readable path)
- `src/backtest/sweep.py` (call validations; feature_key refactor later)

### Combiner

- `src/combiner/simulator.py` (validation, cooldown scope, daily_trade_number, rejection reasons)
- `src/combiner/metrics.py` (surface new rejection counts; add diagnostics later)
- `src/combiner/run.py` / `src/combiner/sweep.py` (guard `max_open_positions==1`; ensure config validation)
- `src/combiner/postprocess.py` (P3: behavior dedupe + leaderboards later)

### Features

- `src/features/levels.py` (LOOKAHEAD rename + safe intraday-so-far columns)
- `src/features/orb.py` (add *_known columns)
- `src/features/feature_config.py` (document new columns)
- `src/features/build_features.py` (wire centralized build config)
- **new** `src/features/feature_key.py` (FeatureBuildConfig + key + build helpers)

### Strategies

- `src/strategies/strategy/base.py` (add `validate_config()` hook)
- `src/strategies/strategy/fast_utils.py` (aliases/docs for rolling helper semantics)
- each of the 10 strategy plugins (add `validate_config`; audit `context_key`)
- YAMLs: `src/strategies/parameters/*.yaml`, `src/strategies/testing_parameters/*_focused.yaml` (remove/lock unsupported axes, not new strategy logic)

### Shared config validation (new)

- **new** `src/utils/config_validation.py` (or `src/config/validation.py`) for shared checks

### Tests (new)

- `tests/test_metrics_drawdown.py`
- `tests/test_execution_validation.py`
- `tests/test_combiner_execution.py`
- `tests/test_feature_no_lookahead.py`
- `tests/test_feature_key.py`
- `tests/test_strategy_config_validation.py`
- `tests/test_strategy_context_keys.py`
- `tests/test_combiner_behavior.py`
- `tests/test_cost_as_r_metrics.py`
- `tests/test_daily_metrics.py`
- optionally `pytest.ini`, `tests/README.md`

---

## Commit plan (A–E)

### Commit A — Engine correctness (P0) + core tests

**Done at `6bc1c7c`.**

### Commit B — Feature no-lookahead + feature_key hardening (P1) + tests

- Rename/mark full-session lookahead columns; add safe “so-far” intraday columns
- Add ORB *_known columns (NaN/False before after_orb)
- Add anchor_known helper if needed for broadcast anchors
- Centralize `FeatureBuildConfig` + feature_key and use across engine/sweep/combiner/research
- Add tests for no-lookahead and feature_key determinism

**Status:** Done (see new plan note `hardening_commit_b_plan.md` and unit tests under `tests/`).

### Commit C — Strategy validation + context cache correctness (P2) + tests

**Done** (see `hardening_commit_c_plan.md`).

- `BaseStrategy.validate_config()` + `src/utils/config_validation.py`
- Wired into `engine`, `sweep`, combiner `run`/`sweep`, `candidate` precompute, `check_strategy_fast_parity`, `run_layer1_focused`
- Long-only / single-level MVPs explicit; afternoon `midday_window` removed/rejected; `context_key` includes ATR/window/buffer params where needed
- Tests: `test_strategy_config_validation.py`, `test_strategy_context_keys.py`

### Commit D — Combiner/postprocess diagnostics (P3) + tests

**Done** (see `hardening_commit_d_plan.md`).

- `src/combiner/behavior.py` + postprocess **`behavior_unique_*`** outputs
- `src/backtest/metrics.py` — `profit_factor_r`, cost-as-R, daily + `period_breakdown`
- `src/combiner/metrics.py` — execution cost wiring, daily_trade_number JSON, rejection counts
- `postprocess.py` — period CSVs, rank leaderboards, cost-robust filter, fixed vs sweep comparison
- Tests: `test_combiner_behavior.py`, `test_cost_as_r_metrics.py`, `test_daily_metrics.py`, `test_combiner_postprocess.py`

### Commit E — Consolidation + docs/closeout

**Done** (documentation and markers only; no research reruns).

- `hardening_status_current.md`, `hardening_closeout_20260505.md`, `hardening_validation_20260505.md`, `rerun_plan_after_hardening.md`
- `tests/README.md`; `PRE_HARDENING_STALE.md` on pre-hardening Layer 1/2 roots; README hardening section
- Light validation recorded in `hardening_validation_20260505.md`

---

## Next action to start implementation safely

1. **User approval** for **`rerun_plan_after_hardening.md`** (post-hardening Layer 1 / Layer 2).
2. Old Layer 1/Layer 2 rankings remain **stale** until that rerun completes.

