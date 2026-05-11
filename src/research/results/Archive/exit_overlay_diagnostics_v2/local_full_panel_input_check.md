# local_full_panel_input_check

- **Panel:** present — **10,628** rows × **170** columns. Profiles: `pa_only_mtp1_meta`, `pa_gap_mtp2_meta`, `primary_mtp2_meta`. Windows: `early_oow`, `insample_ref`, `late_oow`, `full_available`. Required columns for alignment (`profile_id`, `window`, `candidate_id`, `entry_ts_utc`, `signal_ts_utc`, `entry_idx`, `exit_idx`, prices, `risk_per_share`, `r_multiple`, `exit_reason`, `bars_held`, `session_date`) are present.
- **QQQ 1m bars:** loaded from **`data/raw/ibkr`** — **617,160** rows spanning panel session dates; **`missing_sessions = 0`** (see `bar_load_meta.csv`).
- **Reader:** `load_bars_for_panel` in `run_exit_overlay_diagnostics.py` calls `read_bars(asset="equity", symbol="QQQ", ...)`.
- **Alignment:** proceeded successfully; gate outcome **`ALIGNMENT_FAIL`** on aggregate `total_r_diff` (see `alignment/alignment_decision.md`).
