# Data folder audit — `data/`

## Summary

| Check | Value |
|--------|--------|
| Exists | **yes** |
| File count | **104** |
| Total size (MB) | **~34.26** |
| Largest file (MB) | **~0.41** (`symbol=SPY/year=2020/month=03/data.parquet`) |
| Parquet files | **104** (all files are `data.parquet` shards) |
| QQQ-related paths | **76** |
| SPY-related paths | **28** |
| Unrelated / private files | **none detected** (only `data/raw/ibkr/equity/bars_1min/symbol={QQQ,SPY}/...`) |
| Safe to commit | **yes** (every file < 95 MB; total size modest; content is reproducible bar data only) |

## Detail

Per-file listing: `data_folder_audit.csv` (104 rows). One-line rollup: `data_folder_audit_summary.csv`.

## Policy

`data/cache/` remains git-ignored. Only `data/raw/ibkr/**/*.parquet` is force-included via `.gitignore` negation after the global `*.parquet` rule.
