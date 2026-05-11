# PA Batch B/C — tuned v2 Layer 1 plan (QQQ 2023–2024)

**Tag:** `layer1_pa_batch_bc_tuned_qqq_2023_2024_v2`  
**Output root:** `src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v2/`

## Why tuned v2 after P0

`normalized_param_key` was corrected in commit `307d90f`. Baseline (`layer1_pa_batch_bc_qqq_2023_2024`) and tuned v1 (`layer1_pa_batch_bc_tuned_qqq_2023_2024_v1`) sweeps may have **under-explored** the declared grid due to dedupe collisions. **Tuned v2 is the first post-key-fix trusted Layer 1 rerun** for these grids, combined with **diagnostic-driven axes** (not blind expansion).

## Diagnostics used (v1)

- Gate: `src/research/results/pa_batch_bc_gate_diagnostics_v1/`
- Exit: `src/research/results/pa_batch_bc_exit_diagnostics_v1/`
- P0 summary: `src/research/results/p0_correctness_cleanup_summary.md`

### Findings per strategy

| Strategy | Gate / exit takeaway | v2 intent |
|----------|------------------------|-----------|
| `pa_broad_channel_zone` | ~1.4k broad-bull bars; **0** passed hard lower-third ceiling | Add **`signal.zone_max_frac`** (default = old 1/3); grid tests **0.5, 2/3** |
| `pa_generic_breakout_pullback` | 0 finals; cascade before geometry | Loosen **pullback band, overlap, followthrough, min depth** via YAML only |
| `pa_buy_sell_close_trend` | Strong rate; **max-hold-heavy** exits; v1 shortened holds hurt PF | **Longer** `max_hold_minutes`, moderate body/trend, optional `require_vwap_side` |
| `pa_climax_reversal` | v1 strict YAMLs viable; exit mix stop/target balanced | **Small** hull around v1 thresholds |
| `pa_second_entry_pullback` | Very sparse | Slightly looser **context_score_min**, deeper pullback, YAML only |
| `pa_wedge_reversal` | Weak edge at scale | **Small** retest grid only |

## Strategies to rerun

All six Batch B/C PA strategies above, **subject to gate preflight**: if preflight `final_valid_signals == 0`, mark **DEFER** and skip full sweep unless a proof run is explicitly needed.

## Tuned YAMLs (new files)

| File | Raw grid |
|------|----------|
| `src/strategies/testing_parameters/pa_broad_channel_zone_tuned_v2.yaml` | 972 |
| `src/strategies/testing_parameters/pa_generic_breakout_pullback_tuned_v2.yaml` | 576 |
| `src/strategies/testing_parameters/pa_buy_sell_close_trend_tuned_v2.yaml` | 576 |
| `src/strategies/testing_parameters/pa_climax_reversal_tuned_v2.yaml` | 576 |
| `src/strategies/testing_parameters/pa_second_entry_pullback_tuned_v2.yaml` | 576 |
| `src/strategies/testing_parameters/pa_wedge_reversal_tuned_v2.yaml` | 144 |

All **≤ 1500**, no silent `max_combos` cap.

## Code parameterization

- **`pa_broad_channel_zone` only:** `signal.zone_max_frac` (default `1/3` ≡ prior `close <= pa_range_lower_third` behavior). Tunable buy-zone depth in **prior rolling range** fraction from `range_low`.
- **Other strategies:** YAML-only; no default behavior change elsewhere.

## Candidate thresholds

**Strict (Layer 1):** `min_trades=30`, `min_profit_factor=1.05`, `min_total_r=0`, `max_drawdown_r=-50`, `max_avg_bars_held=120`, `max_eod_count=0`, `max_end_of_data_count=0`, `top_per_strategy=5`.

**Diagnostic relaxed:** `min_trades=15`, `min_profit_factor=1.00`, `min_total_r=-3`, `max_drawdown_r=-60`, `max_avg_bars_held=150`, same EOD/EOD data caps, `top_per_strategy=5`. **DIAGNOSTIC ONLY** — not authoritative.

## Explicit non-runs

- No new non–Batch B/C PA strategies  
- No **Layer 2** execution (design doc only if decision = PROCEED)  
- No **mini-WFO**, **full WFO**, **live/paper**  
- No global **shorts**, no **trailing stops**  
- No blind mega-grids beyond sizes above  
