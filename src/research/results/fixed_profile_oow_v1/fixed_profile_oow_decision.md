# Fixed-profile OOW — decision

**Decision:** `REVISIT_LAYER2_CANDIDATE_SELECTION`

## Rationale

- **early_oow** (selected profiles):
  - `indicator_mtp1`: **754** trades, **-29.81** R
  - `indicator_mtp2`: **1508** trades, **-104.17** R
  - `indicator_mtp3`: **1938** trades, **-163.73** R
  - `vwap_mtp1`: **422** trades, **-40.12** R
  - `vwap_mtp2`: **482** trades, **-43.06** R
- **late_oow** (selected profiles):
  - `indicator_mtp1`: **332** trades, **-3.29** R
  - `indicator_mtp2`: **662** trades, **-14.74** R
  - `indicator_mtp3`: **848** trades, **-33.49** R
  - `vwap_mtp1`: **188** trades, **-17.47** R
  - `vwap_mtp2`: **208** trades, **-14.09** R
- **insample_ref** (selected profiles):
  - `indicator_mtp1`: **502** trades, **18.76** R
  - `indicator_mtp2`: **1002** trades, **46.51** R
  - `indicator_mtp3`: **1327** trades, **58.01** R
  - `vwap_mtp1`: **294** trades, **36.71** R
  - `vwap_mtp2`: **337** trades, **42.20** R
- Primary-profile OOW scorecard: **0** windows strongly positive (>+5R), **5** strongly negative (<-5R) → automated label **`REVISIT_LAYER2_CANDIDATE_SELECTION`**.

- VWAP insample replays match historical Global L2-style references; VWAP **early_oow** and **late_oow** are materially negative in this run.
- Indicator insample totals match fixed YAML wiring but **differ from older v1.5 headline R** (trade counts align); see `insample_sanity/insample_sanity_failure.md`.
- Target-limit-aware stress (`exit_slip/oow_exit_slip_scenario_comparison.csv`) softens losses versus symmetric 0.02 stress but **does not flip** negative OOW systems to viable.
- Quality-score cohort splits are mostly uninformative when train window equals full file (`insample_ref`) or thresholds collapse; enriched rows still power regime CSVs where present.

## Explicit non-runs

- mini-WFO; full rolling WFO; live/paper; SPY; Global L1 rerun; broad Global L2 grid
- Strategy / feature / selected-candidate YAML edits; hard regime filter; combiner `regime_router`
- Parameter optimization on OOW windows; OOW-driven candidate selection

## Recommended next step

Execute: **`REVISIT_LAYER2_CANDIDATE_SELECTION`** — see `fixed_profile_oow_v1_summary.md` section 15 for narrative and caveats.
