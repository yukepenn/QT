# Layer 1 (QQQ) — 2020-01-01 to 2026-04-30

## 1. Data window

- **Symbol:** QQQ (primary)
- **Start / end (requested):** 2020-01-01 → 2026-04-30
- **Observed in parquet (RTH):** 2020-01-02 09:30 NY → 2026-04-30 15:59 NY
- **Rows:** 617,160
- **Sessions (unique NY dates):** 1,588
- **Duplicates dropped (`read_bars`):** 0

**SPY warning:** current local SPY parquet is incomplete (rows=220,980; sessions=568; missing many months). SPY was validated only and **not** used for this QQQ research run.

## 2. Layer 1 strategy sweep status

Tag: `layer1_qqq_2020_20260430_v1`  
Root: `src/research/results/layer1_all10_qqq_2020_20260430_v1/`

- **Completed (manifest status=ok):** afternoon_continuation, failed_orb, gap_acceptance_failure, midday_compression_breakout, orb_continuation, orb_retest_continuation, prior_day_level_trap, vwap_reclaim_reject, vwap_reversal, vwap_trend_pullback

## 3. Candidate selection result

- **Selected candidates:** 27
- **Strict candidates:** 15
- **Relaxed candidates:** 12

## 4. Candidates by strategy

- **afternoon_continuation:** 1 (relaxed)
- **failed_orb:** 5 (strict)
- **gap_acceptance_failure:** 5 (strict)
- **orb_continuation:** 3 (relaxed)
- **orb_retest_continuation:** 5 (relaxed)
- **prior_day_level_trap:** 5 (strict)
- **vwap_reclaim_reject:** 1 (relaxed)
- **vwap_trend_pullback:** 2 (relaxed)

## 5. Strict vs relaxed candidates

- **Strict:** `failed_orb`, `gap_acceptance_failure`, `prior_day_level_trap`
- **Relaxed:** `afternoon_continuation`, `orb_continuation`, `orb_retest_continuation`, `vwap_reclaim_reject`, `vwap_trend_pullback`

## 6. Strategies with no candidates

- **midday_compression_breakout:** none (strict or relaxed)
- **vwap_reversal:** none (strict or relaxed)

## 7. Main observations

- Candidate universe is dominated by **opening** families (ORB/failed-orb/gap failure) with additional **VWAP control** candidates.
- Several strategies only pass the **relaxed fallback** (notably ORB continuation / retest).

## 8. Next: Layer 2 result path

Layer 2 root: `src/combiner/results/layer2_qqq_2020_20260430_v2_relaxed/`

