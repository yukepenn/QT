# Reduced Layer 2 v2 — Strategy Library Batch 1 (QQQ 2023–2024)

**Status:** design + combiner configs for `layer2_qqq_v2_batch1_2023_2024`. **No** mini-WFO v4/v5 and **no** full WFO in this phase.

## 1. Why only RSI + Bollinger squeeze are strict core

Layer 1 on QQQ 2023–2024 produced **strict-filter** YAMLs only for:

- `rsi_failure_swing` — oscillator failure / reversal mechanism, distinct from price-channel ORB logic.
- `bollinger_squeeze_breakout` — volatility compression → expansion; orthogonal to pure mean-reversion fades.

These two families passed the stricter Layer 1 gates with exportable configs and are treated as the **primary Batch 1 hypothesis** for Layer 2 stacking and conflict resolution.

## 2. Why Bollinger fade + consecutive exhaustion are diagnostic (relaxed)

- `bollinger_band_fade_chop` and `consecutive_bar_exhaustion` Layer 1 rows used **relaxed** acceptance (warnings / softer thresholds). They are **included in Layer 2 only with `include_warnings: true`** in dedicated candidate sets so we can measure whether they add **diversifying signals** or mostly **overlap / noise** versus the strict core.
- Dedicated diagnostic sets (`range_mean_reversion_diagnostic`, `price_action_exhaustion_diagnostic`) isolate each relaxed family for overlap review.

## 3. Why MA + Donchian are excluded

- `intraday_ma_crossover` and `donchian_channel_breakout` produced **zero** selected Layer 1 candidates for this window. Including them in Layer 2 would reference an empty universe. They stay out until a retuned Layer 1 sweep yields YAMLs.

## 4. Layer 2 execution plan (this repo phase)

- Base config: `src/combiner/configs/layer2_qqq_v2_batch1_2023_2024.yaml`
- Sweep config: `src/combiner/configs/layer2_sweep_qqq_v2_batch1_2023_2024.yaml` (grid size \(6 \times 4 \times 3 \times 3 \times 3 \times 2 = 1296\) combos)
- **Diagnostics-only** preflight on `relaxed_batch1` (signal counts, overlap matrix, conflict summary).
- **Fixed runs** on strict and relaxed sets; **sweep** only if fixed-run gate passes (at least one strict or acceptable relaxed outcome).
- **Postprocess:** behavior dedupe + cost stress on curated sweep outputs.

## 5. No mini-WFO yet

Mini-WFO is **not** part of this step. **Layer 2 results** (fixed + optional sweep + cost stress) decide whether **mini-WFO v4** is justified.

## 6. Decision gate (after Layer 2 numbers)

Proceed toward **mini-WFO v4 design** only if, among strict Batch 1 systems:

- `total_r` is positive for at least one configuration,
- profit factor (or PF_R) > ~1.05,
- cost stress remains acceptable at **0.02** slippage,
- behavior-unique systems are not trivial duplicates,
- drawdown is acceptable for the research mandate.

Otherwise: **tune Batch 1 grids** or **defer Batch 1** and return focus to refined failed-core work.

## Explicit non-goals

- No SPY, no IBKR pulls, no `data/raw` edits.
- No new strategy plugins or Batch 2/3 scope.
