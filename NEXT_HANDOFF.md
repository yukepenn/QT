# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Tip of `main` | After `git pull --ff-only`, run `git log -1 --oneline` (this handoff may add one feature commit). |
| Feature commit | **`Backtest: wire canonical real-symbol sweep connector`** |
| Remote | `git ls-remote origin refs/heads/main` must match local `HEAD` after push |
| Working tree | Stage curated paths only — **never** `git add .` |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | Run before handoff |
| `python -m pytest -q` | **115 passed** |
| `python -m src.strategies.loader --list` | **35** strategies |
| Import smoke (incl. `signal_adapter`, `strategy_runner`) | `imports_ok` |
| `python -m src.backtest.sweep --smoke` | OK |
| `python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend` | JSON report, exit 0 |
| Tracked-heavy check | Clean |

## C. Canonical real-symbol sweep connector

- **Module:** `src/backtest/strategy_runner.py` — load/merge config, grid flattening, `build_features_for_strategy`, `generate_strategy_signals`, `prepare_canonical_signals`, `validate_canonical_pipeline`.
- **Sweep:** `run_canonical_real_symbol_sweep`, `run_single_canonical_from_signals`, `_write_real_sweep_artifacts`, `_git_sha`.
- **CLI:** `--validate-pipeline`, `--dry-run`, `--asset`, full real-symbol set; isolated `--data-root` without other real args → exit **3** with stderr guidance.

## D. Synthetic smoke

- Unchanged: `--smoke`, `run_synthetic_canonical_smoke`, `expand_param_grid`, `config_hash`.

## E. Real-data path

- Uses `read_bars` + `build_features_from_config` + `generate_signals` + `assert_canonical_signal_frame` + `run_strategy_backtest`.
- Requires local IBKR-style parquet tree for the requested window; empty bars → clear `ValueError` / CLI exit **4**.

## F. Strategy integration

- **`docs/CANONICAL_STRATEGY_INTEGRATION_STATUS.csv`** — Champion trio + `orb_continuation` used in CI monkeypatch tests.
- Identity `sig_*` mapping for PA / GAP / CCI; optional `output_contract` still sparse in metadata.

## G. Result schema / manifest

- **`SweepResult`:** `asset`, `data_source`, `feature_config_hash`, `signal_contract_version`.
- **Artifacts:** `canonical_sweep_results.csv`, `canonical_sweep_summary.md`, `run_manifest.json` (see `docs/CANONICAL_SWEEP_RESULT_SCHEMA.md`).

## H. Legacy boundary

- **`--legacy`** argv[0] only → `sweep_legacy`; canonical path never imports `fast_legacy` for accounting.
- **`src/backtest/fast.py`:** unchanged TM-only surface.

## I. Layer 1 / 2 / 3

- **Layer 1:** Synthetic + real-symbol MVP on reference engine; FeatureStore reuse across combos not wired.
- **Layer 2 / 3:** Still legacy-combiner-backed for accounting.

## J. Explicit non-runs

No WFO, mini-WFO, live/paper, SPY research, broad Layer2, Champion migration claims, historical broad sweeps, new strategies, short/scalp research, performance claims from default outputs.

## K. Risks / caveats

- Full `build_features_from_config` per combo is correct but may be slow for large grids.
- Local parquet layout must match `read_bars` expectations.
- `run_manifest.json` `command` embeds local argv (may include paths).

## L. Recommended next step (exactly one)

**`COMPLETE_CANONICAL_BACKTEST_SWEEP`**
