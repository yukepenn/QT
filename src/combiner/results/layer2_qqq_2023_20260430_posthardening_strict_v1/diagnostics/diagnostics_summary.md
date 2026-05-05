# Full-period diagnostics summary

- **Date range:** 2023-01-01 — 2026-04-30
- **Candidates in table:** 29
- **Total signals (sum):** 11017

## Signals by strategy

               strategy  signals
       orb_continuation     2799
orb_retest_continuation     2645
             failed_orb     2134
 afternoon_continuation     1628
   prior_day_level_trap      991
 gap_acceptance_failure      820

## Signals by family

          family  signals
opening_momentum     5444
opening_reversal     2134
 afternoon_trend     1628
  key_level_trap      991
    gap_behavior      820

## Zero-signal candidates

*(none)*

## Top 20 same-bar overlap pairs

                candidate_a                 candidate_b  same_bar_overlap  opposite_side_same_bar  same_direction_same_bar
       ORB_CONTINUATION_001        ORB_CONTINUATION_003               579                       0                      579
       ORB_CONTINUATION_001        ORB_CONTINUATION_004               579                       0                      579
       ORB_CONTINUATION_003        ORB_CONTINUATION_004               579                       0                      579
ORB_RETEST_CONTINUATION_002 ORB_RETEST_CONTINUATION_004               547                       0                      547
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_002               517                       0                      517
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_003               517                       0                      517
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_004               517                       0                      517
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_005               517                       0                      517
ORB_RETEST_CONTINUATION_002 ORB_RETEST_CONTINUATION_003               517                       0                      517
ORB_RETEST_CONTINUATION_002 ORB_RETEST_CONTINUATION_005               517                       0                      517
ORB_RETEST_CONTINUATION_003 ORB_RETEST_CONTINUATION_004               517                       0                      517
ORB_RETEST_CONTINUATION_003 ORB_RETEST_CONTINUATION_005               517                       0                      517
ORB_RETEST_CONTINUATION_004 ORB_RETEST_CONTINUATION_005               517                       0                      517
       ORB_CONTINUATION_002        ORB_CONTINUATION_005               510                       0                      510
             FAILED_ORB_003              FAILED_ORB_004               458                       0                      458
 AFTERNOON_CONTINUATION_001  AFTERNOON_CONTINUATION_002               407                       0                      407
 AFTERNOON_CONTINUATION_001  AFTERNOON_CONTINUATION_003               407                       0                      407
 AFTERNOON_CONTINUATION_001  AFTERNOON_CONTINUATION_004               407                       0                      407
 AFTERNOON_CONTINUATION_002  AFTERNOON_CONTINUATION_003               407                       0                      407
 AFTERNOON_CONTINUATION_002  AFTERNOON_CONTINUATION_004               407                       0                      407

## Top 20 same-day overlap pairs (session-day count)

                candidate_a                 candidate_b  same_day_overlap  same_bar_overlap
       ORB_CONTINUATION_001        ORB_CONTINUATION_003               579               579
       ORB_CONTINUATION_001        ORB_CONTINUATION_004               579               579
       ORB_CONTINUATION_003        ORB_CONTINUATION_004               579               579
ORB_RETEST_CONTINUATION_002 ORB_RETEST_CONTINUATION_004               547               547
       ORB_CONTINUATION_004 ORB_RETEST_CONTINUATION_002               538               238
       ORB_CONTINUATION_004 ORB_RETEST_CONTINUATION_004               538               238
       ORB_CONTINUATION_001 ORB_RETEST_CONTINUATION_002               535               238
       ORB_CONTINUATION_001 ORB_RETEST_CONTINUATION_004               535               238
       ORB_CONTINUATION_003 ORB_RETEST_CONTINUATION_002               535               238
       ORB_CONTINUATION_003 ORB_RETEST_CONTINUATION_004               535               238
       ORB_CONTINUATION_001        ORB_CONTINUATION_002               521               341
       ORB_CONTINUATION_001        ORB_CONTINUATION_005               521               330
       ORB_CONTINUATION_002        ORB_CONTINUATION_003               521               341
       ORB_CONTINUATION_002        ORB_CONTINUATION_004               521               341
       ORB_CONTINUATION_002        ORB_CONTINUATION_005               521               510
       ORB_CONTINUATION_003        ORB_CONTINUATION_005               521               330
       ORB_CONTINUATION_004        ORB_CONTINUATION_005               521               330
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_002               517               517
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_003               517               517
ORB_RETEST_CONTINUATION_001 ORB_RETEST_CONTINUATION_004               517               517

## Top opposite-side same-bar pairs

               candidate_a                candidate_b  opposite_side_same_bar  same_bar_overlap
AFTERNOON_CONTINUATION_001 AFTERNOON_CONTINUATION_002                       0               407
AFTERNOON_CONTINUATION_001 AFTERNOON_CONTINUATION_003                       0               407
AFTERNOON_CONTINUATION_001 AFTERNOON_CONTINUATION_004                       0               407
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
AFTERNOON_CONTINUATION_001       ORB_CONTINUATION_002                       0                 0

## Interpreting overlap for multi-candidate systems

Non-zero **same_bar_overlap** means two candidates sometimes fire on the same bar; the combiner picks one via priority / score. Use **opposite_side_same_bar** to see whether pairs disagree on direction on those bars (more complementary) vs same-direction crowding.
