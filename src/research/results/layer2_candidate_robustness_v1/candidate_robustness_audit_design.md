# Candidate robustness audit — design (v1)

## Why now

Fixed-profile OOW validation (`fixed_profile_oow_v1`) showed VWAP and indicator **combinations** are not robust outside 2023–2024 under replay-faithful settings. Before changing combiner weights or building new profiles, we need **candidate-level** evidence: is failure concentrated in a few names, or is the whole l2_core library fragile?

## Why this is not OOW optimization

- Candidate YAML parameters are **frozen**.
- Windows are **pre-declared** (same as fixed-profile OOW); we do **not** pick windows to maximize metrics.
- Heuristic labels (`ROBUST_POSITIVE`, `INSAMPLE_ONLY`, …) are **triage rules** for research reporting, not a search objective and not used to rewrite parameters.

## Label assignment (heuristic)

See `assign_robustness_label()` in `src/research/audit_l2_candidates_oow_lib.py` (thresholds `INSAMPLE_POS`, `STRONG_NEG`, `WEAK_OOW_FLOOR`, `MIN_TRADES_SPARSE`, turnover guard).

Summary intent:

| Label | Intent |
|-------|--------|
| ROBUST_POSITIVE | Strong insample R; both OOW windows non-catastrophic; not high-turnover fragile |
| INSAMPLE_ONLY | Strong insample; both OOW strongly negative |
| OOW_MIXED | Borderline / asymmetric / does not meet other buckets |
| OOW_NEGATIVE | Weak insample; both OOW weak/negative |
| TOO_SPARSE | Too few trades in any of the three windows, or missing/NaN R |
| HIGH_TURNOVER_FRAGILE | High trades/day with weak avg R on insample while OOW non-catastrophic |
| ANTI_PREDICTIVE_CANDIDATE | Both OOW strongly negative with adequate trades while insample not strongly positive |

## How this informs l2_core policy v2

- Promote only candidates with **cross-window** stability under singleton replay before they influence combiner cores.
- Demote or exclude **INSAMPLE_ONLY** and persistent **OOW_NEGATIVE** / **ANTI_PREDICTIVE** names from automatic “core” status.
- Require **family-level** diversity checks so one strong 2023–2024 regime does not dominate core construction.
