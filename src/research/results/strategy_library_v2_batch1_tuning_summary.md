# Strategy Library v2 Batch 1 Tuning Summary

QQQ only; in-sample 2023–01–01 → 2024–12–31. **mini-WFO v4/v5 and full WFO were not run.**

## 1. Why tuning was needed

- Original reduced Layer 2 v2 Batch 1 was **positive at 0.01** slip but **~flat on R at 0.02** on the leading squeeze stack, with **0.03** clearly negative (`positive_but_sensitive`, not `robust_positive_at_0_02` in the narrative sense of economic margin).
- **`behavior_unique` collapsed to one** dominant squeeze-heavy trade path; many YAMLs were near-duplicates under combiner priority.
- Relaxed fade/exhaustion legs added noise and drawdown without fixing cost robustness (see original `layer2_v2_batch1_summary.md`).

## 2. Cost fragility diagnosis

Curated pack: `src/research/results/batch1_cost_fragility_diagnostics_v1/` (generator: `src/research/gen_batch1_cost_fragility_diagnostics.py`; detailed combiner reruns kept **local** under `src/combiner/results/layer2_qqq_v2_batch1_2023_2024_diagnostics_local/`, gitignored).

- **Trade count:** Hundreds of squeeze-backed trades at the combiner → fixed per-share costs compound; small edge at 0.01 can erode quickly.
- **Risk per share / cost-as-R:** Tight structural stops imply **material `avg_cost_r`** on many trades; see `cost_by_risk_bucket.*` and `summary.md` in the diagnostics folder.
- **Candidate dominance:** Merged attribution shows **Bollinger squeeze ΣR ≫ RSI ΣR**; squeeze IDs dominate total R and the slippage decay path.
- **Near-duplicate YAMLs:** `candidate_overlap_matrix.csv` (original Layer 2 diagnostics) shows high same-bar overlap within multi-row grids.
- **RSI vs squeeze:** RSI contributes a **small** share of ΣR in the diagnostic merge; at the **tuned** combiner, RSI-only fixed runs still show **negative `total_r`** while PF can stay above 1 — the lane does **not** add orthogonal combiner value once costs and routing are applied.
- **Fade/exhaustion:** Original relaxed leg was net harmful or neutral at combiner attribution; not repeated in this tuned phase (strict families only).

Full Q&A narrative: `batch1_cost_fragility_diagnostics_v1/summary.md`.

## 3. Tuned Layer 1

- **Configs:** `src/strategies/testing_parameters/bollinger_squeeze_breakout_tuned_v1.yaml`, `src/strategies/testing_parameters/rsi_failure_swing_tuned_v1.yaml` (do not edit the `*_focused.yaml` baselines).
- **Design notes (as committed):**
  - Squeeze grid tightens squeeze/VWAP/range-expansion axes, caps bandwidth percentiles, fixes `risk.min_risk_per_share: 0.03` in Layer 1 YAML. Raw grid **1024**; sweep produced **128** rows after filters. Best in-window row ≈ **363–376** trades, **~35 R** at 0.01 slip (see `sweep_manifest.csv`).
  - RSI grid is a cleaner oscillator lane; `require_price_reclaim` is **not implemented** in the strategy — omitted from YAML. Raw grid **768**; **120** result rows; best **~83** trades, **~4.8 R** at 0.01 slip.
- **Output root:** `src/research/results/layer1_v2_batch1_tuned_qqq_2023_2024_v1/` — `sweep_manifest.*`, `selected_candidates.csv`, `selected_candidates/*.yaml` (**10** files), selection docs.
- **vs original Batch 1 Layer 1:** Fewer, stricter rows; squeeze top candidates cluster around **~363–376** trades (original squeeze combiner counts were higher in the 400–600+ range depending on stack). RSI remains **much lower frequency** than squeeze.

## 4. Tuned Layer 2

- **Configs:** `src/combiner/configs/layer2_qqq_v2_batch1_tuned_2023_2024_v1.yaml`, `src/combiner/configs/layer2_sweep_qqq_v2_batch1_tuned_2023_2024_v1.yaml`.
- **Diagnostics (`strict_batch1_tuned`, top 5):** `diagnostics_summary.md` — **2817** raw signals (squeeze **1841**, RSI **976**).
- **Fixed runs (`--no-detailed`):** see `fixed_run_summary.csv` — squeeze-only stacks **strongly positive** on R; RSI-only stacks **negative on `total_r`** at baseline slip; strict blend sits between (squeeze dominates fills).
- **Sweep:** **192** combos; wall clock **~30 s** including precompute on warm LocalAppData cache (`layer2_v2_batch1_tuned_v1`).
- **Best `top_unique`:** `volatility_breakout_tuned`, **`BOLLINGER_SQUEEZE_BREAKOUT_001` only**, **376** trades, **`total_r ≈ 35.42`**, **PF ≈ 1.113**, **max_dd_r ≈ −16.82** (see `top_unique_systems.csv`).
- **`behavior_unique`:** **1** (same as pre-tuning Batch 1 snapshot — still a single dominant hash among rows with trades).
- **Cost stress (unique rank 1):** at **0.02** slip, **`total_r ≈ 10.96`**, **PF ≈ 1.008**; at **0.03**, **`total_r` negative**, **PF < 1**. Postprocess flags **`robust_positive_at_0_02`** on the mechanical total-R gate; **PF at 0.02 does not clear 1.05**.
- **`cost_robust_systems.csv`:** populated with **10** rows at default thresholds (rank leaders at **0.02** slip).

## 5. Did tuning improve?

| Metric | Original Batch 1 best top_unique (illustr.) | Tuned v1 best top_unique |
|--------|---------------------------------------------|---------------------------|
| Baseline **0.01** `total_r` | ~34.6 | ~35.4 |
| Trades | ~488 | **376** (fewer) |
| **0.02** `total_r` | ~−0.02 (≈ flat) | **~+10.96** (positive) |
| **0.03** `total_r` | strongly negative | **~−10.22** (still fails) |
| PF at **0.02** | ~1.04 | **~1.008** (below 1.05 bar) |
| `behavior_unique` count | 1 | **1** (unchanged) |
| `cost_robust_systems` | empty (default thresholds) | **10** rows |

**Conclusion:** Tuning **materially improved** the **0.02 slippage R path** (from ~flat to clearly positive) while **reducing trade count**, but **economic margin at 0.02 remains thin** (PF ≈ 1.008), **0.03 still fails**, and **behavior diversity did not improve**.

## 6. Decision

**`TUNE_BATCH1_GRIDS_AGAIN`**

Rationale: Although the **0.02 `total_r` gate** now passes, the **PF > 1.05 at 0.02** bar from the mini-WFO v4 readiness checklist **does not**, **`behavior_unique` is still singular**, and the sweep leader remains **one squeeze candidate** (`BOLLINGER_SQUEEZE_BREAKOUT_001`). **Do not** proceed to mini-WFO v4 design on this snapshot alone.

**Explicit non-runs:** mini-WFO v4 **not** run; mini-WFO v5 **not** run; full WFO **not** run.
