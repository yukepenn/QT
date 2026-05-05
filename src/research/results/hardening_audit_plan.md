## Hardening Audit Plan (P0/P1/P2/P3) — Pre–Layer 3

- **Branch**: `main`
- **Remote**: `origin` configured (`https://github.com/yukepenn/QT`)
- **Current HEAD**: `3c38c1b` (Feat(research): finish QQQ 2020 layer2 v2)
- **Working tree**: untracked doc(s) only (see `git status --short`)
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

- max_drawdown baseline starts at first cum value (should start at 0)
- risk uses `abs(entry-stop)` before validating correct stop side
- target validation incomplete (fixed_r target_r and fixed_price target side)
- finite price validation incomplete
- common config validation incomplete
- combiner cooldown can leak across sessions (cooldown not reset on new session)
- fast combiner `daily_trade_number` is placeholder (0)
- combiner supports only 1 open position but config exposes `max_open_positions`
- opposite-direction conflict not cleanly separated from lower-priority conflict in fast path reasons/counts

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

- postprocess “top unique” is config-level, not behavior-level
- cost-as-R diagnostics missing
- R-based PF/expectancy distribution missing
- daily_trade_number breakdown missing (also blocked by P0 daily_trade_number in fast combiner)
- monthly/quarterly breakdowns missing

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

- Add shared execution validation helpers (Python + Numba-compatible)
- Fix drawdown baseline to start from 0 in both pandas and numba
- Enforce stop-side correctness before risk/targets
- Enforce fixed_r/fixed_price target validation and finite price checks
- Combiner: reset cooldown at session boundary; implement real fast `daily_trade_number`
- Guard `max_open_positions != 1` with explicit error
- Split opposite-direction conflict vs lower-priority conflict (fast path counts + labels)
- Add tests for drawdown + validation + combiner invariants

### Commit B — Feature no-lookahead + feature_key hardening (P1) + tests

- Rename/mark full-session lookahead columns; add safe “so-far” intraday columns
- Add ORB *_known columns (NaN/False before after_orb)
- Add anchor_known helper if needed for broadcast anchors
- Centralize `FeatureBuildConfig` + feature_key and use across engine/sweep/combiner/research
- Add tests for no-lookahead and feature_key determinism

### Commit C — Strategy validation + context cache correctness (P2) + tests

- Add `BaseStrategy.validate_config()`
- Add shared config validation module and call it from engines/sweeps/combiner precompute
- Make hidden behavior explicit:
  - gap_acceptance_failure: reject unsupported sides unless implemented
  - prior_day_level_trap: reject unsupported levels/sides unless implemented
  - afternoon_continuation: remove fake uniqueness or wire param correctly (prefer explicit)
- Audit `context_key()` for every strategy vs params used inside `prepare_signal_context`
- Add tests: validate_config + context_key changes

### Commit D — Combiner/postprocess diagnostics (P3) + tests

- Behavior-level dedupe (stable behavior hash from trades)
- Cost-as-R diagnostics + R-based PF/expectancy distribution
- Daily trade number breakdown, daily/monthly/quarterly breakdowns (top systems only)
- Cost-aware leaderboards and “cost robust” filters (configurable thresholds)
- Add tests: behavior_hash + cost metrics + daily metrics

### Commit E — Consolidation + docs/closeout

- Add/standardize pytest config and tests docs
- Run light suite: `pytest`, `compileall`, loader list, small parity smoke, small combiner smoke
- Update README/PROGRESS/CHANGES and write closeout + rerun plan docs
- Document that **old Layer 1/Layer 2 outputs are pre-hardening and rankings are stale** after fixes

---

## Next action to start implementation safely

1. Commit a lightweight checkpoint including Phase 0 docs (no code changes yet), then proceed to Commit A.
2. Do not run full Layer 1/Layer 2 until all tests pass through Commit C/D and smoke checks succeed.

