# Full-period diagnostics summary

- **Date range:** QQQ 2020-01-01 → 2026-04-30
- **Candidates in table:** 15
- **Total signals (sum):** 7990

## Signals by strategy

              strategy  signals
            failed_orb     4132
gap_acceptance_failure     2022
  prior_day_level_trap     1836

## Signals by family

          family  signals
opening_reversal     4132
    gap_behavior     2022
  key_level_trap     1836

## Zero-signal candidates

*(none)*

## Top 20 same-bar overlap pairs

               candidate_a                candidate_b  same_bar_overlap  opposite_side_same_bar  same_direction_same_bar
            FAILED_ORB_001             FAILED_ORB_003               836                       0                      836
            FAILED_ORB_001             FAILED_ORB_004               836                       0                      836
            FAILED_ORB_001             FAILED_ORB_005               836                       0                      836
            FAILED_ORB_003             FAILED_ORB_004               836                       0                      836
            FAILED_ORB_003             FAILED_ORB_005               836                       0                      836
            FAILED_ORB_004             FAILED_ORB_005               836                       0                      836
            FAILED_ORB_001             FAILED_ORB_002               788                       0                      788
            FAILED_ORB_002             FAILED_ORB_003               788                       0                      788
            FAILED_ORB_002             FAILED_ORB_004               788                       0                      788
            FAILED_ORB_002             FAILED_ORB_005               788                       0                      788
GAP_ACCEPTANCE_FAILURE_001 GAP_ACCEPTANCE_FAILURE_002               403                       0                      403
GAP_ACCEPTANCE_FAILURE_001 GAP_ACCEPTANCE_FAILURE_003               403                       0                      403
GAP_ACCEPTANCE_FAILURE_001 GAP_ACCEPTANCE_FAILURE_004               403                       0                      403
GAP_ACCEPTANCE_FAILURE_001 GAP_ACCEPTANCE_FAILURE_005               403                       0                      403
GAP_ACCEPTANCE_FAILURE_002 GAP_ACCEPTANCE_FAILURE_003               403                       0                      403
GAP_ACCEPTANCE_FAILURE_002 GAP_ACCEPTANCE_FAILURE_004               403                       0                      403
GAP_ACCEPTANCE_FAILURE_002 GAP_ACCEPTANCE_FAILURE_005               403                       0                      403
GAP_ACCEPTANCE_FAILURE_003 GAP_ACCEPTANCE_FAILURE_004               403                       0                      403
GAP_ACCEPTANCE_FAILURE_003 GAP_ACCEPTANCE_FAILURE_005               403                       0                      403
GAP_ACCEPTANCE_FAILURE_004 GAP_ACCEPTANCE_FAILURE_005               403                       0                      403

## Top 20 same-day overlap pairs (session-day count)

               candidate_a                candidate_b  same_day_overlap  same_bar_overlap
            FAILED_ORB_001             FAILED_ORB_003               836               836
            FAILED_ORB_001             FAILED_ORB_004               836               836
            FAILED_ORB_001             FAILED_ORB_005               836               836
            FAILED_ORB_003             FAILED_ORB_004               836               836
            FAILED_ORB_003             FAILED_ORB_005               836               836
            FAILED_ORB_004             FAILED_ORB_005               836               836
            FAILED_ORB_001             FAILED_ORB_002               788               788
            FAILED_ORB_002             FAILED_ORB_003               788               788
            FAILED_ORB_002             FAILED_ORB_004               788               788
            FAILED_ORB_002             FAILED_ORB_005               788               788
GAP_ACCEPTANCE_FAILURE_001 GAP_ACCEPTANCE_FAILURE_002               403               403
GAP_ACCEPTANCE_FAILURE_001 GAP_ACCEPTANCE_FAILURE_003               403               403
GAP_ACCEPTANCE_FAILURE_001 GAP_ACCEPTANCE_FAILURE_004               403               403
GAP_ACCEPTANCE_FAILURE_001 GAP_ACCEPTANCE_FAILURE_005               403               403
GAP_ACCEPTANCE_FAILURE_002 GAP_ACCEPTANCE_FAILURE_003               403               403
GAP_ACCEPTANCE_FAILURE_002 GAP_ACCEPTANCE_FAILURE_004               403               403
GAP_ACCEPTANCE_FAILURE_002 GAP_ACCEPTANCE_FAILURE_005               403               403
GAP_ACCEPTANCE_FAILURE_003 GAP_ACCEPTANCE_FAILURE_004               403               403
GAP_ACCEPTANCE_FAILURE_003 GAP_ACCEPTANCE_FAILURE_005               403               403
GAP_ACCEPTANCE_FAILURE_004 GAP_ACCEPTANCE_FAILURE_005               403               403

## Top opposite-side same-bar pairs

   candidate_a                candidate_b  opposite_side_same_bar  same_bar_overlap
FAILED_ORB_001             FAILED_ORB_002                       0               788
FAILED_ORB_001             FAILED_ORB_003                       0               836
FAILED_ORB_001             FAILED_ORB_004                       0               836
FAILED_ORB_001             FAILED_ORB_005                       0               836
FAILED_ORB_001 GAP_ACCEPTANCE_FAILURE_001                       0                56
FAILED_ORB_001 GAP_ACCEPTANCE_FAILURE_002                       0                56
FAILED_ORB_001 GAP_ACCEPTANCE_FAILURE_003                       0                56
FAILED_ORB_001 GAP_ACCEPTANCE_FAILURE_004                       0                56
FAILED_ORB_001 GAP_ACCEPTANCE_FAILURE_005                       0                56
FAILED_ORB_001   PRIOR_DAY_LEVEL_TRAP_001                       0                 4
FAILED_ORB_001   PRIOR_DAY_LEVEL_TRAP_002                       0                 4
FAILED_ORB_001   PRIOR_DAY_LEVEL_TRAP_003                       0                 4
FAILED_ORB_001   PRIOR_DAY_LEVEL_TRAP_004                       0                 4
FAILED_ORB_001   PRIOR_DAY_LEVEL_TRAP_005                       0                 4
FAILED_ORB_002             FAILED_ORB_003                       0               788

## Interpreting overlap for multi-candidate systems

Non-zero **same_bar_overlap** means two candidates sometimes fire on the same bar; the combiner picks one via priority / score. Use **opposite_side_same_bar** to see whether pairs disagree on direction on those bars (more complementary) vs same-direction crowding.
