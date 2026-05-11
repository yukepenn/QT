# Full-period diagnostics summary

- **Date range:** 2023-01-01 — 2024-12-31
- **Candidates in table:** 4
- **Total signals (sum):** 1004

## Signals by strategy

               strategy  signals
pa_buy_sell_close_trend      904
     pa_climax_reversal      100

## Signals by family

                     family  signals
pa_close_trend_continuation      904
         pa_climax_reversal      100

## Zero-signal candidates

*(none)*

## Top 20 same-bar overlap pairs

                        candidate_a                         candidate_b  same_bar_overlap  opposite_side_same_bar  same_direction_same_bar
PA_BUY_SELL_CLOSE_TREND_DIVERSE_001 PA_BUY_SELL_CLOSE_TREND_DIVERSE_002               392                       0                      392
     PA_CLIMAX_REVERSAL_DIVERSE_001      PA_CLIMAX_REVERSAL_DIVERSE_002                49                       0                       49
PA_BUY_SELL_CLOSE_TREND_DIVERSE_001      PA_CLIMAX_REVERSAL_DIVERSE_001                 0                       0                        0
PA_BUY_SELL_CLOSE_TREND_DIVERSE_001      PA_CLIMAX_REVERSAL_DIVERSE_002                 0                       0                        0
PA_BUY_SELL_CLOSE_TREND_DIVERSE_002      PA_CLIMAX_REVERSAL_DIVERSE_001                 0                       0                        0
PA_BUY_SELL_CLOSE_TREND_DIVERSE_002      PA_CLIMAX_REVERSAL_DIVERSE_002                 0                       0                        0

## Top 20 same-day overlap pairs (session-day count)

                        candidate_a                         candidate_b  same_day_overlap  same_bar_overlap
PA_BUY_SELL_CLOSE_TREND_DIVERSE_001 PA_BUY_SELL_CLOSE_TREND_DIVERSE_002               443               392
     PA_CLIMAX_REVERSAL_DIVERSE_001      PA_CLIMAX_REVERSAL_DIVERSE_002                50                49
PA_BUY_SELL_CLOSE_TREND_DIVERSE_002      PA_CLIMAX_REVERSAL_DIVERSE_001                42                 0
PA_BUY_SELL_CLOSE_TREND_DIVERSE_002      PA_CLIMAX_REVERSAL_DIVERSE_002                42                 0
PA_BUY_SELL_CLOSE_TREND_DIVERSE_001      PA_CLIMAX_REVERSAL_DIVERSE_001                38                 0
PA_BUY_SELL_CLOSE_TREND_DIVERSE_001      PA_CLIMAX_REVERSAL_DIVERSE_002                38                 0

## Top opposite-side same-bar pairs

                        candidate_a                         candidate_b  opposite_side_same_bar  same_bar_overlap
PA_BUY_SELL_CLOSE_TREND_DIVERSE_001 PA_BUY_SELL_CLOSE_TREND_DIVERSE_002                       0               392
PA_BUY_SELL_CLOSE_TREND_DIVERSE_001      PA_CLIMAX_REVERSAL_DIVERSE_001                       0                 0
PA_BUY_SELL_CLOSE_TREND_DIVERSE_001      PA_CLIMAX_REVERSAL_DIVERSE_002                       0                 0
PA_BUY_SELL_CLOSE_TREND_DIVERSE_002      PA_CLIMAX_REVERSAL_DIVERSE_001                       0                 0
PA_BUY_SELL_CLOSE_TREND_DIVERSE_002      PA_CLIMAX_REVERSAL_DIVERSE_002                       0                 0
     PA_CLIMAX_REVERSAL_DIVERSE_001      PA_CLIMAX_REVERSAL_DIVERSE_002                       0                49

## Interpreting overlap for multi-candidate systems

Non-zero **same_bar_overlap** means two candidates sometimes fire on the same bar; the combiner picks one via priority / score. Use **opposite_side_same_bar** to see whether pairs disagree on direction on those bars (more complementary) vs same-direction crowding.
