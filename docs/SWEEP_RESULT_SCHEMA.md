# Canonical sweep result schema

**Date:** 2026-05-11

Rows are produced by `run_canonical_sweep` / `run_synthetic_canonical_smoke` as a flat `pandas.DataFrame` (from `SweepResult.__dict__`).

## Canonical fields

| Column | Type | Description |
|--------|------|-------------|
| `combo_id` | str | Stable id (`combo_0000`, …) |
| `strategy` | str | Strategy label (smoke: `synthetic_smoke`) |
| `symbol` | str | Symbol label |
| `start` | str | Window start (label; smoke default `2024-01-02`) |
| `end` | str | Window end (label) |
| `config_hash` | str | Short SHA256 of sorted JSON (`config_hash`) |
| `params_json` | str | JSON of per-combo overrides |
| `trade_count` | int | From `summarize_trades` |
| `total_r` | float | Sum of `r_multiple` |
| `total_gross_r` | float | Sum of `gross_r_multiple` when present |
| `total_net_pnl` | float | |
| `avg_r` | float | Mean `r_multiple` |
| `win_rate` | float | |
| `profit_factor_r` | float | R-based profit factor |
| `max_drawdown_r` | float | On cumulative R |
| `execution_semantics_version` | str | From `ExecutionPolicy.semantics_version` |
| `engine` | str | **`canonical_reference`** |
| `canonical_or_legacy` | str | **`canonical`** |
| `notes` | str | e.g. `synthetic_smoke`, `dry_run` |
| `asset` | str | `equity` or `futures` (passed to `read_bars`) |
| `data_source` | str | `synthetic_builtin`, `ibkr_parquet:<resolved_path>`, etc. |
| `feature_config_hash` | str | Short fingerprint of `feature_key_from_config(cfg)` (empty for synthetic-only rows) |
| `signal_contract_version` | str | e.g. `standard_sig_v1` (`STANDARD_SIGNAL_CONTRACT_VERSION`) |

## `run_manifest.json` (real-symbol runs with `--output-root`)

| Field | Description |
|--------|-------------|
| `git_sha` | `git rev-parse HEAD` when available |
| `command` | Joined argv |
| `timestamp` | UTC ISO8601 |
| `engine` | `canonical_reference` |
| `execution_semantics_version` | Policy stamp |
| `symbols` | Symbol string |
| `strategy` | Strategy id |
| `start` / `end` | NY calendar window |
| `config_path` / `grid_path` | CLI paths (may be empty) |
| `no_save` / `dry_run` | Booleans |
| `canonical_or_legacy` | `canonical` |
| `asset` | Asset class |
| `data_root` | Data directory |

Missing optional values are stored as empty strings.

When using `python -m src.backtest.sweep --legacy …`:

- Log / metadata should set `engine=legacy_numba_fast`.
- `canonical_or_legacy=legacy_prior` on any exported sweep tables (legacy truth is reference-only until parity).

Do not merge legacy and canonical CSVs without these columns.
