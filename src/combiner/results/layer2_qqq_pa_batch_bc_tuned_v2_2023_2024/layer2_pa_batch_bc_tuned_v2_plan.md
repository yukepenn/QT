# PA Batch B/C tuned v2 — reduced Layer 2 plan (QQQ 2023–2024)

## Candidate root

`src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v2/selected_candidates`

## Strict candidates only

- **10 YAMLs** from tuned v2 Layer 1 strict selection: **5×** `pa_buy_sell_close_trend`, **5×** `pa_climax_reversal`
- **No** diagnostic relaxed rows, **no** PA Batch A, **no** `pa_broad_channel_zone` / `pa_generic_breakout_pullback` / `pa_second_entry_pullback` / `pa_wedge_reversal` (not in strict tuned v2 set)

## Candidate families / sets

| Set name | Strategies | `max_per_strategy` |
|----------|------------|-------------------|
| `pa_close_trend` | `pa_buy_sell_close_trend` | 5 |
| `pa_climax` | `pa_climax_reversal` | 5 |
| `pa_batch_bc_core` | both | 5 each (full strict library) |
| `pa_close_trend_top1_diagnostic` | close trend | 1 |
| `pa_climax_top1_diagnostic` | climax | 1 |

## Why Layer 2 is allowed now

- Post-`context_key` optimization and Brooks primitive cleanup, **two** strict PA families have tuned v2 economics and exit diagnostics (`pa_batch_bc_exit_diagnostics_v2/`).
- Goal: measure **router / overlap / cost stress** on the **combined** universe before any mini-WFO design.

## Risks

- **Close-trend:** max-hold and cost sensitivity (per exit diagnostics v2).
- **Climax:** lower trade count vs close-trend; may be **under-selected** when combined if priority favors the higher-activity family.

## Gates (research)

- **`behavior_unique` ≥ 2** strong hashes preferred (distinct trade paths, not only config permutations).
- **0.02 slippage:** `total_r >= 0` and `profit_factor` or `profit_factor_r > 1.05` for leading systems where metrics exist.
- Avoid **single-family overclaim** unless the second family is clearly non-degenerate in diagnostics + behavior.
- **max_drawdown_r** not catastrophic vs Layer 1 expectations.
- **Trade #2** (`max_trades_per_day=2`): no obvious blow-up vs `max_trades_per_day=1` baseline.

## Explicit non-runs

- **No** mini-WFO execution  
- **No** full WFO  
- **No** live / paper  
- **No** Layer 1 rerun  
- **No** new strategies or feature work  

## Configs

- Base: `src/combiner/configs/layer2_qqq_pa_batch_bc_tuned_v2_2023_2024.yaml`
- Trade2/cooldown fixed variant: `src/combiner/configs/layer2_qqq_pa_batch_bc_tuned_v2_2023_2024_trade2.yaml`
- Sweep: `src/combiner/configs/layer2_sweep_qqq_pa_batch_bc_tuned_v2_2023_2024.yaml` (144 combos)

## Result root

`src/combiner/results/layer2_qqq_pa_batch_bc_tuned_v2_2023_2024/`

## Signal cache

Prefer `%LOCALAPPDATA%\QT\candidate_signals` on Windows to reduce OneDrive lock contention.
