# l2_core policy v2 (draft, post fixed-profile OOW)

## Principles

1. **Candidate-level OOW audit required** before any YAML is treated as “core” for global Layer 2 design.
2. **Catastrophic OOW negatives** (`INSAMPLE_ONLY`, `ANTI_PREDICTIVE` with adequate counts) → default **`DROP_FROM_CORE`** or **`WATCHLIST_DIAGNOSTIC`** only.
3. **High-turnover** names need **stronger** insample avg_R **and** non-catastrophic OOW; otherwise **`WATCHLIST_DIAGNOSTIC`** / exclude from tight cores.
4. **Family quotas:** no family enters core solely on 2023–2024 leaderboard strength.
5. **Indicator mtp profiles:** treat as **high risk** unless singleton audits + overlap checks justify inclusion; prefer **lower mtp** until evidence improves.
6. **VWAP:** default **watchlist** unless individual candidates show OOW stability (not observed in v1 vwap slice).
7. **Target-limit-aware overlay** remains secondary: baseline replay must not be structurally broken on OOW before overlays.
8. **Quality score / router:** insufficient as a gate until fixed profiles and singleton audits pass a stability bar.

## Candidate actions

See `l2_core_policy_v2_candidate_actions.csv` (mirrors `candidate_robustness_labels.csv` policy column).
