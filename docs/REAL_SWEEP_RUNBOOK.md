# Canonical real-symbol sweep — local runbook

**Date:** 2026-05-11

These commands are for **developers with local IBKR parquet** under `data/raw/ibkr`. Do not commit trade-level CSVs or large sweep folders.

## 1. Metadata-only (no disk I/O)

```bash
python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend
```

## 2. Full pipeline check (bars + features + signals, no accounting)

```bash
python -m src.backtest.sweep --validate-pipeline ^
  --strategy pa_buy_sell_close_trend ^
  --symbol QQQ ^
  --start 2024-01-02 ^
  --end 2024-01-03 ^
  --data-root data/raw/ibkr
```

(PowerShell line continuation `^`; use `\` on bash.)

## 3. Tiny canonical sweep (1 combo, print only)

```bash
python -m src.backtest.sweep ^
  --strategy pa_buy_sell_close_trend ^
  --symbol QQQ ^
  --start 2024-01-02 ^
  --end 2024-01-03 ^
  --data-root data/raw/ibkr ^
  --dry-run
```

## 4. Tiny sweep with curated artifacts

```bash
python -m src.backtest.sweep ^
  --strategy orb_continuation ^
  --symbol QQQ ^
  --start 2024-01-02 ^
  --end 2024-01-02 ^
  --data-root data/raw/ibkr ^
  --output-root local_runs/canonical_sweep_smoke ^
  --max-combos 1
```

Inspect `canonical_sweep_results.csv`, `run_manifest.json`, `canonical_sweep_summary.md` — keep **local-only** unless they are tiny review aids.

## Rules

- No multi-year loops in this runbook.
- No performance interpretation; schema validation and plumbing only.
- Legacy Numba remains `python -m src.backtest.sweep --legacy ...` (first token).
