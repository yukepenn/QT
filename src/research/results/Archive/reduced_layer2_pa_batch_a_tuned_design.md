# Reduced Layer 2 — PA Batch A tuned v1 (design only)

**Status:** planning document only. **No combiner run.** No mini-WFO. No full WFO.

## Candidate root

`src/research/results/layer1_pa_batch_a_tuned_qqq_2023_2024_v1/selected_candidates/`

Ten YAMLs (**five** `pa_trading_range_bls_hs`, **five** `pa_failed_range_breakout_trap`). **`pa_tight_channel_pullback`** and **`pa_mtr_reversal`** have **no** strict Layer 1 exports from tuned v1 — omit from core bundle unless a future sweep qualifies them.

## Candidate sets (metadata grouping)

| Set id | Contents |
|--------|----------|
| `pa_failed_range_trap` | `PA_FAILED_RANGE_BREAKOUT_TRAP_*` |
| `pa_trading_range` | `PA_TRADING_RANGE_BLS_HS_*` |
| `pa_batch_a_core` | Union of the two sets above |
| `pa_channel_pullback` | *(empty until Layer 1 qualifies tight channel)* |
| `pa_mtr` | *(empty until Layer 1 qualifies MTR)* |

Optional future comparison (not configured): `pa_batch_a_with_refined_failed` vs refined failed-ORB core — **explicitly out of scope** for this phase (no merge with refined_failed_orb per research charter).

## Proposed small combiner grid (research)

- `top_per_strategy`: **[1, 2]** (draw from `pa_batch_a_core`)
- `max_trades_per_day`: **[1, 2]**
- `daily_max_loss_r`: **[-1.5, -2.0]**
- `cooldown_after_loss_minutes`: **[0, 15]**
- `priority_policy`: **`metadata_priority`**

## Gates

- **Cost stress:** reuse repo baseline slippage ladders (e.g. **0.02** R-per-share stress) before trusting leaderboard ranks.
- **Behavior dedupe:** require distinct trade-sequence fingerprints where `postprocess` exposes `behavior_unique_*`.
- **Non-overlap sanity:** conflict groups from `metadata.yaml` must remain consistent when both PA families are active.

## Explicit non-run statement

This file **does not** execute `src/combiner/run.py`, `src/combiner/sweep.py`, `src/walkforward/mini_wfo.py`, or any live/paper path.
