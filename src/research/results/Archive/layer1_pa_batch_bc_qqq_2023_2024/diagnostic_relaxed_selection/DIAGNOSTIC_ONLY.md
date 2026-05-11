# DIAGNOSTIC ONLY — not authoritative

This folder records a **relaxed-threshold** selection pass for troubleshooting. **Do not** treat these rows as production Layer 1 candidates. The authoritative candidate library is:

`../selected_candidates/` (strict filters only).

## Command

```bash
python src/research/select_candidates.py \
  --output-root src/research/results/layer1_pa_batch_bc_qqq_2023_2024/diagnostic_relaxed_selection \
  --top-per-strategy 5 \
  --min-trades 15 \
  --min-profit-factor 1.00 \
  --min-total-r -3 \
  --max-drawdown-r -60 \
  --max-avg-bars-held 150 \
  --max-eod-count 0 \
  --max-end-of-data-count 0 \
  --result pa_broad_channel_zone=src/strategies/testing_parameters_results/pa_broad_channel_zone/sweep_20260510_163320_layer1_pa_batch_bc_qqq_2023_2024/results.csv \
  --result pa_climax_reversal=src/strategies/testing_parameters_results/pa_climax_reversal/sweep_20260510_163331_layer1_pa_batch_bc_qqq_2023_2024/results.csv \
  --result pa_second_entry_pullback=src/strategies/testing_parameters_results/pa_second_entry_pullback/sweep_20260510_163343_layer1_pa_batch_bc_qqq_2023_2024/results.csv \
  --result pa_wedge_reversal=src/strategies/testing_parameters_results/pa_wedge_reversal/sweep_20260510_163356_layer1_pa_batch_bc_qqq_2023_2024/results.csv \
  --result pa_buy_sell_close_trend=src/strategies/testing_parameters_results/pa_buy_sell_close_trend/sweep_20260510_163415_layer1_pa_batch_bc_qqq_2023_2024/results.csv \
  --result pa_generic_breakout_pullback=src/strategies/testing_parameters_results/pa_generic_breakout_pullback/sweep_20260510_163614_layer1_pa_batch_bc_qqq_2023_2024/results.csv
```

## Result

- Only **`pa_buy_sell_close_trend`** produced any passing rows; top five are listed in `selected_candidates.csv`.
- Duplicate `.yaml` exports under `selected_candidates/` were **removed** from the repo to avoid confusion with strict YAMLs; reproduce from `selected_candidates.csv` + sweep `results.csv` if needed.
