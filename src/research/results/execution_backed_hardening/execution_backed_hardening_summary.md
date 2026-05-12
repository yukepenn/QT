# Execution-backed hardening — summary

Post exit-overlay diagnostic, **`src/execution/`** + **`combiner/adapter`** + **`combiner/state`** were hardened for: **same-session next-bar entry**, **cooldown reset on new session**, **`min_risk_per_share`** on **`ExecutionPolicy`** with **`risk_too_small`** materialization reject, **scale-out fraction of remaining qty**, plus doc/index sync and a **fast-path plan** (no Numba).

**Decision:** `DESIGN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`.

**Evidence root:** this folder; **tests:** `tests/test_execution_backed_hardening.py`.
