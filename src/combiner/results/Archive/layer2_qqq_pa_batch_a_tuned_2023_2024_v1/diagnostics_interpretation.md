# Diagnostics interpretation — PA Batch A tuned v1 (QQQ 2023–2024)

Source folder: `diagnostics/` under this Layer 2 root.

## Candidate signal volume

From `diagnostics/candidate_signal_summary.csv`:

- **Total signals (all candidates):** 1453
- **By strategy:**
  - `pa_failed_range_breakout_trap`: 1100 signals (5 candidates × 220 each)
  - `pa_trading_range_bls_hs`: 353 signals (4 candidates × 63 + 1 candidate × 101)

All candidates are **long-only** (no `short_signals`).

## Overlap / conflicts

From `diagnostics/candidate_conflict_summary.csv`:

- **Within strategy duplicates (same-bar overlap equals signals):**
  - failed-trap candidates overlap **220/220** on same bar across all pairs ⇒ these five YAMLs are effectively **the same signal schedule** under Layer 2 routing.
  - trading-range candidates 001–004 overlap **63/63**; candidate 005 overlaps **58/63** with others.

- **Cross-family interaction (failed-trap vs trading-range):**
  - **same-bar overlap = 0** for all pairs ⇒ router rarely (never in this window) needs same-bar priority between the two families.
  - **same-day overlap** exists (e.g. 28 or 50 days depending on candidate pair), so daily trade caps can still cause **day-level competition**.

## Implications for Layer 2 evaluation

- The effective diversity inside each family is **low** (especially failed-trap).
- The portfolio question is therefore mostly:
  - **which family dominates** under `max_open_positions=1` + daily caps, and
  - whether allowing `max_trades_per_day=2` adds value or just churn.

These diagnostics justify the planned fixed runs:

- `pa_failed_top1_diagnostic`, `pa_trading_top1_diagnostic` (single-candidate behavior),
- family sets at `top_per_strategy` 1 vs 2,
- and `pa_batch_a_core` to measure interaction under identical routing constraints.

