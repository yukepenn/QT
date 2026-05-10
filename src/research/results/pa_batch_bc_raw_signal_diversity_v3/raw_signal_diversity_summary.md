# Raw sweep signal diversity — PA Batch B/C tuned v3 (QQQ 2023–2024)

Strict filters: `min_trades=30`, `min_profit_factor=1.05`, `min_total_r=0`, `max_drawdown_r=-50`, `max_avg_bars_held=120`, `eod/end_of_data=0`.  
Pool analyzed: **top 100** rows by `candidate_score` after filtering.

## Summary

| Strategy | Rows in CSV | Strict eligible | Unique `pure_signal_hash` @ top 20 | @ top 50 | @ top 100 | In top-100 pool |
|-----------|-------------|-----------------|-------------------------------------|----------|-----------|----------------|
| `pa_climax_reversal` | 1152 | **176** | **2** | **2** | **5** | **5** |
| `pa_buy_sell_close_trend` | 1152 | **895** | **8** | **13** | **26** | **26** |

## Interpretation

- **Climax (H1):** The strict pool is **not** a single-mask universe. The **Layer-1 strict top-5 selector** was the bottleneck: lower-ranked strict rows introduce **additional** `pure_signal_hash` groups within the first 100 score-sorted rows.
- **Close-trend:** Rich strict diversity; selector-only issues are secondary.

## Artifacts

Per-strategy: `raw_sweep_signal_diversity_{strategy}.csv`, `unique_signal_hash_candidates_{strategy}.csv`, `duplicate_signal_hash_groups_{strategy}.csv`, short `{strategy}.md`.
