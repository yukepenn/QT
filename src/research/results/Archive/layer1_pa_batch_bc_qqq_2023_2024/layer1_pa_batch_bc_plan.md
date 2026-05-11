# PA Batch B/C — formal Layer 1 plan (QQQ 2023–2024)

## Purpose

Run **full focused-grid sweeps** for six PA Batch B/C strategies on **QQQ** over **2023-01-01 → 2024-12-31** to see whether enough **strict Layer 1 candidates** exist to justify a later **reduced Layer 2** design. This answers: *Do B/C produce enough high-quality candidates?*

## Strategies in scope

**Batch B:** `pa_broad_channel_zone`, `pa_climax_reversal`, `pa_second_entry_pullback`, `pa_wedge_reversal`  
**Batch C:** `pa_buy_sell_close_trend`, `pa_generic_breakout_pullback`

## Window and instrument

- **Symbol:** QQQ only (equity). **No** SPY.
- **Dates:** 2023-01-01 — 2024-12-31 (inclusive).

## Why Jan 2025 smoke is not enough

Jan 2025 is a **short** window with **capped** combos; several strategies showed **zero trades** in that smoke while others were active. **Signal rate and edge** must be judged on the **full research window** and **full focused grids** (within the ≤1500 raw combo policy).

## Strict selection gates (primary)

Applied via `select_candidates.py` on sweep `results.csv` rows:

| Gate | Value |
|------|--------|
| min_trades | 30 |
| min_profit_factor | 1.05 |
| min_total_r | 0 |
| max_drawdown_r | -50 |
| max_avg_bars_held | 120 |
| max_eod_count | 0 |
| max_end_of_data_count | 0 |
| top_per_strategy | 5 |

**Primary** exports live under `selected_candidates/` only. **No** mixing with refined_failed_orb or PA Batch A Layer 2 candidates.

## Diagnostic relaxed selection (non-authoritative)

Run only if strict yields too few candidates or families; outputs under `diagnostic_relaxed_selection/`:

| Gate | Value |
|------|--------|
| min_trades | 15 |
| min_profit_factor | 1.00 |
| min_total_r | -3 |
| max_drawdown_r | -60 |
| max_avg_bars_held | 150 |
| max_eod_count | 0 |
| top_per_strategy | 5 |

Label: **DIAGNOSTIC ONLY** — not merged into primary `selected_candidates/`.

## Grid policy

- **Raw grid ≤ 1500:** run **full** grid (no `--max-combos` cap).
- **Raw grid > 1500:** reduce focused YAML axes, document in `grid_review.md`, then run.
- Preflight raw sizes: 288 (four Batch B), 432 (two Batch C) — **all full grid**.

## Explicit non-runs

- PA Batch B/C **Layer 2** (combiner) — not in this phase.
- **mini-WFO**, **full WFO**, **live/paper**.
- **IBKR pull**, new strategies, feature/strategy logic changes unless a **clear bug** is found.

## Artifact policy

- **Commit:** plan, preflight, grid review, sweep manifest, signal diagnosis, selection summaries, strict `selected_candidates/*` (if any), fast-context check, Layer 1 summary, optional `reduced_layer2_*` **design only** if decision allows.
- **Do not commit:** `src/strategies/testing_parameters_results/**` sweep folders, large CSVs of raw sweeps beyond what we curate, caches, `trades.csv` / `equity.csv` from exploratory runs.

## Tag and orchestration

- **Tag:** `layer1_pa_batch_bc_qqq_2023_2024`
- **Orchestrator:** `src/research/run_layer1_focused.py` (wraps `src/backtest/sweep.py` per strategy).
