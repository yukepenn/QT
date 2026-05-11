# Pre-sweep gate decision — PA Batch B/C tuned v3

Source: `pa_batch_bc_gate_diagnostics_v3_preflight/pa_gate_rows.csv` (first grid combo per strategy).

| strategy | final_valid_signals | assessment |
|----------|---------------------|--------------|
| `pa_buy_sell_close_trend` | **440** | Nonzero; safe to sweep full grid. |
| `pa_climax_reversal` | **95** | Nonzero; lower frequency than close-trend (expected). Safe to sweep; diversity must be checked **post-selection** via `candidate_signal_diversity.py`. |

**Decision:** **PROCEED_TO_FULL_GRID_SWEEP** for both strategies (no zero-signal block).
