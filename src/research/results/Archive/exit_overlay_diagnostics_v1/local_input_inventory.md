# local_input_inventory

Companion CSV: `local_input_inventory.csv`.

- **Panel:** `trade_context_panel.csv` — present; **10,628** rows; **170** columns; profiles `pa_only_mtp1_meta`, `pa_gap_mtp2_meta`, `primary_mtp2_meta`; windows `early_oow`, `insample_ref`, `late_oow`, `full_available`.
- **QQQ bars:** `data/raw/ibkr` parquet partitions; date span per `overlay_data_quality.csv` (`2020-01-02`–`2026-04-30`); **617,160** bar rows loaded for the panel span.
- **Session coverage:** **1526** unique `session_date` values in filtered panel; **0** missing bar sessions (`bars_available=0` in `overlay_input_coverage.csv`).
- **Commit status:** panel and `local_rows/**` — **untracked / gitignored**; do not stage.
