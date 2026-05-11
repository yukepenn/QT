# PA Batch B/C — exit diagnostics v2 (strict tuned v2 YAMLs)

**Window:** QQQ 2023-01-01 → 2024-12-31  
**Script:** `src/research/pa_exit_diagnostics.py`  
**Inputs:** `layer1_pa_batch_bc_tuned_qqq_2023_2024_v2/selected_candidates/*.yaml`

## Summary

### pa_buy_sell_close_trend (5 YAMLs)

- **Economics:** ~459–461 trades; **total_r ~29–37** at **0.02** slippage stress vs ~34–42 at base 0.01 — meaningful cost sensitivity but PF stays **≈1.18–1.23** under stress on these rows.
- **Exits:** **max_hold_count** large (often **200+**) vs stop/target counts — **max-hold-dominated** exit profile persists at tuned v2 longer holds (diagnostic confirmation).

### pa_climax_reversal (5 YAMLs)

- **51 trades** each on identical hyper surfaces where params duplicate effective economics.
- **max_hold_count** low (0–2); **stop vs target** balanced (≈29–30 stops, ≈20 targets).
- **0.02 stress:** total_r compresses toward ~0–2; PF remains **~1.19–1.22** on strong rows — milder hold drag than close-trend.

## Files

- `pa_batch_bc_exit_diagnostics_v2.csv` — copy of `pa_exit_rows.csv`
