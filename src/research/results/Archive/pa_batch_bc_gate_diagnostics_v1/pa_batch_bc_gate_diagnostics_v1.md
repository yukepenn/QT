# PA Batch B/C — gate diagnostics v1 (tuned v1 YAMLs, QQQ 2023–2024)

**Window:** 2023-01-01 → 2024-12-31, **first combo** from each `*_tuned_v1.yaml` (same merge as `check_strategy_fast_parity`).

| Strategy | Total bars | Entry window bars | Final `valid` signals | Notes |
|----------|------------|-------------------|----------------------|--------|
| `pa_broad_channel_zone` | 194,880 | 83,327 | 0 | **Bottleneck:** `close <= pa_range_lower_third` (zone filter) — count drops from **1,402** broad-bull bars to **0** in-zone. |
| `pa_generic_breakout_pullback` | 194,880 | 75,797 | 0 | All gates collapsed inside strategy loop before geometry (see script totals only for this run). |
| `pa_second_entry_pullback` | 194,880 | 83,327 | 10 | Sparse; investigate context / two-leg vs manifest trade count. |
| `pa_buy_sell_close_trend` | 194,880 | 75,802 | 401 | Primary “working” family on this window under tuned v1. |
| `pa_climax_reversal` | 194,880 | 60,742 | 79 | Modest support vs broad channel / generic. |

**Detailed gate chain** (broad channel only, see `src/research/pa_gate_diagnostics.py`): `pass_regime_broad_bull` → `pass_zone_below_upper_third` → pullback depth → VWAP context → bull reversal / climax block → `finalize_long_signals_df` (min risk, stops).

**Files:** `pa_batch_bc_gate_diagnostics_v1.csv` (copy of `pa_gate_rows.csv`), `pa_gate_rows.jsonl` (append log).
