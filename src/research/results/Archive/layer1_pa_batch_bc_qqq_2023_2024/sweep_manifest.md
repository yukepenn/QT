# Layer 1 sweep manifest — PA Batch B/C (QQQ 2023–2024)

Tag: `layer1_pa_batch_bc_qqq_2023_2024`

Machine-readable: `sweep_manifest.csv`.

| strategy | status | elapsed_sec | capped | max_combos | raw_grid | result_rows | best_trades | best_pf | best_pf_r | best_total_r | best_maxDD_r | best_avg_bars_held | best_eod | best_eod_data | notes |
|----------|--------|-------------|--------|------------|----------|-------------|-------------|---------|-----------|--------------|--------------|-------------------|----------|---------------|-------|
| pa_broad_channel_zone | ok_zero_trade | 10.75 | false | — | 288 | 72 | 0 | 0.0 | | 0.0 | 0.0 | 0.0 | 0 | 0 | all_combos_zero_trades |
| pa_climax_reversal | ok | 11.526 | false | — | 288 | 72 | 93 | 0.879 | | −13.71 | −17.90 | 7.37 | 0 | 0 | |
| pa_second_entry_pullback | ok | 11.405 | false | — | 288 | 72 | 8 | 2.387 | | +6.58 | −1.07 | 4.5 | 0 | 0 | |
| pa_wedge_reversal | ok | 12.655 | false | — | 288 | 72 | 126 | 0.964 | | −10.09 | −24.77 | 10.06 | 2 | 0 | |
| pa_buy_sell_close_trend | ok | 19.925 | false | — | 432 | 108 | 413 | 1.230 | | +24.07 | −10.86 | 59.34 | 0 | 0 | best row PF-ranked |
| pa_generic_breakout_pullback | ok_zero_trade | 118.693 | false | — | 432 | 108 | 0 | 0.0 | | 0.0 | 0.0 | 0.0 | 0 | 0 | all_combos_zero_trades |

**Notes**

- `max_combos`: not used (full grid).
- `best_*` columns come from the sweep manifest row (best PF row where applicable; zero-trade strategies have zeros).
- Full paths to `results_csv` / `sweep_folder` are absolute in `sweep_manifest.csv` (local machine).
