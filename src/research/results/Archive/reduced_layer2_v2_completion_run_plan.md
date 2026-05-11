# Reduced Layer 2 v2 completion — run plan (QQQ 2023–2024)

**Status:** executable plan. **Not** mini-WFO v4/v5, **not** full WFO, **not** live/paper.

## Preconditions (confirmed)

- **30** candidate YAMLs under `src/research/results/layer1_v2_completion_qqq_2023_2024/selected_candidates/`.
- Fast-context sanity: **30 / 30** passed (`candidate_fast_context_check.md`).
- **No** `sma20_reclaim_reject` or `large_candle_failure` YAMLs in tree (those strategies have **zero** selected candidates).
- **`adx_dmi_trend_continuation`:** relaxed-only / diagnostic in Layer 1 manifest; combiner set `adx_diagnostic` and optional inclusion via `all_with_relaxed_completion` only.

## Candidate root

`src/research/results/layer1_v2_completion_qqq_2023_2024/selected_candidates`

## Family buckets (candidate sets)

| Set id | Strategies | Notes |
|--------|------------|-------|
| `macd_momentum_family` | `macd_momentum_turn` | |
| `oscillator_reversal_family` | `stochastic_oversold_cross`, `cci_extreme_snapback` | |
| `atr_trend_family` | `supertrend_atr_flip` | |
| `level_reclaim_family` | `multi_day_level_trap`, `prior_close_reclaim` | Lower trade count per strategy |
| `strict_completion_core` | All six strict completion strategies | **Excludes ADX** |
| `all_strict_completion` | All YAMLs with `include_warnings: false` | Implicit: all non-warning candidates in root |
| `all_with_relaxed_completion` | All 30 YAMLs (`include_warnings: true`) | Includes relaxed ADX |
| `adx_diagnostic` | `adx_dmi_trend_continuation` only | Diagnostic |

**Excluded from any dedicated strict set:** `sma20_reclaim_reject`, `large_candle_failure` (no files). **Excluded from `strict_completion_core`:** ADX.

## Config paths

- Base: `src/combiner/configs/layer2_qqq_v2_completion_2023_2024.yaml`
- Sweep: `src/combiner/configs/layer2_sweep_qqq_v2_completion_2023_2024.yaml`

## Grid size (sweep)

`7 × 3 × 3 × 3 × 2 × 2 = 756` combinations  
(`candidate_set` × `top_per_strategy` × `max_trades_per_day` × `daily_max_loss_r` × `cooldown_after_loss_minutes` × `priority_policy`).

**Explicitly out of scope for this phase:** `top_per_strategy: 5`, `cooldown: 30`, broader relaxed-heavy sets.

## Fixed runs (before sweep)

Fifteen tagged runs under `src/combiner/results/layer2_qqq_v2_completion_2023_2024/fixed_runs/`:

| # | candidate_set | top_per_strategy |
|---|-----------------|------------------|
| 1–2 | `macd_momentum_family` | 1, 3 |
| 3–4 | `oscillator_reversal_family` | 1, 3 |
| 5–6 | `atr_trend_family` | 1, 3 |
| 7–8 | `level_reclaim_family` | 1, 3 |
| 9–10 | `strict_completion_core` | 1, 3 |
| 11–12 | `all_strict_completion` | 1, 3 |
| 13–14 | `all_with_relaxed_completion` | 1, 3 |
| 15 | `adx_diagnostic` | 2 |

Template:

```text
python src/combiner/run.py --candidate-root src/research/results/layer1_v2_completion_qqq_2023_2024/selected_candidates --config src/combiner/configs/layer2_qqq_v2_completion_2023_2024.yaml --asset equity --symbol QQQ --start 2023-01-01 --end 2024-12-31 --candidate-set <SET> --top-per-strategy <N> --output-root src/combiner/results/layer2_qqq_v2_completion_2023_2024/fixed_runs --tag fixed_<SET>_top<N> --use-signal-cache [--signal-cache-root %LOCALAPPDATA%\QT\candidate_signals]
```

Then:

```text
python src/combiner/postprocess.py --collect-fixed-runs src/combiner/results/layer2_qqq_v2_completion_2023_2024/fixed_runs --fixed-runs-dir src/combiner/results/layer2_qqq_v2_completion_2023_2024/fixed_runs --write-period-breakdowns --output-root src/combiner/results/layer2_qqq_v2_completion_2023_2024
```

## Diagnostics (first)

```text
python src/combiner/run.py ... --candidate-set all_with_relaxed_completion --top-per-strategy 5 --diagnostics-only --output-root src/combiner/results/layer2_qqq_v2_completion_2023_2024 --use-signal-cache
```

Expected under `diagnostics/`: `candidate_signal_summary.csv`, `candidate_overlap_matrix.csv`, `candidate_conflict_summary.csv`, plus `diagnostics_summary.md` via postprocess.

## Pass / fail gates

- **Stop before sweep** if diagnostics show broken candidates (then fix YAML if obvious, rerun fast-context).
- **Defer sweep** if all fixed runs are negative / unusable per `fixed_run_summary.csv` (document decision `TUNE_COMPLETION_GRIDS_FIRST` or `DEFER`).
- **Run sweep** only if ≥2 family-level fixed runs look promising and diagnostics are clean enough (document criteria in `layer2_v2_completion_summary.md`).

## Explicit non-runs

- mini-WFO v4 / v5 — **not run**
- Full WFO — **not run**
- SPY / IBKR pull / broker — **not run**
