# expanded_stability_risk_flags

                risk_id severity        status                                                                notes
                 2025Q1   medium       WARNING Quarterly PnL negative for key profiles; see weak_period_profile_pnl
                 2022Q4   medium       WARNING                  Quarterly PnL negative; see weak_period_profile_pnl
         2023Q3_primary      low          INFO                                       Included as optional CCI slice
    max_hold_dependency   medium       WARNING                    max_hold share ~0.47–0.59 across profiles/windows
       stop_sensitivity      low NOT_EVALUATED                        Period-level stop attribution requires replay
                 no_spy     high          OPEN                                                   No SPY cross-check
                 no_wfo     high          OPEN                                                      No WFO evidence
          no_live_paper     high          OPEN                                               No live/paper evidence
 full_available_overlap   medium          INFO                      Do not treat overlapping windows as independent
period_exit_attribution   medium          OPEN    weak_period_exit_reason.csv marked REQUIRES_LOCAL_DETAILED_REPLAY

