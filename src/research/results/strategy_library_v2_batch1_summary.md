# Strategy Library v2 — Batch 1 summary (QQQ)

## 1. Why Batch 1 was added

Batch 1 adds **six orthogonal mechanism families** (MA trend shift, RSI-style oscillator reversal, Bollinger squeeze breakout, Bollinger fade in chop, Donchian breakout, consecutive-bar exhaustion) without inflating the ORB/VWAP/gap/trap surface. See `strategy_library_v2_batch1_plan.md` for why `opening_drive_pullback` / `opening_range_failure_retest` stay refinements, not new plugins.

## 2. Non-duplication vs existing stack

These plugins do **not** reuse ORB/VWAP/gap/trap entry templates; they consume **new feature columns** from `indicators.py`, `channels.py`, and `regime.py` plus existing safe OHLCV/VWAP/volatility/volume columns.

## 3. Feature modules

| module | role |
|--------|------|
| `src/features/indicators.py` | Session-scoped EMA/SMA/RSI/MACD/stoch/CCI/ADX-style columns |
| `src/features/channels.py` | Bollinger + prior-exclusive Donchian |
| `src/features/regime.py` | `range_efficiency`, `vwap_cross_count`, `trend_score`, `compression_score` |

`feature_key.py` / `build_features.py` / `feature_config.py` integrate these with stable cache keys.

## 4. Registration

**16** strategies registered in `loader.py` (10 legacy + 6 Batch 1). Metadata in `metadata.yaml`.

## 5. Smoke (Jan 2025)

QQQ **2025-01-01 → 2025-01-31**, `--max-combos 24`, `--min-trades 1`, **numba_fast**, all **exit 0**. Best row by `profit_factor` (in-window only; not predictive):

| strategy | runtime_s | combos | best_trades | best_total_r | best_pf |
|----------|----------:|-------:|------------:|-------------:|--------:|
| intraday_ma_crossover | 0.54 | 24 | 18 | -0.65 | 0.76 |
| rsi_failure_swing | 0.56 | 24 | 7 | 0.62 | 3.83 |
| bollinger_squeeze_breakout | 0.81 | 24 | 20 | -1.68 | 0.69 |
| bollinger_band_fade_chop | 0.85 | 24 | 19 | -3.88 | 0.81 |
| donchian_channel_breakout | 0.55 | 24 | 1 | -1.04 | 0.0 |
| consecutive_bar_exhaustion | 0.53 | 24 | 19 | -6.12 | 0.58 |

Details and warnings: `strategy_library_v2_batch1_health.md` / `.csv`.

## 6. Layer 1 (2023–2024) — partial

Full per-strategy 2023–2024 sweeps at production depth are **not** all committed here (time budget). A representative **capped** sweep for **`rsi_failure_swing`** (`--max-combos 150`, `min_trades=10` for sweep display) showed **meaningful** PF/Total R in-window; **`select_candidates`** wrote **5** YAMLs under `layer1_v2_batch1_qqq_2023_2024/` (filters: `min_trades>=25`, `PF>=1.02`, `total_r>=-5`, `maxDD_r>=-60`).

**Other Batch 1 strategies:** treat as **NEEDS_GRID_TUNING** until similar 2023–2024 sweeps are run with tuned `min_trades` / grid density.

## 7. Candidate counts (this commit)

| strategy | candidates (this partial run) |
|----------|------------------------------|
| rsi_failure_swing | 5 |
| others | not run in this commit |

## 8. Promising vs weak

| strategy | label |
|----------|--------|
| rsi_failure_swing | **PROMISING_FOR_LAYER2** (spot-check only) |
| intraday_ma_crossover | **NEEDS_GRID_TUNING** |
| bollinger_squeeze_breakout | **NEEDS_GRID_TUNING** |
| bollinger_band_fade_chop | **NEEDS_GRID_TUNING** |
| donchian_channel_breakout | **NEEDS_GRID_TUNING** |
| consecutive_bar_exhaustion | **NEEDS_GRID_TUNING** |

## 9. mini-WFO v4

**Defer** mini-WFO v4 until at least one additional Batch 1 family shows stable 2023–2024 behavior under conservative filters (or grids are tightened deliberately).

## 10. Decision

**TUNE_BATCH1_GRIDS_FIRST** — run deeper 2023–2024 sweeps (or widen acceptance thresholds) for the remaining five strategies; keep **rsi_failure_swing** on watch for a **reduced Layer 2** probe **after** independent review (not executed in this phase).

### Recommended next step (design-only)

If Batch 1 strengthens: propose reduced Layer 2 candidate sets (`indicator_trend`, `oscillator_reversal`, …) and a **mini-WFO v4** design that keeps refined failed/gap core separate — **do not run** until explicitly approved.
