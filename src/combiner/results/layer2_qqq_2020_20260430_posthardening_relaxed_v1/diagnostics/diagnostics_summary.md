# Full-period diagnostics summary

- **Date range:** QQQ 2020-01-01 → 2026-04-30
- **Candidates in table:** 27
- **Total signals (sum):** 18271

## Signals by strategy

               strategy  signals
orb_retest_continuation     4900
             failed_orb     4132
       orb_continuation     3078
 gap_acceptance_failure     2022
   prior_day_level_trap     1836
    vwap_trend_pullback      920
 afternoon_continuation      789
    vwap_reclaim_reject      594

## Signals by family

          family  signals
opening_momentum     7978
opening_reversal     4132
    gap_behavior     2022
  key_level_trap     1836
      vwap_trend      920
 afternoon_trend      789
    vwap_reclaim      594

## Zero-signal candidates

*(none)*

## Top 20 same-bar overlap pairs

                candidate_a                 candidate_b  same_bar_overlap  opposite_side_same_bar  same_direction_same_bar
       ORB_CONTINUATION_001        ORB_CONTINUATION_003               989                       0                      989
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_002               980                       0                      980
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_003               980                       0                      980
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_004               980                       0                      980
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_005               980                       0                      980
ORB_RETEST_CONTINUATION_002 ORB_RETEST_CONTINUATION_003               980                       0                      980
ORB_RETEST_CONTINUATION_002 ORB_RETEST_CONTINUATION_004               980                       0                      980
ORB_RETEST_CONTINUATION_002 ORB_RETEST_CONTINUATION_005               980                       0                      980
ORB_RETEST_CONTINUATION_003 ORB_RETEST_CONTINUATION_004               980                       0                      980
ORB_RETEST_CONTINUATION_003 ORB_RETEST_CONTINUATION_005               980                       0                      980
ORB_RETEST_CONTINUATION_004 ORB_RETEST_CONTINUATION_005               980                       0                      980
       ORB_CONTINUATION_001        ORB_CONTINUATION_002               965                       0                      965
       ORB_CONTINUATION_002        ORB_CONTINUATION_003               965                       0                      965
             FAILED_ORB_001              FAILED_ORB_003               836                       0                      836
             FAILED_ORB_001              FAILED_ORB_004               836                       0                      836
             FAILED_ORB_001              FAILED_ORB_005               836                       0                      836
             FAILED_ORB_003              FAILED_ORB_004               836                       0                      836
             FAILED_ORB_003              FAILED_ORB_005               836                       0                      836
             FAILED_ORB_004              FAILED_ORB_005               836                       0                      836
             FAILED_ORB_001              FAILED_ORB_002               788                       0                      788

## Top 20 same-day overlap pairs (session-day count)

                candidate_a                 candidate_b  same_day_overlap  same_bar_overlap
       ORB_CONTINUATION_001        ORB_CONTINUATION_003               989               989
       ORB_CONTINUATION_001        ORB_CONTINUATION_002               988               965
       ORB_CONTINUATION_002        ORB_CONTINUATION_003               988               965
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_002               980               980
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_003               980               980
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_004               980               980
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_005               980               980
ORB_RETEST_CONTINUATION_002 ORB_RETEST_CONTINUATION_003               980               980
ORB_RETEST_CONTINUATION_002 ORB_RETEST_CONTINUATION_004               980               980
ORB_RETEST_CONTINUATION_002 ORB_RETEST_CONTINUATION_005               980               980
ORB_RETEST_CONTINUATION_003 ORB_RETEST_CONTINUATION_004               980               980
ORB_RETEST_CONTINUATION_003 ORB_RETEST_CONTINUATION_005               980               980
ORB_RETEST_CONTINUATION_004 ORB_RETEST_CONTINUATION_005               980               980
       ORB_CONTINUATION_003 ORB_RETEST_CONTINUATION_001               952               570
       ORB_CONTINUATION_003 ORB_RETEST_CONTINUATION_002               952               570
       ORB_CONTINUATION_003 ORB_RETEST_CONTINUATION_003               952               570
       ORB_CONTINUATION_003 ORB_RETEST_CONTINUATION_004               952               570
       ORB_CONTINUATION_003 ORB_RETEST_CONTINUATION_005               952               570
       ORB_CONTINUATION_001 ORB_RETEST_CONTINUATION_001               934               570
       ORB_CONTINUATION_001 ORB_RETEST_CONTINUATION_002               934               570

## Top opposite-side same-bar pairs

               candidate_a                 candidate_b  opposite_side_same_bar  same_bar_overlap
AFTERNOON_CONTINUATION_001              FAILED_ORB_001                       0                 0
AFTERNOON_CONTINUATION_001              FAILED_ORB_002                       0                 0
AFTERNOON_CONTINUATION_001              FAILED_ORB_003                       0                 0
AFTERNOON_CONTINUATION_001              FAILED_ORB_004                       0                 0
AFTERNOON_CONTINUATION_001              FAILED_ORB_005                       0                 0
AFTERNOON_CONTINUATION_001  GAP_ACCEPTANCE_FAILURE_001                       0                 0
AFTERNOON_CONTINUATION_001  GAP_ACCEPTANCE_FAILURE_002                       0                 0
AFTERNOON_CONTINUATION_001  GAP_ACCEPTANCE_FAILURE_003                       0                 0
AFTERNOON_CONTINUATION_001  GAP_ACCEPTANCE_FAILURE_004                       0                 0
AFTERNOON_CONTINUATION_001  GAP_ACCEPTANCE_FAILURE_005                       0                 0
AFTERNOON_CONTINUATION_001        ORB_CONTINUATION_001                       0                 0
AFTERNOON_CONTINUATION_001        ORB_CONTINUATION_002                       0                 0
AFTERNOON_CONTINUATION_001        ORB_CONTINUATION_003                       0                 0
AFTERNOON_CONTINUATION_001 ORB_RETEST_CONTINUATION_001                       0                 0
AFTERNOON_CONTINUATION_001 ORB_RETEST_CONTINUATION_002                       0                 0

## Interpreting overlap for multi-candidate systems

Non-zero **same_bar_overlap** means two candidates sometimes fire on the same bar; the combiner picks one via priority / score. Use **opposite_side_same_bar** to see whether pairs disagree on direction on those bars (more complementary) vs same-direction crowding.
