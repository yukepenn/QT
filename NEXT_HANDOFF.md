# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Latest commit | **`df52f35`** — `Backtest: implement canonical sweep smoke` (full: `df52f35e9da35bb984e475f8a220eedb9260dab8`) |
| Remote | `git ls-remote origin refs/heads/main` must match local `HEAD` after push |
| Working tree | Stage curated paths only — **never** `git add .` |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | Run before handoff |
| `python -m pytest -q` | **100 passed** |
| `python -m src.strategies.loader --list` | **35** strategies |
| Import smoke (execution, management, backtest engine/metrics/sweep, combiner selection/state, router, portfolio) | `imports_ok` |
| `import src.backtest.legacy.fast_legacy` / `sweep_legacy` | `legacy_imports_ok` |
| `python -m src.backtest.sweep --help` | Canonical options + legacy first-token note |
| `python -m src.backtest.sweep --smoke` | Synthetic two-combo sweep; `engine=canonical_reference` |
| `python scripts/canonical_execution_smoke.py` | Still valid for execution-only smoke |
| Tracked-heavy check | Clean (no parquet/npy/top_runs/trades.csv in index) |

## C. Canonical sweep implementation

- **API:** `expand_param_grid`, `config_hash`, `run_canonical_sweep`, `run_single_canonical_combo`, `run_synthetic_canonical_smoke`, `canonical_sweep_main`, `main`.
- **Types:** `SweepCombo`, `SweepResult`, `CanonicalSweepConfig` (`SweepResult` includes `avg_r`, `engine=canonical_reference`, `canonical_or_legacy=canonical`, `execution_semantics_version`).
- **CLI:** Default (no args) prints help, exit **1**. `--smoke` exit **0**. `--canonical-help` exit **0**. `--data-root` without `--smoke` exit **3** (not wired). Reserved **`--config`**, **`--grid`** for future YAML/JSON.
- **Legacy:** **`main`**: if `argv[0] == "--legacy"` → `sweep_legacy.main(argv[1:])`, prints `engine=legacy_numba_fast`. No `--legacy` branch inside `canonical_sweep_main` (avoids silent empty legacy argv).

## D. Synthetic smoke result

- Two combos over `sig_target_r` ∈ {1.0, 2.0}; deterministic OHLCV + one valid long signal row.
- Schema: `docs/CANONICAL_SWEEP_RESULT_SCHEMA.md`; narrative: `docs/CANONICAL_SWEEP_SMOKE_SUMMARY.md`.
- Optional tiny writes: `--output-root` + not `--no-save` → `canonical_sweep_smoke.csv` + `canonical_sweep_meta.json`.

## E. Signal adapter status

- **`src/backtest/signal_adapter.py`:** `infer_signal_mapping`, `canonicalize_signal_frame`, `validate_canonical_signal_frame`, `assert_canonical_signal_frame`.
- **Champion-related strategies** (`pa_buy_sell_close_trend`, `gap_acceptance_failure`, `cci_extreme_snapback`): already emit standard `sig_*`; mapping table in `docs/CANONICAL_STRATEGY_INTEGRATION_PLAN.md`.

## F. Legacy sweep boundary

- **`--legacy` first token only** for Numba grid; stdout labels `engine=legacy_numba_fast`.
- **`src/backtest/fast.py`:** `TM_*` only; `__getattr__` raises toward `legacy.fast_legacy` (tests in `tests/test_legacy_surface.py`).

## G. Layer 1 / 2 / 3 status

- **Layer 1:** Canonical single-strategy + **synthetic sweep** on reference engine; real bar-backed sweep not wired.
- **Layer 2:** Combiner simulator still **legacy Numba** explicit re-export.
- **Layer 3:** Walkforward harnesses still depend on legacy combiner until execution-backed combiner exists.

## H. Explicit non-runs

No WFO, mini-WFO, live/paper, SPY, broad Layer2, Champion migration, historical sweeps, new strategies, short/scalp research, selected YAML edits, performance claims from smoke.

## I. Risks / caveats

- Real-symbol sweep still needs `read_bars` + `FeatureStore` + strategy `generate_signals` orchestration.
- `validate_testing_grid_for_strategy` / `_metrics_row` remain thin delegators to legacy for YAML compatibility only.
- Combiner / Layer3 canonical accounting still pending.

## J. Files changed (high level)

- `src/backtest/sweep.py`, `src/backtest/signal_adapter.py` (new)
- `tests/test_backtest_sweep_canonical.py`, `test_backtest_signal_adapter.py`, `test_canonical_sweep_result_schema.py`, `test_backtest_sweep_legacy_boundary.py`
- `docs/CANONICAL_SWEEP_*`, `CANONICAL_STRATEGY_INTEGRATION_PLAN.md`, `SIGNAL_CONTRACT.md`, `LAYER_FLOW.md`, `LEGACY_RESULTS_POLICY.md`, implementation plan + inventory CSV, smoke summary, result schema
- `README.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `NEXT_HANDOFF.md`

## K. Recommended next step (exactly one)

**`COMPLETE_CANONICAL_BACKTEST_SWEEP`**
