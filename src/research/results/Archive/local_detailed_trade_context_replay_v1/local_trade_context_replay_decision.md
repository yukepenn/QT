# local_trade_context_replay_decision

## Decision: `REFINE_ROUTER_QUALITY_SCORE`

### Rationale (3–6 bullets)

- The local detailed replay succeeded with **10,628** trades and **100%** decision-context join coverage on core PA regime fields, enabling trade-level diagnostics.
- Offline router filters show large **trade-retention** vs **risk-period** tradeoffs; the best risk improvements observed are paired with substantial trade removal and large total-R loss.
- Trade-quality score v2 (proxy implementation) produces **very sparse A-only** and modest A+B coverage, with unclear separation in the current proxy components.
- Market-context slicing shows meaningful dispersion across monthly context labels, suggesting the next increment should be **better-aligned scoring/filters** rather than immediate integration.

### Recommended next step

- Refine the **offline router** and **quality score v2** definitions to better match the available decision-time features (and explicitly document any missing components), then rerun aggregate-only diagnostics.

### Explicit non-runs

- No WFO / mini-WFO / live / paper
- No SPY / broad Layer2 / Global Layer1 rerun
- No strategy signal semantics changes
- No selected candidate YAML edits
- No production router wiring in combiner
- No short/scalp implementation
- No row-level artifacts committed

