# Strategy Library v2 Batch 1 Summary

## 1. Purpose

- Add **non-overlapping behavioral families** (MA / oscillator / Bollinger / Donchian / exhaustion) orthogonal to the ORB/VWAP/gap/trap stack.
- Avoid inflating the library with **near-duplicate** opening-drive / ORB-template variants (see `strategy_library_v2_batch1_plan.md`).

## 2. Implementation status

- **Features:** `indicators.py`, `channels.py`, `regime.py`, `build_types.py`; integrated in `feature_config.py`, `feature_key.py`, `build_features.py`.
- **Strategies:** six plugins registered (**16** total strategies in `loader.py`).
- **Tests:** `162+` after adding `tests/test_select_candidates_manifest.py` (manifest multi-strategy selection).
- **DataFrame fragmentation:** mitigated via single `pd.concat` per feature module (see audit §Phase 2).

## 3. Smoke health (Jan 2025)

QQQ **2025-01-01 → 2025-01-31**, `--max-combos 50`, `--min-trades 1`, `--no-save`, `--profile`. Source: `strategy_library_v2_batch1_health.csv` / `.md`.

Jan is a **wiring / health** check only — not used to declare live edge.

## 4. Layer 1 2023–2024 results

- **Window:** 2023-01-01 → 2024-12-31, QQQ only.
- **Tag:** `layer1_v2_batch1_qqq_2023_2024`.
- **Capping:** raw grids **> 2000** → `--max-combos 500` (see `sweep_manifest.csv` column `capped`). **Donchian** raw grid **1728** → full exhaust.
- **Prior rsi-only export:** superseded by the unified manifest row in `sweep_manifest.csv` (same tag, consistent `min_trades=25` display slice for manifest stats).

### By strategy (manifest “best” row = top PF among rows with trades ≥ 25)

| strategy | capped | result_rows | best PF | best total_r | strict candidates |
|----------|--------|------------:|--------:|-------------:|-------------------|
| intraday_ma_crossover | yes | 192 | 0.94 | -3.45 | 0 |
| rsi_failure_swing | yes | 128 | 1.85 | 7.64 | 5 |
| bollinger_squeeze_breakout | yes | 500 | 1.35 | 30.96 | 5 |
| bollinger_band_fade_chop | yes | 500 | 1.14 | -2.93 | 0 (5 relaxed) |
| donchian_channel_breakout | no | 72 | 0.93 | -64.51 | 0 |
| consecutive_bar_exhaustion | yes | 256 | 1.14 | -3.25 | 0 (5 relaxed) |

**Selection:** `select_candidates.py --manifest sweep_manifest.csv` → **20** YAMLs total in `selected_candidates/` (see `candidate_summary.md`). **No** candidates: `intraday_ma_crossover`, `donchian_channel_breakout` (`no_candidate_strategies.txt`).

## 5. Family interpretation (labels)

| strategy | label |
|----------|--------|
| intraday_ma_crossover | **NEEDS_GRID_TUNING** |
| rsi_failure_swing | **PROMISING_FOR_REDUCED_LAYER2** |
| bollinger_squeeze_breakout | **PROMISING_FOR_REDUCED_LAYER2** |
| bollinger_band_fade_chop | **NEEDS_GRID_TUNING** (relaxed-only; marginal / noisy) |
| donchian_channel_breakout | **DEFER** |
| consecutive_bar_exhaustion | **NEEDS_GRID_TUNING** (relaxed-only; marginal PF) |

## 6. Recommended next action

**`PROCEED_TO_REDUCED_LAYER2_V2_BATCH1_DESIGN`** — at least **two** Batch 1 families (`rsi_failure_swing`, `bollinger_squeeze_breakout`) produced **strict** passing YAMLs; additional relaxed families need review before any combiner weighting.

Concrete design (not executed): `src/research/results/reduced_layer2_v2_batch1_design.md`.

## 7. Explicit non-runs

- **Layer 2** sweeps: **not run**.
- **mini-WFO v4 / v5**: **not run**.
- **Full WFO**: **not run**.
