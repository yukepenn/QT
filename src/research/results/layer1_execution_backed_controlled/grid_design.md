# Grid and run design — controlled Layer1

**Principles:** Small controlled effective search space, **`--max-combos`** caps, **`execution_backed`** semantics via **`simulate_trade_path`** (sweep row engine label may read `reference` — see pipeline state doc). **QQQ** + **`data/raw/ibkr`** only.

## Per-strategy grids

| Strategy | Grid source | Raw combos | First-pass cap | Runtime |
|----------|-------------|------------|----------------|---------|
| PA | `pa_buy_sell_close_trend_focused.yaml` | 432 | **64** (then 128 if stable) | medium |
| GAP | `gap_acceptance_failure_focused.yaml` | 192 | **64** | medium |
| CCI | `cci_extreme_snapback_focused.yaml` | 32 | **32** (full grid OK) | small |

**Alternative:** Copy a **reduced** grid YAML under the result root in the **run** task (not this design commit) with fewer keys — only if `--max-combos` truncation is too blunt for exploration.

## Strict selection gates (post-run)

- **Minimum trades:** e.g. `trade_count >= 30` over 2023–2024 (tune per strategy liquidity).
- **PF_R:** `profit_factor_r >= 1.1` **or** top-quartile among passing combos if PF noisy.
- **MaxDD_R:** prefer lower tail; e.g. `max_drawdown_r` not in worst 20% of passing set.
- **Tiny-N:** reject if `trade_count < 15` unless diagnostic-only bucket.
- **Concentration:** flag if >50% R from a single calendar month.

## Relaxed diagnostic gates

- Allow logging combos with `trade_count in [10, 30]` into **`candidate_rejects_summary.csv`** with reason codes for manual review — **do not** promote to selected without strict gate pass.

## Metrics to record (from sweep + metrics)

Already in sweep result schema / `summarize_trades` lineage: **`total_r`**, **`avg_r`**, **`profit_factor_r`**, **`max_drawdown_r`**, **`trade_count`**, **`win_rate`**, **`total_gross_r`**. Extend in **postprocess** (next task) with: **`trades_per_month`**, **`avg_bars_held`**, **`exit_reason` histogram** if trade-level export is enabled locally (not committed).

## Overfitting guard

- Prefer **stable** trade counts and **reasonable** PF over max total R alone.
- Hold out **2025** (in-sample committed data) as optional **second gate** after 2023–2024 selection — **design only** for v2 pass; not required for first micro-run.
