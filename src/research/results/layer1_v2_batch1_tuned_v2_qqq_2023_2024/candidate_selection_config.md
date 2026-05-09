# Candidate selection — tuned v2

## Strict thresholds (cost-aware)

- `min_trades`: 40  
- `min_profit_factor`: **1.10**  
- `min_total_r`: 0  
- `max_drawdown_r`: -40 (floor: row `max_drawdown_r` must be ≥ -40)  
- `max_avg_bars_held`: 120  
- `max_eod_count`: 0  
- `max_end_of_data_count`: 0  

## 0.02 slippage prefilter

Tooling: `src/research/layer1_row_slippage_eval.py` re-simulates top baseline-filtered rows at `slippage_per_share=0.02`. **Not run** for tuned v2 because **no rows passed baseline PF ≥ 1.10**.

## Outcome

**Zero candidates.** Best in-window row (by PF among `trades ≥ 40`) had **profit_factor ≈ 1.048**, **total_r ≈ 6.82**, **268 trades**.

## RSI tuned v2

**Not created** (Case B): prior Layer 2 evidence shows RSI does not add combiner `total_r` once squeeze is present; no orthogonal slice worth a second grid in this phase.
