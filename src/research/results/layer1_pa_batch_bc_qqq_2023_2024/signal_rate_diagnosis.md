# Signal / trade-rate diagnosis — PA Batch B/C Layer 1 (QQQ 2023–2024)

Focused grids, full sweeps (no `max_combos` cap). Metrics are **in-sample** on `results.csv` rows after duplicate-combo skip.

## pa_broad_channel_zone (Batch B)

- **Grid:** 288 raw → 72 result rows (216 skipped duplicate).
- **Trades:** all 72 rows have **0** trades (matches Jan 2025 smoke: 0 trades).
- **Diagnosis:** **too_sparse** — no fills on QQQ 2023–2024 under current signal gates; needs **grid / gate relaxation** or feature-threshold review (`TOO_SPARSE_NEEDS_GRID_TUNE` / `FEATURE_LOGIC_REVIEW`), not Layer 2.

## pa_climax_reversal (Batch B)

- **Trades:** every combo trades heavily (median **93** trades); **max 93**.
- **Edge:** best profit factor **~0.88**, total R **~−13.7**, max DD R **~−17.9** (Jan smoke had few trades; full window is active but losing).
- **Diagnosis:** **high_activity_weak_edge** — signal rate is fine; economics fail vs costs / path. Tune grid toward fewer, higher-quality fades or defer.

## pa_second_entry_pullback (Batch B)

- **Trades:** 36/72 rows nonzero; **max 8** trades (median nonzero **8**). Best row: PF **~2.39**, total R **~+6.6**, but **well below** strict `min_trades=30`.
- **Diagnosis:** **too_sparse** at the strategy level for 2023–2024 despite nonzero smoke in some windows — widen grid / loosen exclusivity to reach trade counts worth Layer 1 gates.

## pa_wedge_reversal (Batch B)

- **Trades:** all rows active; median **123**, max **126**.
- **Edge:** best PF **~0.96**, total R **~−10.1**, max DD R **~−24.8** (Jan smoke had a handful of trades; full sample is busy but negative).
- **Diagnosis:** **high_activity_weak_edge** — similar to climax: not sparse, but no PF ≥ 1.05 at scale.

## pa_buy_sell_close_trend (Batch C)

- **Trades:** all 108 rows nonzero; median **~394**, max **413**.
- **Edge:** best PF **~1.23**, total R **~+24.1**, max DD R **~−10.9**; **36** rows pass **strict** Layer 1 filters (including `max_eod_count=0`, `max_avg_bars_held=120`).
- **Hold time:** best-ranked rows often have **high** average bars held (**~55–61**), so the playbook is **slow** vs typical intraday scalps → **cost_sensitive_candidate** for Layer 2 (metadata already marks `cost_sensitivity: high`).
- **Jan smoke:** active (e.g. ~18 trades in Jan 2025) — consistent with viable signal rate on the full window.

## pa_generic_breakout_pullback (Batch C)

- **Trades:** all **0** on 2023–2024 (matches Jan 2025 smoke).
- **Diagnosis:** **too_sparse** — same remediation as broad channel: grid / breakout definition / pullback gate review before any Layer 2 talk.

## Summary table

| Strategy | Signal rate | Edge (best PF) | vs Jan smoke |
|----------|---------------|----------------|--------------|
| pa_broad_channel_zone | none | — | consistent (0) |
| pa_climax_reversal | high | weak | smoke few; full window busy |
| pa_second_entry_pullback | very low | strong PF, tiny n | smoke 0; window still tiny n |
| pa_wedge_reversal | high | weak | smoke few; full window busy |
| pa_buy_sell_close_trend | high | moderate+ | consistent |
| pa_generic_breakout_pullback | none | — | consistent (0) |
