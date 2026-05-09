# Strategy Library v2 — Batch 1 plan (QQQ)

## Why not new plugins for opening_drive_pullback / opening_range_failure_retest

These are **variants of opening-range behavior**, not new economic hypotheses. Shipping them as separate strategies would **inflate the library** with near-duplicate ORB/VWAP/gap/trap logic and complicate Layer 1/2 dedupe.

- **opening_drive_pullback** belongs as a **refinement** to **`orb_continuation`** / **`orb_retest_continuation`** (continuation vs pullback entry timing off the same ORB anchor).
- **opening_range_failure_retest** belongs as a **refinement** to **`failed_orb`** / **`gap_acceptance_failure`** (failed acceptance / reclaim / retest paths share the same family semantics).

We keep the **strong Layer 1/2/3 framework** and add **orthogonal families** instead.

## Batch 1 is intentionally non-overlapping

Batch 1 adds **six** plugins in **five** distinct mechanism classes already absent from the core ORB/VWAP/gap/trap stack:

1. **Moving-average trend shift** — `intraday_ma_crossover`
2. **Oscillator reversal** — `rsi_failure_swing`
3. **Bollinger / volatility expansion** — `bollinger_squeeze_breakout`
4. **Bollinger / band mean reversion (chop)** — `bollinger_band_fade_chop`
5. **Donchian rolling channel breakout** — `donchian_channel_breakout`
6. **Price-action exhaustion** — `consecutive_bar_exhaustion`

## Scope (this phase)

- **Foundation + smoke + limited Layer 1** on **QQQ** only.
- **No** full rolling WFO, **no** Layer 2 combiner sweep, **no** mini-WFO v4 unless separately approved.
- **No** live or paper trading.
- **No** Batch 2/3 strategies in this commit.

## Deliverables

Feature modules (`indicators`, `channels`, `regime`), six strategies with YAMLs, loader/metadata, tests, health CSV/MD, Layer 1 curated outputs under `src/research/results/layer1_v2_batch1_qqq_2023_2024/`, and interpretation summary `strategy_library_v2_batch1_summary.md`.
