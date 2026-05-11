# Robust l2_core v2 diagnostic v1 — decision (RUN)

**Decision (exactly one):** **`PROCEED_TO_FIXED_ROBUST_PROFILE_OOW_VALIDATION`**

## Rationale (3–6 bullets)

- At least one small robust-core candidate set is **positive in all three windows** (`insample_ref`, `early_oow`, `late_oow`) under the tiny grid.
- **`max_trades_per_day=2` dominates**: it materially improves late OOW stability versus `max_trades_per_day=1` in the same candidate sets.
- `daily_max_loss_r` ∈ {−1.5, −2.0} and `priority_policy` have **minimal impact** on totals for this diagnostic grid (no evidence they are the limiting factor).
- Target-limit-aware exit/slip overlay preserves the main conclusion: top systems remain **positive under stress** (see `exit_slip/robust_core_exit_slip_scenarios.csv`).
- Balanced core adds breadth but can **dilute late OOW** (notably via `PA_BUY_SELL_CLOSE_TREND_004` contribution in late OOW).

## Recommended next step (exactly one)

Run a **fixed-profile robust-core OOW validation** (research-only, small) on the best-performing candidate sets from this diagnostic:

- `pa_only_core`
- `pa_gap_core`
- `primary_representative_core` (as an interpretability baseline)

Hold constraints constant (no router, no YAML edits, no broad grids) and reuse the same windows.

## Explicit non-runs (this task)

- No broad Layer2 sweep
- No mini-WFO / full WFO
- No live/paper
- No SPY
- No strategy / feature / candidate-YAML edits
- No signal-cache usage (`--use-signal-cache`)

