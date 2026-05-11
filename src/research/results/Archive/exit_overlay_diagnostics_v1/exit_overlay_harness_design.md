# Exit overlay harness design (v1)

## Principles

1. **Entries frozen** — `entry_ts_utc`, `entry_price`, `stop_price`, `target_price`, `risk_per_share` from the local trade-context panel; no signal / YAML / combiner changes.
2. **Post-entry only** — walk 1-minute QQQ OHLCV from the entry bar forward within the session calendar day.
3. **No lookahead** — overlays use only bars at or after the entry bar; trend-swing eligibility uses **decision-time** row fields (`context_bucket`, `decision_pa_always_in_side_20_label`).
4. **Intrabar ambiguity** — if stop and target are both touched in the same bar: default **`stop_first`**; record `ambiguous_bar` on the exit bar when applicable; optional `target_first` / `skip_ambiguous` supported in simulator enum for sensitivity (not headline aggregates).
5. **VWAP trail** — session VWAP from typical price × volume cumulatively from session open (no external VWAP column in raw parquet).
6. **Sanity gate** — `fixed_target_replay` should match panel `r_multiple` when the bar path model matches combiner materialization; current mean abs diff **~0.28–0.38 R** by profile×window → **treat overlay deltas as diagnostic until replay is aligned** (see `overlay_sanity_vs_original.csv`).

## Overlay list (v1)

| overlay_id | intent |
|------------|--------|
| `baseline_original` | Panel `r_multiple` / exit fields (sanity baseline). |
| `fixed_target_replay` | Re-simulate fixed stop/target path on 1m bars. |
| `trend_swing_1p5R` / `trend_swing_2R` | Wider targets (1.5R / 2R) when trend-swing eligible only. |
| `runner_after_1R_trail_vwap` | After +1R MFE, trail with VWAP−0.25×ATR (floor initial stop). |
| `runner_after_1R_trail_atr` | After +1R, Chandelier-style trail using ATR. |
| `no_followthrough_exit_{3,5}bars` | Exit if MFE < 0.15R by bar N (reversal/gap-failure focus in analysis slices). |
| `max_hold_tighten_{30,60}` | Force exit at bar cap if stop/target not hit. |

## Outputs

- **Committed:** aggregates under this root (`overlay_results_*.csv`, summaries, decision, bundle, `overlay_results_detail_by_profile_window.csv`).
- **Local-only:** `local_rows/overlay_trade_results.csv` (per-trade per-overlay rows).
