# Layer 2 v2 Batch 1 Tuned — QQQ 2023–2024

## 1. Purpose

Cost-aware **tuned** reduced Layer 2 on **strict Batch 1 families only** (`bollinger_squeeze_breakout`, `rsi_failure_swing`), using candidates from `layer1_v2_batch1_tuned_qqq_2023_2024_v1/`. **Mini-WFO v4/v5 and full WFO were not run.**

## 2. Candidate universe

| Item | Value |
|------|------:|
| Candidate root | `src/research/results/layer1_v2_batch1_tuned_qqq_2023_2024_v1/selected_candidates` |
| YAMLs | **10** (5 squeeze + 5 RSI) |
| Base config | `src/combiner/configs/layer2_qqq_v2_batch1_tuned_2023_2024_v1.yaml` |
| Sweep config | `src/combiner/configs/layer2_sweep_qqq_v2_batch1_tuned_2023_2024_v1.yaml` |

## 3. Diagnostics (`strict_batch1_tuned`, top 5 per strategy)

- **Total raw signals (sum over candidates):** **2817**  
- **By strategy:** `bollinger_squeeze_breakout` **1841**; `rsi_failure_swing` **976**  
- **Artifacts:** `diagnostics/candidate_signal_summary.csv`, `candidate_overlap_matrix.csv`, `candidate_conflict_summary.csv`, `diagnostics_summary.md`, `candidate_precompute_profile_summary.*`

Signal cache (local, not committed): `%LOCALAPPDATA%\qt\layer2_v2_batch1_tuned_v1`.

## 4. Fixed runs (Numba path, `--no-detailed`)

| Tag | candidate_set | top | trades | total_r | PF | max_dd_r |
|-----|----------------|----:|-------:|--------:|---:|---------:|
| fixed_volatility_breakout_tuned_top1 | volatility_breakout_tuned | 1 | 376 | **35.42** | 1.113 | −16.82 |
| fixed_volatility_breakout_tuned_top5 | volatility_breakout_tuned | 5 | 403 | **28.03** | 1.070 | −19.07 |
| fixed_oscillator_reversal_tuned_top1 | oscillator_reversal_tuned | 1 | 206 | **−9.29** | 1.102 | −21.56 |
| fixed_oscillator_reversal_tuned_top5 | oscillator_reversal_tuned | 5 | 224 | **−6.58** | 1.115 | −23.87 |
| fixed_strict_batch1_tuned_top1 | strict_batch1_tuned | 1 | 565 | **17.52** | 1.087 | −24.66 |
| fixed_strict_batch1_tuned_top5 | strict_batch1_tuned | 5 | 582 | **10.85** | 1.064 | −25.88 |

- **Dominant path:** `BOLLINGER_SQUEEZE_BREAKOUT_001` wins priority and captures all fills in the top `volatility_breakout_tuned` rows.  
- **RSI lane:** positive **PF** but **negative `total_r`** at the combiner under the shared execution stack — does **not** validate as an orthogonal Layer 2 contributor here.

Rollup: `fixed_run_summary.csv` / `.md`.

## 5. Sweep

- **Grid:** **192** combos (3 × 4 × 2 × 2 × 2 × 2).  
- **Wall time:** ~**30 s** end-to-end on warm signal cache (see sweep log: `sweep_20260509_225629/`).  
- **Best `top_unique`:** `volatility_breakout_tuned`, `top_per_strategy=1`, **`BOLLINGER_SQUEEZE_BREAKOUT_001`**, **`max_trades_per_day=1`**, `daily_max_loss_r=−1.5`, `cooldown_after_loss_minutes=0`, `metadata_priority` — **376** trades, **`total_r ≈ 35.42`**, **PF ≈ 1.113**, **`max_dd_r ≈ −16.82`**.  
- **Config dedupe:** the top ~dozen unique ranks are **tie-break permutations** of the same candidate JSON (policy/cooldown/daily cap), not distinct trade paths.

## 6. Cost stress (top unique ranks 1–10)

From `cost_stress/cost_stress_summary.md` (leader is unique rank 1 = squeeze top1):

| Slippage / share | total_r (illustr.) | PF | Notes |
|------------------|-------------------:|---:|-------|
| 0.01 (baseline) | ~35.42 | ~1.113 | strong in-sample |
| **0.02** | **~10.96** | **~1.008** | **positive R**, thin PF margin |
| 0.03 | ~−10.22 | ~0.925 | fails |

Postprocess label on the mechanical gate: **`robust_positive_at_0_02`** (total R > 0 at 0.02). **PF at 0.02 is still ~1.008**, below a **1.05** economic margin bar.

## 7. Behavior dedupe

- **`behavior_unique` systems:** **1** among inspected top rows with `trades.csv` (see `behavior_unique_systems.md`).  
- **Interpretation:** tuning **did not** introduce a second distinct trade-path family at the combiner; the stack is still **squeeze-ID-001-shaped**.

## 8. Comparison vs original Batch 1 Layer 2 (same window)

| Metric | Original `layer2_qqq_v2_batch1_2023_2024` best top_unique | Tuned v1 best top_unique |
|--------|----------------------------------------------------------|---------------------------|
| Trades | ~488 | **376** |
| 0.01 `total_r` | ~34.6 | ~35.4 |
| 0.02 `total_r` | ~−0.02 | **~+10.96** |
| 0.03 `total_r` | strongly negative | ~−10.22 |
| `behavior_unique` | 1 | **1** |

## 9. Decision

**`TUNE_BATCH1_GRIDS_AGAIN`**

Rationale: **0.02 R improved materially**, but **PF at 0.02 ~1.008**, **`behavior_unique` still 1**, and the winner is still a **single squeeze YAML**. This does **not** satisfy the stricter mini-WFO v4 design gate documented in `src/research/results/strategy_library_v2_batch1_tuning_summary.md`.

---

**Explicit non-runs:** mini-WFO v4 **not** run; mini-WFO v5 **not** run; full WFO **not** run.
