# Strict candidate selection — tuned v2

Filters passed to `src/research/select_candidates.py`:

- `min_trades`: 30  
- `min_profit_factor`: 1.05  
- `min_total_r`: 0  
- `max_drawdown_r`: -50  
- `max_avg_bars_held`: 120  
- `max_eod_count`: 0  
- `max_end_of_data_count`: 0  
- `top_per_strategy`: 5  
- `sort_by`: candidate_score  

Manifest: `sweep_manifest.csv` (includes strategies skipped at preflight with no results CSV).
