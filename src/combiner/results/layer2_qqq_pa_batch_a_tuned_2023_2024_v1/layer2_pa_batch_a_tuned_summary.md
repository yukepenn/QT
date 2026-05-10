# PA Batch A tuned v1 — reduced Layer 2 summary (QQQ 2023–2024)

## 1. Purpose

Run a PA-only **reduced Layer 2** on the **tuned v1** PA Batch A candidate library to evaluate portfolio/router behavior under simple system constraints. No mini-WFO or full WFO in this phase.

## 2. Inputs

- **Window:** QQQ, 2023-01-01 → 2024-12-31
- **Candidate root:** `src/research/results/layer1_pa_batch_a_tuned_qqq_2023_2024_v1/selected_candidates`
- **Candidates:** 10 YAMLs (5 `pa_trading_range_bls_hs`, 5 `pa_failed_range_breakout_trap`)
- **Configs:**
  - `src/combiner/configs/layer2_qqq_pa_batch_a_tuned_2023_2024_v1.yaml`
  - `src/combiner/configs/layer2_sweep_qqq_pa_batch_a_tuned_2023_2024_v1.yaml`

## 3. Diagnostics

See `diagnostics/` and `diagnostics_interpretation.md`.

Key points:

- **Total signals:** 1453
  - failed-trap: **1100** signals (5×220)
  - trading-range: **353** signals (4×63 + 1×101)
- **Cross-family same-bar overlap:** **0** (router does not face same-bar tie-breaks across the two PA families in this window).
- **Within-family duplicates:** extremely high (same-bar overlap equals signals across many pairs), especially failed-trap ⇒ “top_per_strategy=2” mostly increases **conflict rejections**, not behavior diversity.

## 4. Fixed runs

From `fixed_run_summary.csv` (baseline slippage 0.01):

- **failed-trap top1:** trades 220, total_r **12.88**, PF **1.206**, maxDD_r **-16.96**
- **trading-range top1:** trades 63, total_r **25.57**, PF **1.470**, maxDD_r **-22.17**
- **core top1 (1+1):** trades 255, total_r **26.20**, PF **1.261**, maxDD_r **-36.13**

Gate outcome: **PASS** (baseline economics are strong for both families and the core).

## 5. Sweep

- **Grid size:** 48 combos (per `layer2_sweep_qqq_pa_batch_a_tuned_2023_2024_v1.yaml`)
- **Sweep dir:** `sweep_20260510_155256/`
- **Top-unique:** `top_unique_systems.csv` (30+ rows are mostly repeats of the same candidate signals under different knobs)
- **Behavior-unique:** `behavior_unique_systems.csv` shows **2** strong behavior hashes (one trading-range, one failed-trap)

## 6. Cost stress (required)

Source: `cost_stress/cost_stress_results.csv` and `cost_stress_summary.md` (generated with `--cost-stress-top 48`).

Best systems at **0.02 slippage** by candidate set:

- **pa_trading_range:** total_r **+7.03**, PF **1.122**, maxDD_r **-27.85**  → **robust positive**
- **pa_failed_range_trap:** total_r **-11.74**, PF **1.004**, maxDD_r **-34.11** → **cost-fragile**
- **pa_batch_a_core:** total_r **-4.39**, PF **1.029**, maxDD_r **-55.24** → **cost-fragile**

Conclusion: **portfolio/core does not pass the 0.02 gate**, even though the trading-range leg does.

## 7. Daily trade number profile

From sweep rows (e.g. `sweep_.../results.csv`) and behavior summaries:

- Trading-range best path is effectively **trade #1 only** (no benefit from `max_trades_per_day=2` on this system).
- Core systems sometimes generate trade #2 (non-zero `trades_by_daily_trade_number_json`), but this does **not** translate into cost-robust edge under 0.02.

## 8. Interpretation

| Candidate set | Class | Notes |
|--------------|-------|------|
| pa_trading_range | **LAYER2_PROMISING** | Cost-stress stays **positive at 0.02**; behavior hash strong. |
| pa_failed_range_trap | **COST_FRAGILE** | Baseline ok, but fails 0.02 gate. |
| pa_batch_a_core | **SINGLE_FAMILY_ONLY** | Baseline strong, but at 0.02 the core turns negative; do not overclaim portfolio readiness. |

## 9. Decision (exactly one)

### **TUNE_PA_BATCH_A_GRIDS_AGAIN**

Rationale:

- Required gate “cost stress at 0.02” fails for **failed-trap** and **core**, so we cannot justify a mini-WFO design yet.
- Layer 2 indicates the “portfolio” is currently effectively dominated by the more cost-robust leg (`pa_trading_range`) under stress.
- Next tuning should target cost sensitivity for failed-trap and the core combination (still PA-only; no refined_failed merge).

## 10. Explicit non-runs

- mini-WFO not run
- full WFO not run
- live/paper not run
- refined_failed merge not run

