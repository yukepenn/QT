# weak_period_interpretation

This file summarizes weak periods using **quarterly profile PnL** (`complete_quarterly_summary.csv`, `full_available`) and **QQQ-derived quarterly context**.

Period-sliced **exit-reason mix** and **candidate contribution** are **not** present in curated complete-smoke CSVs; those rows are explicitly marked `REQUIRES_LOCAL_DETAILED_REPLAY` / `WINDOW_LEVEL_FALLBACK`.

## Table
weak_period         interpretation  qqq_context_label                                                     notes
     2025Q1 MARKET_CONTEXT_ALIGNED downtrend_high_vol                            pa_gap_tracks_or_beats_pa_only
     2022Q4 MARKET_CONTEXT_ALIGNED      unknown_mixed                              pa_gap_underperforms_pa_only
     2023Q3 MARKET_CONTEXT_ALIGNED  downtrend_low_vol pa_gap_underperforms_pa_only;primary_underperforms_pa_gap

