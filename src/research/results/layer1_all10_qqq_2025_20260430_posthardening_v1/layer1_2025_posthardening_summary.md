# Layer 1 — QQQ recent window post-hardening v1

In-sample research only (2025-01-01 → 2026-04-30 on QQQ RTH). Not live-ready.

## 1. Data window

- **Symbol:** QQQ only.
- **Start / end:** 2025-01-01 → 2026-04-30.
- **Smoke read_bars check (2025-01):** `rows=7800`, `unique_ny_dates=20`, duplicates dropped: 0.

## 2. Sweep completion

All **10** registered strategies ran with `*_focused.yaml` grids, tag `layer1_qqq_2025_20260430_posthardening_v1`. Source: `sweep_manifest.csv`.

| strategy | grid_size | elapsed_sec | result_rows | best_pf | best_total_r | best_trades | sweep_folder |
|----------|-----------|-------------|-------------|---------|--------------|-------------|--------------|
| afternoon_continuation | 256 | 9.369 | 256 | 1.0468 | -9.23 | 128 | sweep_20260506_022131_layer1_qqq_2025_20260430_posthardening_v1 |
| failed_orb | 768 | 12.910 | 768 | 1.5461 | 46.49 | 234 | sweep_20260506_022144_layer1_qqq_2025_20260430_posthardening_v1 |
| gap_acceptance_failure | 192 | 7.372 | 192 | 1.6075 | 12.44 | 73 | sweep_20260506_022151_layer1_qqq_2025_20260430_posthardening_v1 |
| midday_compression_breakout | 31104 | 64.847 | 31104 | inf | 3.94 | 1 | sweep_20260506_022257_layer1_qqq_2025_20260430_posthardening_v1 |
| orb_continuation | 512 | 18.791 | 512 | 1.3713 | 33.04 | 239 | sweep_20260506_022316_layer1_qqq_2025_20260430_posthardening_v1 |
| orb_retest_continuation | 256 | 11.774 | 256 | 1.5277 | 37.73 | 196 | sweep_20260506_022328_layer1_qqq_2025_20260430_posthardening_v1 |
| prior_day_level_trap | 512 | 7.990 | 512 | 1.5330 | 10.19 | 71 | sweep_20260506_022336_layer1_qqq_2025_20260430_posthardening_v1 |
| vwap_reclaim_reject | 512 | 8.335 | 512 | 1.1224 | 22.25 | 192 | sweep_20260506_022345_layer1_qqq_2025_20260430_posthardening_v1 |
| vwap_reversal | 480 | 9.254 | 480 | 1.5173 | -39.53 | 182 | sweep_20260506_022354_layer1_qqq_2025_20260430_posthardening_v1 |
| vwap_trend_pullback | 512 | 7.794 | 512 | 1.0973 | -14.46 | 148 | sweep_20260506_022402_layer1_qqq_2025_20260430_posthardening_v1 |

## 3. Candidate selection thresholds

Command (manifest mode):

```text
python src/research/select_candidates.py --manifest src/research/results/layer1_all10_qqq_2025_20260430_posthardening_v1/sweep_manifest.csv --output-root src/research/results/layer1_all10_qqq_2025_20260430_posthardening_v1 --top-per-strategy 5 --min-trades 30 --min-profit-factor 1.05 --min-total-r 0 --max-drawdown-r -40 --max-avg-bars-held 90 --max-eod-count 0 --max-end-of-data-count 0 --allow-relaxed-fallback --relaxed-min-trades 15 --relaxed-min-profit-factor 1.00 --relaxed-min-total-r -5 --relaxed-max-drawdown-r -60
```

## 4. Selected candidates

- **Total YAMLs:** 40 under `selected_candidates/`.
- **Strict:** 30 (`filters_used=strict`).
- **Relaxed:** 10 (`filters_used=relaxed`, `warning=relaxed_filter`).

## 5. Candidates by strategy

From the YAML export:

- **failed_orb** (5, strict)
- **orb_retest_continuation** (5, strict)
- **orb_continuation** (5, strict)
- **gap_acceptance_failure** (5, strict)
- **prior_day_level_trap** (5, strict)
- **vwap_reclaim_reject** (5, strict)
- **afternoon_continuation** (5, relaxed_filter)
- **vwap_trend_pullback** (5, relaxed_filter)

## 6. No-candidate strategies

- **midday_compression_breakout:** no rows passed filters (strict or relaxed). (Manifest best PF is `inf` on a 1-trade row; not meaningful.)
- **vwap_reversal:** no rows passed filters (strict or relaxed), despite manifest best PF being high; best rows are negative total R in-window.

## 7. Top recent-window strategy families (Layer 1)

Based on the best candidate scores in `candidate_summary.md` (higher is better):

1. **ORB retest** (orb_retest_continuation): strongest scores (~1.73–1.89), healthy trade counts (~196–206), PF ~1.42–1.53.
2. **Opening reversal / failed ORB** (failed_orb): strong scores (~1.71–1.79), PF ~1.45–1.55, trades ~231–241.
3. **ORB continuation** (orb_continuation): solid scores (~1.52–1.56), PF ~1.30–1.37, trades ~211–244.
4. **Gap + key-level traps** (gap_acceptance_failure, prior_day_level_trap): good scores (~1.45–1.52) but lower trade counts (~71–74).
5. **VWAP reclaim/reject** (vwap_reclaim_reject): modest scores (~0.93–1.17), PF ~1.08–1.12.
6. **Afternoon continuation** and **VWAP trend pullback**: only pass via relaxed fallback in this recent window.

## 8. Comparison vs 2023–2026 (post-hardening v1)

Reference root:
`src/research/results/layer1_all10_qqq_2023_20260430_posthardening_v1/`

- Candidate breadth is similar: **40** YAMLs (2025–2026) vs **39** YAMLs (2023–2026), across **8** strategies.
- The same two strategies remain empty under these gates: **midday_compression_breakout** and **vwap_reversal**.
- Recent window shows a strong ORB/failed-ORB core, consistent with 2023–2026 behavior.

## 9. Comparison vs 2020–2026 (full history post-hardening v1)

Reference root:
`src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1/`

- Candidate count is higher here (**40**) vs full-history (**27**), but note we used **lower thresholds** for the shorter recent window.
- In the full-history run, several families only cleared **relaxed** filters; in this recent window, **ORB continuation / ORB retest / VWAP reclaim-reject** clear **strict** gates more readily.

## 10. Recommendation (next step)

- This recent window looks strong enough to justify a **Layer 2 recent-window check** (separately), but treat conclusions as **regime-dependent** and **in-sample**.
- No Layer 2 run was executed in this task.

