# QQQ data availability (local parquet)

- **Symbol:** QQQ
- **First month partition:** `2020-01-01`
- **Last month partition:** `2026-04-30`
- **Inferred first date:** `2020-01-01`
- **Inferred last date:** `2026-04-30`

## Selected validation windows (clipped to data when possible)

- **early_oow** (pre-selection): `2020-01-01` → `2022-12-31` — **754** RTH sessions
- **insample_ref** (selection reference): `2023-01-01` → `2024-12-31` — **502** RTH sessions
- **late_oow** (post-selection): `2025-01-01` → `2026-04-30` — **332** RTH sessions
- **full_available** (full span (clipped to data)): `2020-01-01` → `2026-04-30` — **1588** RTH sessions

If partitions are missing, install local `data/raw/ibkr/equity/bars_1min/symbol=QQQ/year=*/month=*/data.parquet` before running combiner replays.
