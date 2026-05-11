# full_panel_run_inventory

| Field | Value |
|--------|--------|
| Git tip | Use `git rev-parse HEAD` on `main` after pull — commit message **`Research(exit): run full-panel overlay alignment`** |
| V2 decision (this cycle) | **`REFINE_REPLAY_ALIGNMENT`** |
| Prior committed v2 alignment | **Synthetic smoke** (1-row style numerics) — preserved under `alignment/archive_synthetic_pre_full_panel/` |
| Full-panel alignment | **Real** — 10,628 panel rows × 15 grid configs; see `alignment/full_panel_alignment_manifest.csv` |
| Local panel (expected) | `src/research/results/local_detailed_trade_context_replay_v1/local_rows/trade_context_panel.csv` |
| QQQ bars | `data/raw/ibkr` via `load_bars_for_panel` → `read_bars(equity, QQQ)` |
| Curated outputs | **Overwritten** in `alignment/` for this real run; **not** using `git add .` |
| Local-only (never stage) | `local_rows/alignment_trade_detail.csv`, future `overlay_trade_results_v2.csv`, parquet, caches, logs |
