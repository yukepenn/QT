# Layer 1 — QQQ full history post-hardening v1

In-sample research only (2020-01-01 → 2026-04-30 on QQQ RTH). Not live-ready.

## 1. Data window

- **Symbol:** QQQ (equity), 1-min RTH bars only.
- **Start / end:** 2020-01-01 → 2026-04-30 (1,588 NY sessions; 617,160 rows in `read_bars` smoke check).

## 2. Hardening status

Layer 2 / Layer 1 tooling uses the post-hardening stack (validation, feature keys, execution checks, combiner behavior/cost helpers). No change to strategy signal logic in this phase.

## 3. Strategy sweep completion

All **10** strategies ran with `*_focused.yaml` grids, tag `layer1_qqq_2020_20260430_posthardening_v1`. Source: `sweep_manifest.csv`.

| strategy | grid_size | combos_done | elapsed_sec | result_rows | best_pf | best_total_r | best_trades |
|----------|-----------|-------------|-------------|-------------|---------|--------------|-------------|
| afternoon_continuation | 256 | 256 | 36.8 | 256 | 1.149 | 26.89 | 789 |
| failed_orb | 768 | 768 | 80.8 | 768 | 1.197 | 55.83 | 836 |
| gap_acceptance_failure | 192 | 192 | 33.0 | 192 | 1.281 | 41.56 | 403 |
| midday_compression_breakout | 31104 | 31104 | 650.4 | 31104 | inf | 0.98 | 1 |
| orb_continuation | 512 | 512 | 141.7 | 512 | 1.008 | 2.17 | 989 |
| orb_retest_continuation | 256 | 256 | 64.7 | 256 | 1.037 | 36.59 | 980 |
| prior_day_level_trap | 512 | 512 | 38.1 | 512 | 1.117 | 6.59 | 359 |
| vwap_reclaim_reject | 512 | 512 | 27.3 | 512 | 1.006 | 24.94 | 594 |
| vwap_reversal | 480 | 480 | 22.9 | 480 | 1.108 | -327.15 | 980 |
| vwap_trend_pullback | 512 | 512 | 20.2 | 512 | 1.021 | 1.36 | 460 |

**Approximate total sweep wall time:** ~1,116 s (~18.6 min) on this machine (dominated by `midday_compression_breakout` grid).

## 4. Candidate selection thresholds

Command (manifest mode):

```text
python src/research/select_candidates.py --manifest src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1/sweep_manifest.csv --output-root src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1 --top-per-strategy 5 --min-trades 150 --min-profit-factor 1.05 --min-total-r 0 --max-drawdown-r -100 --max-avg-bars-held 90 --max-eod-count 0 --max-end-of-data-count 0 --allow-relaxed-fallback --relaxed-min-trades 80 --relaxed-min-profit-factor 1.00 --relaxed-min-total-r -10 --relaxed-max-drawdown-r -120
```

## 5. Selected candidates count

- **27** YAMLs under `selected_candidates/`.
- **15** rows used **strict** filters (`filters_used=strict` in `selected_candidates.csv`).
- **12** rows used **relaxed** fallback (`relaxed_filter` warning / `filters_used=relaxed`).

## 6. Candidates by strategy

| strategy | count | notes |
|----------|-------|--------|
| failed_orb | 5 | strict |
| gap_acceptance_failure | 5 | strict |
| prior_day_level_trap | 5 | strict |
| orb_retest_continuation | 5 | relaxed |
| orb_continuation | 3 | relaxed |
| vwap_trend_pullback | 2 | relaxed |
| afternoon_continuation | 1 | relaxed |
| vwap_reclaim_reject | 1 | relaxed |

## 7. Strict vs relaxed

- **Strict-only families:** failed_orb, gap_acceptance_failure, prior_day_level_trap (all five slots filled per strategy where applicable).
- **Relaxed-only:** afternoon_continuation, orb_continuation, orb_retest_continuation, vwap_reclaim_reject, vwap_trend_pullback (weak Layer 1 scores for some ORB rows, but passed relaxed gates).

## 8. No-candidate strategies

- **midday_compression_breakout:** no row passed strict or relaxed filters (grid is huge; best visible stats are not economically meaningful at one-trade rows).
- **vwap_reversal:** no row passed (manifest best_total_r deeply negative on best_pf row).

## 9. Comparison vs 2023 shorter-window library

- **2023 post-hardening v1:** 39 candidates across 8 strategies; `midday_compression_breakout` and `vwap_reversal` had no selections.
- **2020–2026 v1:** 27 candidates across **8** strategies with the same two strategies empty. The longer window yields fewer top-per-strategy slots that meet strict gates; opening/trap families still dominate the strict core.

## 10. Main observations

- **failed_orb** and **gap_acceptance_failure** remain the strongest strict Layer 1 scores on full history.
- **ORB continuation** candidates are marginal (negative `candidate_score` in YAML export) but cleared relaxed thresholds — treat as research-only.
- **vwap_reversal** remains structurally weak on this grid over the full sample.
- This is **single-window in-sample** fitting; any edge may not generalize.

## 11. Next Layer 2 roots

- Strict: `src/combiner/results/layer2_qqq_2020_20260430_posthardening_strict_v1/`
- Relaxed: `src/combiner/results/layer2_qqq_2020_20260430_posthardening_relaxed_v1/`
- Configs: `src/combiner/configs/layer2_qqq_2020_20260430_posthardening_{strict,relaxed}.yaml` and matching `layer2_sweep_*.yaml`.
