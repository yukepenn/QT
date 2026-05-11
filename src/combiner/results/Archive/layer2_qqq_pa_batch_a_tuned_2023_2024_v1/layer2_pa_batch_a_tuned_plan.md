# PA Batch A tuned v1 — reduced Layer 2 plan (QQQ 2023–2024)

## Purpose

Evaluate whether the two PA families that passed tuned Layer 1 behave well as a **portfolio/router** under Layer 2 constraints.

- **In scope**: PA Batch A tuned v1 candidates only.
- **Not in scope**: mini-WFO, full WFO, live/paper, SPY, data pulls, merging refined_failed_orb, mixing with v2 completion families.

## Inputs

- **Window**: QQQ, 2023-01-01 → 2024-12-31
- **Candidate root**: `src/research/results/layer1_pa_batch_a_tuned_qqq_2023_2024_v1/selected_candidates`
- **Candidate families**:
  - `pa_trading_range_bls_hs` (5 YAMLs)
  - `pa_failed_range_breakout_trap` (5 YAMLs)

## Configs

- Base config: `src/combiner/configs/layer2_qqq_pa_batch_a_tuned_2023_2024_v1.yaml`
- Sweep config: `src/combiner/configs/layer2_sweep_qqq_pa_batch_a_tuned_2023_2024_v1.yaml`

## Diagnostics-only precompute (required)

Run `--diagnostics-only` for `pa_batch_a_core` to review:

- signals by candidate / strategy
- overlap matrix and conflict summary (same-bar priority resolution)
- candidate duplicates / near-duplicates

## Fixed runs (gates before sweep)

Run `--no-detailed` fixed runs for:

- `pa_failed_range_trap` with `top_per_strategy` ∈ {1, 2}
- `pa_trading_range` with `top_per_strategy` ∈ {1, 2}
- `pa_batch_a_core` with `top_per_strategy` ∈ {1, 2}
- diagnostics singles: `pa_failed_top1_diagnostic`, `pa_trading_top1_diagnostic`

Collect summaries via `postprocess.py --collect-fixed-runs`.

### Fixed-run gate to proceed to sweep

Proceed only if:

- at least one `pa_failed_range_trap` fixed run is **PF > 1.05** and **total_r > 0**
- at least one `pa_trading_range` fixed run is **PF > 1.05** and **total_r > 0**
- `pa_batch_a_core` is not substantially worse than the better single-family run
- drawdown not catastrophic (rough: `max_drawdown_r > -60`)

If gate fails: **skip sweep** and write summary/decision accordingly.

## Reduced sweep (only if fixed-run gate passes)

Sweep grid is intentionally small: **48 combos**.

After sweep, run `postprocess.py` for:

- top_unique
- behavior_unique
- cost stress (including 0.02 slippage review)
- period breakdowns (if produced and small)

## Required gates to review

- **Cost stress @ 0.02**: must be reviewed; label robust vs fragile.
- **Behavior dedupe**: verify whether we have >1 distinct behavior path (or clear single-winner rationale).
- **Daily trade number profile**: check whether `max_trades_per_day=2` adds value or churn.
- **No overclaim**: avoid single-family overclaim; call out if the core collapses to one family.

## Artifact rules

Commit only curated outputs (CSVs/MDs/summaries). Do not commit:

- `top_runs/`
- `run_*`, `sweep_*` folders
- full `trades.csv`, `equity.csv`
- `.cache/**`, `data/raw/**`, `*.npy/*.npz/*.memmap/*.parquet`

