# Candidate selection — Layer 1 tuned v1 (Batch 1)

**Manifest:** `sweep_manifest.csv`  
**Output root:** `layer1_v2_batch1_tuned_qqq_2023_2024_v1/`

## Strict filters (both strategies)

- `min_trades`: 40  
- `min_profit_factor`: 1.08  
- `min_total_r`: 0  
- `max_drawdown_r`: -50  
- `max_avg_bars_held`: 120  
- `max_eod_count`: 0  
- `max_end_of_data_count`: 0  

## Relaxed fallback (per strategy, only if strict empty)

- `min_trades`: 25  
- `min_profit_factor`: 1.02  
- `min_total_r`: 0  
- `max_drawdown_r`: -60  

## Top per strategy

5 (`--top-per-strategy 5`)

## Scope

Only **bollinger_squeeze_breakout** and **rsi_failure_swing** were swept. Other Batch 1 plugins are out of scope for this tuning pass.
