# Indicator max_trades_per_day diagnostics (QQQ 2023–2024)

**Inputs:** enriched combiner trade CSVs for **mtp=1** (v1 path), **mtp=2**, **mtp=3** (local replays + local enrich staging — not committed).

## Headline comparison

See `indicator_mtp_comparison.csv`.

- **mtp=1:** 502 trades, **~+43.55R** total, **~+0.087R** avg.
- **mtp=2:** 1000 trades, **~+72.12R** total, **~+0.072R** avg; **trade #2 ~+28.58R** (498 trades).
- **mtp=3:** 1241 trades, **~+79.48R** total, **~+0.064R** avg; trade #2 same cohort as mtp=2; **trade #3 ~+7.35R** (241 trades).

## Interpretation

- **Total R** rises with **mtp**, but **avg R and PF** decay vs mtp=1 — classic **turnover / marginal-trade** tension.
- **Trade #2 is clearly additive** in-sample; **trade #3** is **positive but thin** on a per-trade basis (see per-bucket `avg_r`, `avg_bars_held` in `indicator_mtp3_trade_number_summary.csv`).
- **Same-family repeats / prior outcomes:** `indicator_mtp2_by_family_repeat.csv`, `indicator_mtp3_by_family_repeat.csv`, `indicator_mtp*_by_prior_outcome.csv`.

## Recommendation (research only)

- **Do not** raise production `max_trades_per_day` on this evidence alone without **cost-turnover** and **OOS** alignment.
- A future router **should not** assume “second indicator trade = toxic” — the aggregate **trade #2** bucket is **profitable** here.
