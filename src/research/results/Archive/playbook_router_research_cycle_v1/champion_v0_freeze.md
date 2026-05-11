# Champion v0 freeze

## Scope
- **Long-only** intraday sleeve on QQQ; **not** a full day-trader system.
- **Not production-ready**; frozen as **benchmark / incumbent** for future router, scalp, and short research.
- Future strategies must **challenge** this frozen incumbent under explicit gates.

## Frozen profiles

       profile_id                   role                                                                   candidate_ids           status                                                                           reason
pa_only_mtp1_meta         CLEAN_BASELINE                                                     PA_BUY_SELL_CLOSE_TREND_003           frozen                    simplest profile; positive all key windows; robustness anchor
 pa_gap_mtp2_meta       DEFAULT_COMBINED                          PA_BUY_SELL_CLOSE_TREND_003;GAP_ACCEPTANCE_FAILURE_001           frozen                        default combined; PA driver; GAP adds early/insample/full
primary_mtp2_meta BREADTH_REFERENCE_ONLY PA_BUY_SELL_CLOSE_TREND_003;GAP_ACCEPTANCE_FAILURE_001;CCI_EXTREME_SNAPBACK_003 frozen_reference highest full R; deeper DD; weaker late_oow — do not promote without new evidence

## Do not modify
- Selected candidate YAML parameters for these profiles.
- Signal semantics for embedded strategies.

## Evidence
- Layer3 complete smoke + expanded stability v1.
