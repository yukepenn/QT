# PA Batch A — formal Layer 1 plan (QQQ 2023–2024)

## Purpose

Run **formal Layer 1** focused sweeps for the four **PA Batch A** plugins after the shared `pa_*` feature foundation, then **strict** candidate selection, signal/trade-rate diagnosis, and fast-context sanity — **without** Layer 2, mini-WFO, full WFO, or live/paper work.

## Strategies in scope

| Strategy | Focused grid | Family (metadata) |
|----------|----------------|-------------------|
| `pa_trading_range_bls_hs` | `pa_trading_range_bls_hs_focused.yaml` | `pa_trading_range` |
| `pa_failed_range_breakout_trap` | `pa_failed_range_breakout_trap_focused.yaml` | `pa_range_breakout_failure` |
| `pa_tight_channel_pullback` | `pa_tight_channel_pullback_focused.yaml` | `pa_channel_pullback` |
| `pa_mtr_reversal` | `pa_mtr_reversal_focused.yaml` | `pa_major_trend_reversal` |

## Window and symbol

- **Symbol:** QQQ (equity), **only**.
- **Dates:** `2023-01-01` → `2024-12-31` (inclusive RTH 1m bars via existing reader).
- **No SPY**, no IBKR pull in this phase.

## Why Jan 2025 zero-trade strategies stay included

Jan 2025 smokes used a **short** window and `min_trades=1` display filters; **`pa_tight_channel_pullback`** and **`pa_mtr_reversal`** showed **no fills** on that slice. That is **insufficient** to drop them from formal Layer 1: two years of QQQ data may still produce sparse but non-zero combos, and diagnosis belongs on **full sweep results**, not January alone.

## Strict selection thresholds (primary)

Used with `select_candidates.py` manifest mode:

- `min_trades`: **30**
- `min_profit_factor`: **1.05**
- `min_total_r`: **0**
- `max_drawdown_r`: **-50**
- `max_avg_bars_held`: **120**
- `max_eod_count`: **0**
- `max_end_of_data_count`: **0**
- `top_per_strategy`: **5**

No `allow_relaxed_fallback` for the **primary** `selected_candidates/` export.

## Diagnostic relaxed thresholds (optional, separate folder)

Run **only if** strict selection yields zero candidates, fewer than two PA families represented, or tcp/mtr need a trade visibility check. Outputs under `diagnostic_relaxed_selection/` only; **not** merged into primary YAML set.

- `min_trades`: 18 (between 15 and 20; document as 18)
- `min_profit_factor`: 1.00
- `min_total_r`: -3
- `max_drawdown_r`: -60
- `max_avg_bars_held`: 150
- `max_eod_count`: 0
- `top_per_strategy`: 5

## Grid policy

- Target **raw** focused grid **≤ 1500** combos per strategy; if larger, cap with `--max-combos` on `sweep.py` **only** for that strategy and set `capped=true` in manifest notes.
- Current PA focused YAMLs expand to **108** raw combos each → **full grid** (no cap).

## Explicit non-runs

- PA **Layer 2** combiner, **mini-WFO**, **full WFO**, **live/paper**.
- No PA Batch B/C plugins.
- No edits to PA strategy **signal logic** unless a blocking bug appears.

## Artifact policy

- **Commit:** curated files under `src/research/results/layer1_pa_batch_a_qqq_2023_2024/` (manifest, preflight, grid review, diagnosis, selection summaries, YAMLs, summary MD).
- **Do not commit:** `src/strategies/testing_parameters_results/**` sweep trees, caches, raw `trades.csv` / `equity.csv` / `top_runs/`, etc. (see `docs/ARTIFACT_POLICY.md`).

## Orchestration

- Preferred: `python src/research/run_layer1_focused.py` with `--strategies` listing the four PA names, `--tag layer1_pa_batch_a_qqq_2023_2024`, `--output-root` this folder, `--min-trades 1` for sweep display (full result rows), `--top 100`, `--progress-every 100`.
