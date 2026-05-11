# Reduced Layer 2 — PA Batch B/C tuned v2 (design only)

**Status:** Design document only — **no Layer 2 combiner run** in this phase.

## Candidate root

- `src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v2/selected_candidates/`
- **Strategies present:** `pa_buy_sell_close_trend`, `pa_climax_reversal` only (strict YAMLs).

## Objective

Tiny router/combiner grid to test **non-redundant** coexistence of **two PA families** under **mandatory** cost stress **0.02** slippage (per-share), **behavior_unique** dedupe, **no mini-WFO**.

## Proposed grid (illustrative)

| Axis | Values |
|------|--------|
| `top_per_strategy` | 1, 2 |
| `max_trades_per_day` | 1 |
| `daily_max_loss_r` | −1.5, −2.0 |
| `cooldown_after_loss_minutes` | 0, 15 |
| `priority_policy` | metadata_priority |

## Gates

- Drop combinations that fail **cost stress @ 0.02** on reference window or duplicate behavior fingerprints.
- Keep combiner artifacts **light** per `docs/ARTIFACT_POLICY.md`.

## Explicit non-runs

- No mini-WFO, no full WFO, no live/paper until separate approval.
