# Data design — controlled Layer1 (repo-local only)

**Policy:** Use **`data/raw/ibkr`** only. **No** external roots, **no** `.env` data paths, **no** downloads in the run task. **No `D:`** strings in committed CSV/MD (use repo-relative paths).

## Committed QQQ coverage

- **Layout:** `data/raw/ibkr/equity/bars_1min/symbol=QQQ/year=YYYY/month=MM/data.parquet`
- **Years present:** 2020 through **2026** (2026 includes months committed in repo at design time).
- **Bar size:** 1 minute equity bars.
- **Reader:** `read_bars(asset="equity", symbol="QQQ", start=..., end=..., data_dir="data/raw/ibkr")` concatenates available monthly files in range.

## Schema (typical columns)

Loaded frame includes session / time / OHLCV / minute-from-open (exact set from parquet schema — aligns with **`BacktestConfig`** defaults: `session_date`, `ts_utc`, `ts_ny`, `minute_from_open`, `open`, `high`, `low`, `close`, plus feature builders adding VWAP, ATR, etc.).

## RTH / session

Bars are IBKR equity 1m partitions as stored; strategies use **`minute_from_open`** and **`session_date`**. If future RTH filtering is required, implement at read or feature stage — **not** assumed changed for this design.

## Design windows

| Tier | Window | Use |
|------|--------|-----|
| **Preferred first controlled run** | **2023-01-01** to **2024-12-31** | Two full calendar years on committed data; limits runtime vs 2020–2026 full span while still multi-regime. |
| **Fallback (smaller)** | **2024-01-01** to **2024-06-30** | Half-year smoke for grid debugging. |
| **Stretch (full committed QQQ)** | **2020-01-01** to end of last committed 2026 month | Only after first-pass gates pass and runtime is acceptable; use **`--max-combos`** strictly. |

**Justification:** Full 7-year grid sweeps risk parameter explosion and long wall times; **2023–2024** matches recent “core span” language elsewhere in the repo and stays inside committed data without external roots.

## CLI variables (template)

- `DATA_ROOT=data/raw/ibkr`
- `SYMBOL=QQQ`
- `ASSET=equity`
- `START=2023-01-01` / `END=2024-12-31` (or fallback above)
