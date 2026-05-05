# Equity data coverage

## Backfill run status (automated)

- A full pull was started: `SPY` + `QQQ`, **2020-01-01 → 2026-04-30**, `--rth`, `TRADES`, `--chunk-days 5`, `--sleep 1.0`, `127.0.0.1:4002`.
- **Run aborted** mid-`SPY` (around **chunk 165/464**, Mar–Apr 2022) with **Socket disconnect**, then **Connection refused** on reconnect (IB Gateway/TWS likely closed or port blocked). **`QQQ` was not started** in that run.
- **Partial `SPY` parquet** from this session was merged incrementally; **`QQQ`** on disk may be **smoke-only** (e.g. 2026-04) until you rerun the full command with Gateway stable.
- **Rerun** (safe to upsert/dedupe per month):  
  `python src/data/pull_ibkr_1min.py --asset equity --symbols SPY QQQ --start 2020-01-01 --end 2026-04-30 --rth --chunk-days 5 --sleep 1.0 --client-id 101`  
  Reconnect logic in `pull_ibkr_1min.py` now retries with backoff (see `ensure_ib_connected`).

---

- Range: **2020-01-01** — **2026-04-30** (NY calendar months for file check)
- Data dir: `D:/OneDrive - Washington University in St. Louis/QT/data/raw/ibkr`

## SPY

- **rows:** 220980
- **min_ts_ny / max_ts_ny:** 2020-01-02T09:30:00-05:00 → 2026-04-30T15:59:00-04:00
- **unique_session_dates:** 568
- **duplicate_ts dropped (read_bars):** 0
- **monthly parquet files:** 28 (28 distinct year/month)
- **missing months (no parquet dir):** 48
- **sessions with row_count < 300:** 3
- **sessions with row_count > 400:** 0

**First 10 low-row sessions:**

```
[('2020-11-27', 210), ('2020-12-24', 210), ('2021-11-26', 210)]
```

**Last 10 low-row sessions:**

```
[('2020-11-27', 210), ('2020-12-24', 210), ('2021-11-26', 210)]
```

**Missing months (sample):** 2022-04, 2022-05, 2022-06, 2022-07, 2022-08, 2022-09, 2022-10, 2022-11, 2022-12, 2023-01, 2023-02, 2023-03, 2023-04, 2023-05, 2023-06, 2023-07, 2023-08, 2023-09, 2023-10, 2023-11, 2023-12, 2024-01, 2024-02, 2024-03, 2024-04, 2024-05, 2024-06, 2024-07, 2024-08, 2024-09, 2024-10, 2024-11, 2024-12, 2025-01, 2025-02, 2025-03

## QQQ

- **rows:** 1560
- **min_ts_ny / max_ts_ny:** 2026-04-27T09:30:00-04:00 → 2026-04-30T15:59:00-04:00
- **unique_session_dates:** 4
- **duplicate_ts dropped (read_bars):** 0
- **monthly parquet files:** 1 (1 distinct year/month)
- **missing months (no parquet dir):** 75
- **sessions with row_count < 300:** 0
- **sessions with row_count > 400:** 0

**First 10 low-row sessions:**

```
[]
```

**Last 10 low-row sessions:**

```
[]
```

**Missing months (sample):** 2020-01, 2020-02, 2020-03, 2020-04, 2020-05, 2020-06, 2020-07, 2020-08, 2020-09, 2020-10, 2020-11, 2020-12, 2021-01, 2021-02, 2021-03, 2021-04, 2021-05, 2021-06, 2021-07, 2021-08, 2021-09, 2021-10, 2021-11, 2021-12, 2022-01, 2022-02, 2022-03, 2022-04, 2022-05, 2022-06, 2022-07, 2022-08, 2022-09, 2022-10, 2022-11, 2022-12
