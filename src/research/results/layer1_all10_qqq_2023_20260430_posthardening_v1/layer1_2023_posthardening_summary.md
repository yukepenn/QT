# Layer 1 — QQQ post-hardening (2023-01-01 → 2026-04-30)

## 1. Data window

- **Symbol:** QQQ only (RTH 1-min).
- **Requested:** 2023-01-01 → 2026-04-30.
- **Representative read_bars check:** ~323,820 rows, ~834 sessions, duplicates dropped: 0 (see smoke read in validation log).

## 2. Hardening status

- Sweeps executed with **Commits A–D** code on `main` (`validate_config`, execution validation, feature keys, metrics).
- This is a **shorter window** than full 2020–2026; use for **pipeline verification**, not as a final long-history library.

## 3. Strategy sweep completion

All **10** registered strategies ran with `status=ok` in `sweep_manifest.csv` (see manifest for per-strategy `elapsed_sec`, `result_rows`, best metrics).

| Strategy | Notes |
|----------|--------|
| afternoon_continuation | ok |
| failed_orb | ok |
| gap_acceptance_failure | ok |
| midday_compression_breakout | ok (large grid; many low-trade rows) |
| orb_continuation | ok |
| orb_retest_continuation | ok |
| prior_day_level_trap | ok |
| vwap_reclaim_reject | ok |
| vwap_reversal | ok (best row still heavily negative **total_r** in-window) |
| vwap_trend_pullback | ok |

## 4. Candidate selection thresholds

- **Strict:** `min_trades=80`, `min_profit_factor=1.05`, `min_total_r=0`, `max_drawdown_r=-60`, `max_avg_bars_held=90`, `max_eod_count=0`, `max_end_of_data_count=0`.
- **Relaxed fallback:** `--allow-relaxed-fallback` with `relaxed_min_trades=40`, `relaxed_min_pf=1.0`, `relaxed_min_total_r=-5`, `relaxed_max_drawdown_r=-80`.
- **Top per strategy:** 5 (`--top-per-strategy 5`).

## 5. Selected candidates

- **Total YAMLs:** 39 (`selected_candidates/*.yaml`).

## 6. Candidates by strategy

From selection output: `failed_orb` (5), `gap_acceptance_failure` (5), `orb_continuation` (5), `orb_retest_continuation` (5), `prior_day_level_trap` (5), `vwap_reclaim_reject` (5), `vwap_trend_pullback` (5), `afternoon_continuation` (4).

## 7. Strict vs relaxed

- Rows with **`warn=relaxed_filter`** in `candidate_summary.md`: **vwap_reclaim_reject** (all 5) and **vwap_trend_pullback** (all 5). Others listed under strict pass in the summary (empty `warn`).

## 8. No-candidate strategies

- **midday_compression_breakout:** no rows passed strict or relaxed filters.
- **vwap_reversal:** no rows passed filters (best sweep metrics remain unacceptable under thresholds).

## 9. Main observations

- Library is **skewed** toward opening/trap/ORB families; **no midday_compression** and **no vwap_reversal** candidates.
- **VWAP** entries rely on **relaxed** thresholds — interpret Layer 2 VWAP-heavy systems cautiously.

## 10. Next Layer 2 roots

- **Strict:** `src/combiner/results/layer2_qqq_2023_20260430_posthardening_strict_v1/`
- **Relaxed:** `src/combiner/results/layer2_qqq_2023_20260430_posthardening_relaxed_v1/`
- **Configs:** `layer2_qqq_2023_20260430_posthardening_{strict,relaxed}.yaml` and matching `layer2_sweep_*.yaml`.
