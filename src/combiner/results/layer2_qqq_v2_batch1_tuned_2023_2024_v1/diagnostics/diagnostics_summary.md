# Full-period diagnostics summary

- **Date range:** 2023-01-01 — 2024-12-31
- **Candidates in table:** 10
- **Total signals (sum):** 2817

## Signals by strategy

                  strategy  signals
bollinger_squeeze_breakout     1841
         rsi_failure_swing      976

## Signals by family

              family  signals
volatility_expansion     1841
 oscillator_reversal      976

## Zero-signal candidates

*(none)*

## Top 20 same-bar overlap pairs

                   candidate_a                    candidate_b  same_bar_overlap  opposite_side_same_bar  same_direction_same_bar
BOLLINGER_SQUEEZE_BREAKOUT_001 BOLLINGER_SQUEEZE_BREAKOUT_002               376                       0                      376
BOLLINGER_SQUEEZE_BREAKOUT_003 BOLLINGER_SQUEEZE_BREAKOUT_004               363                       0                      363
BOLLINGER_SQUEEZE_BREAKOUT_003 BOLLINGER_SQUEEZE_BREAKOUT_005               357                       0                      357
BOLLINGER_SQUEEZE_BREAKOUT_004 BOLLINGER_SQUEEZE_BREAKOUT_005               357                       0                      357
BOLLINGER_SQUEEZE_BREAKOUT_001 BOLLINGER_SQUEEZE_BREAKOUT_003               310                       0                      310
BOLLINGER_SQUEEZE_BREAKOUT_001 BOLLINGER_SQUEEZE_BREAKOUT_004               310                       0                      310
BOLLINGER_SQUEEZE_BREAKOUT_002 BOLLINGER_SQUEEZE_BREAKOUT_003               310                       0                      310
BOLLINGER_SQUEEZE_BREAKOUT_002 BOLLINGER_SQUEEZE_BREAKOUT_004               310                       0                      310
BOLLINGER_SQUEEZE_BREAKOUT_001 BOLLINGER_SQUEEZE_BREAKOUT_005               307                       0                      307
BOLLINGER_SQUEEZE_BREAKOUT_002 BOLLINGER_SQUEEZE_BREAKOUT_005               307                       0                      307
         RSI_FAILURE_SWING_001          RSI_FAILURE_SWING_002               206                       0                      206
         RSI_FAILURE_SWING_001          RSI_FAILURE_SWING_003               206                       0                      206
         RSI_FAILURE_SWING_001          RSI_FAILURE_SWING_004               206                       0                      206
         RSI_FAILURE_SWING_002          RSI_FAILURE_SWING_003               206                       0                      206
         RSI_FAILURE_SWING_002          RSI_FAILURE_SWING_004               206                       0                      206
         RSI_FAILURE_SWING_003          RSI_FAILURE_SWING_004               206                       0                      206
         RSI_FAILURE_SWING_001          RSI_FAILURE_SWING_005               132                       0                      132
         RSI_FAILURE_SWING_002          RSI_FAILURE_SWING_005               132                       0                      132
         RSI_FAILURE_SWING_003          RSI_FAILURE_SWING_005               132                       0                      132
         RSI_FAILURE_SWING_004          RSI_FAILURE_SWING_005               132                       0                      132

## Top 20 same-day overlap pairs (session-day count)

                   candidate_a                    candidate_b  same_day_overlap  same_bar_overlap
BOLLINGER_SQUEEZE_BREAKOUT_001 BOLLINGER_SQUEEZE_BREAKOUT_002               376               376
BOLLINGER_SQUEEZE_BREAKOUT_001 BOLLINGER_SQUEEZE_BREAKOUT_003               363               310
BOLLINGER_SQUEEZE_BREAKOUT_001 BOLLINGER_SQUEEZE_BREAKOUT_004               363               310
BOLLINGER_SQUEEZE_BREAKOUT_001 BOLLINGER_SQUEEZE_BREAKOUT_005               363               307
BOLLINGER_SQUEEZE_BREAKOUT_002 BOLLINGER_SQUEEZE_BREAKOUT_003               363               310
BOLLINGER_SQUEEZE_BREAKOUT_002 BOLLINGER_SQUEEZE_BREAKOUT_004               363               310
BOLLINGER_SQUEEZE_BREAKOUT_002 BOLLINGER_SQUEEZE_BREAKOUT_005               363               307
BOLLINGER_SQUEEZE_BREAKOUT_003 BOLLINGER_SQUEEZE_BREAKOUT_004               363               363
BOLLINGER_SQUEEZE_BREAKOUT_003 BOLLINGER_SQUEEZE_BREAKOUT_005               363               357
BOLLINGER_SQUEEZE_BREAKOUT_004 BOLLINGER_SQUEEZE_BREAKOUT_005               363               357
         RSI_FAILURE_SWING_001          RSI_FAILURE_SWING_002               206               206
         RSI_FAILURE_SWING_001          RSI_FAILURE_SWING_003               206               206
         RSI_FAILURE_SWING_001          RSI_FAILURE_SWING_004               206               206
         RSI_FAILURE_SWING_002          RSI_FAILURE_SWING_003               206               206
         RSI_FAILURE_SWING_002          RSI_FAILURE_SWING_004               206               206
         RSI_FAILURE_SWING_003          RSI_FAILURE_SWING_004               206               206
BOLLINGER_SQUEEZE_BREAKOUT_001          RSI_FAILURE_SWING_001               178                 0
BOLLINGER_SQUEEZE_BREAKOUT_001          RSI_FAILURE_SWING_002               178                 0
BOLLINGER_SQUEEZE_BREAKOUT_001          RSI_FAILURE_SWING_003               178                 0
BOLLINGER_SQUEEZE_BREAKOUT_001          RSI_FAILURE_SWING_004               178                 0

## Top opposite-side same-bar pairs

                   candidate_a                    candidate_b  opposite_side_same_bar  same_bar_overlap
BOLLINGER_SQUEEZE_BREAKOUT_001 BOLLINGER_SQUEEZE_BREAKOUT_002                       0               376
BOLLINGER_SQUEEZE_BREAKOUT_001 BOLLINGER_SQUEEZE_BREAKOUT_003                       0               310
BOLLINGER_SQUEEZE_BREAKOUT_001 BOLLINGER_SQUEEZE_BREAKOUT_004                       0               310
BOLLINGER_SQUEEZE_BREAKOUT_001 BOLLINGER_SQUEEZE_BREAKOUT_005                       0               307
BOLLINGER_SQUEEZE_BREAKOUT_001          RSI_FAILURE_SWING_001                       0                 0
BOLLINGER_SQUEEZE_BREAKOUT_001          RSI_FAILURE_SWING_002                       0                 0
BOLLINGER_SQUEEZE_BREAKOUT_001          RSI_FAILURE_SWING_003                       0                 0
BOLLINGER_SQUEEZE_BREAKOUT_001          RSI_FAILURE_SWING_004                       0                 0
BOLLINGER_SQUEEZE_BREAKOUT_001          RSI_FAILURE_SWING_005                       0                 0
BOLLINGER_SQUEEZE_BREAKOUT_002 BOLLINGER_SQUEEZE_BREAKOUT_003                       0               310
BOLLINGER_SQUEEZE_BREAKOUT_002 BOLLINGER_SQUEEZE_BREAKOUT_004                       0               310
BOLLINGER_SQUEEZE_BREAKOUT_002 BOLLINGER_SQUEEZE_BREAKOUT_005                       0               307
BOLLINGER_SQUEEZE_BREAKOUT_002          RSI_FAILURE_SWING_001                       0                 0
BOLLINGER_SQUEEZE_BREAKOUT_002          RSI_FAILURE_SWING_002                       0                 0
BOLLINGER_SQUEEZE_BREAKOUT_002          RSI_FAILURE_SWING_003                       0                 0

## Interpreting overlap for multi-candidate systems

Non-zero **same_bar_overlap** means two candidates sometimes fire on the same bar; the combiner picks one via priority / score. Use **opposite_side_same_bar** to see whether pairs disagree on direction on those bars (more complementary) vs same-direction crowding.
