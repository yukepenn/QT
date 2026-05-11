# Full-period diagnostics summary

- **Date range:** QQQ 2025-01-01 → 2026-04-30
- **Candidates in table:** 40
- **Total signals (sum):** 6327

## Signals by strategy

               strategy  signals
             failed_orb     1173
       orb_continuation     1136
    vwap_reclaim_reject      994
orb_retest_continuation      990
    vwap_trend_pullback      674
 afternoon_continuation      640
 gap_acceptance_failure      365
   prior_day_level_trap      355

## Signals by family

          family  signals
opening_momentum     2126
opening_reversal     1173
    vwap_reclaim      994
      vwap_trend      674
 afternoon_trend      640
    gap_behavior      365
  key_level_trap      355

## Zero-signal candidates

*(none)*

## Top 20 same-bar overlap pairs

                candidate_a                 candidate_b  same_bar_overlap  opposite_side_same_bar  same_direction_same_bar
       ORB_CONTINUATION_001        ORB_CONTINUATION_002               239                       0                      239
             FAILED_ORB_002              FAILED_ORB_004               234                       0                      234
       ORB_CONTINUATION_001        ORB_CONTINUATION_004               231                       0                      231
       ORB_CONTINUATION_002        ORB_CONTINUATION_004               231                       0                      231
             FAILED_ORB_001              FAILED_ORB_003               223                       0                      223
             FAILED_ORB_002              FAILED_ORB_005               220                       0                      220
             FAILED_ORB_004              FAILED_ORB_005               220                       0                      220
             FAILED_ORB_001              FAILED_ORB_005               214                       0                      214
             FAILED_ORB_002              FAILED_ORB_003               211                       0                      211
             FAILED_ORB_003              FAILED_ORB_004               211                       0                      211
       ORB_CONTINUATION_003        ORB_CONTINUATION_005               211                       0                      211
             FAILED_ORB_001              FAILED_ORB_002               206                       0                      206
             FAILED_ORB_001              FAILED_ORB_004               206                       0                      206
             FAILED_ORB_003              FAILED_ORB_005               204                       0                      204
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_002               196                       0                      196
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_003               196                       0                      196
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_004               196                       0                      196
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_005               196                       0                      196
ORB_RETEST_CONTINUATION_002 ORB_RETEST_CONTINUATION_003               196                       0                      196
ORB_RETEST_CONTINUATION_002 ORB_RETEST_CONTINUATION_004               196                       0                      196

## Top 20 same-day overlap pairs (session-day count)

            candidate_a                 candidate_b  same_day_overlap  same_bar_overlap
   ORB_CONTINUATION_001        ORB_CONTINUATION_002               239               239
         FAILED_ORB_002              FAILED_ORB_003               234               211
         FAILED_ORB_002              FAILED_ORB_004               234               234
         FAILED_ORB_003              FAILED_ORB_004               234               211
         FAILED_ORB_001              FAILED_ORB_002               233               206
         FAILED_ORB_001              FAILED_ORB_003               233               223
         FAILED_ORB_001              FAILED_ORB_004               233               206
         FAILED_ORB_001              FAILED_ORB_005               231               214
         FAILED_ORB_002              FAILED_ORB_005               231               220
         FAILED_ORB_003              FAILED_ORB_005               231               204
         FAILED_ORB_004              FAILED_ORB_005               231               220
   ORB_CONTINUATION_001        ORB_CONTINUATION_004               231               231
   ORB_CONTINUATION_002        ORB_CONTINUATION_004               231               231
   ORB_CONTINUATION_001        ORB_CONTINUATION_003               211                94
   ORB_CONTINUATION_001        ORB_CONTINUATION_005               211                94
   ORB_CONTINUATION_002        ORB_CONTINUATION_003               211                94
   ORB_CONTINUATION_002        ORB_CONTINUATION_005               211                94
   ORB_CONTINUATION_003        ORB_CONTINUATION_005               211               211
VWAP_RECLAIM_REJECT_004     VWAP_RECLAIM_REJECT_005               207               159
   ORB_CONTINUATION_001 ORB_RETEST_CONTINUATION_002               206                70

## Top opposite-side same-bar pairs

               candidate_a                candidate_b  opposite_side_same_bar  same_bar_overlap
AFTERNOON_CONTINUATION_001 AFTERNOON_CONTINUATION_002                       0               123
AFTERNOON_CONTINUATION_001 AFTERNOON_CONTINUATION_003                       0               123
AFTERNOON_CONTINUATION_001 AFTERNOON_CONTINUATION_004                       0               123
AFTERNOON_CONTINUATION_001 AFTERNOON_CONTINUATION_005                       0               123
AFTERNOON_CONTINUATION_001             FAILED_ORB_001                       0                 0
AFTERNOON_CONTINUATION_001             FAILED_ORB_002                       0                 0
AFTERNOON_CONTINUATION_001             FAILED_ORB_003                       0                 0
AFTERNOON_CONTINUATION_001             FAILED_ORB_004                       0                 0
AFTERNOON_CONTINUATION_001             FAILED_ORB_005                       0                 0
AFTERNOON_CONTINUATION_001 GAP_ACCEPTANCE_FAILURE_001                       0                 0
AFTERNOON_CONTINUATION_001 GAP_ACCEPTANCE_FAILURE_002                       0                 0
AFTERNOON_CONTINUATION_001 GAP_ACCEPTANCE_FAILURE_003                       0                 0
AFTERNOON_CONTINUATION_001 GAP_ACCEPTANCE_FAILURE_004                       0                 0
AFTERNOON_CONTINUATION_001 GAP_ACCEPTANCE_FAILURE_005                       0                 0
AFTERNOON_CONTINUATION_001       ORB_CONTINUATION_001                       0                 0

## Interpreting overlap for multi-candidate systems

Non-zero **same_bar_overlap** means two candidates sometimes fire on the same bar; the combiner picks one via priority / score. Use **opposite_side_same_bar** to see whether pairs disagree on direction on those bars (more complementary) vs same-direction crowding.
