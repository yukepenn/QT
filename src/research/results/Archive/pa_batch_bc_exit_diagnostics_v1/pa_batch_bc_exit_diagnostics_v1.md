# PA Batch B/C — exit diagnostics v1 (selected candidates, QQQ 2023–2024)

**Method:** `src/research/pa_exit_diagnostics.py` loads the full `config:` block from each Layer 1 candidate YAML, rebuilds features, fast backtest from signal arrays, reports aggregate metrics + **0.02** slippage stress row.

## `pa_buy_sell_close_trend` (baseline `layer1_pa_batch_bc_qqq_2023_2024/selected_candidates/`)

Five strict candidates: **~380–413 trades** in-window; **max_hold** is a large share of exits (typ. **~230–305** of trades) → hold / time-exit dominated profile at default `max_hold_minutes` and 0.01 base slippage. **0.02 slippage stress** cuts `total_r` materially vs base (order ~20–30% drop on the runs below — see CSV).

## `pa_climax_reversal` (tuned v1 `layer1_pa_batch_bc_tuned_qqq_2023_2024_v1/selected_candidates/`)

All five strict YAMLs are **identical** economics on this window in this diagnostic (**37** trades, same `total_r` / exit mix) — confirms dedupe / selection tied to the same effective parameter surface.

**Exit mix (all five):** `stop_count` 18, `target_count` 19, `max_hold_count` 0 — short holds; cost stress 0.02 is milder than on close-trend.

**File:** `pa_batch_bc_exit_diagnostics_v1.csv` (copy of `pa_exit_rows.csv`).
