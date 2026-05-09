# Strategy Library v2 Batch 1 — tuning v2 summary

QQQ only; window **2023–01–01 → 2024–12–31**. **mini-WFO v4/v5 and full WFO were not run.**

## 1. Why tuned v2 was run

Tuned v1 improved **0.02 `total_r`** vs original Batch 1, but **PF at 0.02 ~1.008** and **`behavior_unique = 1`**. This pass targeted **fewer, thicker** squeeze trades (`min_risk_per_share: 0.05`, tighter bandwidth percentiles, higher `target_r`, `max_trades_per_day: 1` at Layer 1) to lift **economic margin** and **PF under stress**.

## 2. What changed vs tuned v1

| Item | tuned_v1 | tuned_v2 |
|------|----------|----------|
| `risk.min_risk_per_share` | 0.03 | **0.05** |
| `features.bb_std` grid | 1.5, 2.0 | **2.0 only** (channels still build 1.5+2.0 columns) |
| `max_bandwidth_percentile` | up to ~0.22 | **0.08–0.15** |
| `risk.stop_mode` | bb_mid, breakout_candle_low | **bb_mid, atr_buffer** |
| `risk.target_r` | 1.25–1.5 | **1.5–2.0** |
| `max_hold` | 45, 60 | **45, 60** |
| Raw grid | 1024 | **576** (72 unique rows after param dedupe) |

RSI **tuned_v2** was **not** added (no evidence of an easy orthogonal improvement).

## 3. Tuned v1 cost diagnosis (Phase 1)

Curated pack: `src/research/results/batch1_tuned_v1_cost_diagnostics/` (from detailed combiner run `diag_v1_vol_top1`, **local** `run_*` under `src/combiner/results/layer2_qqq_v2_batch1_tuned_2023_2024_v1_diagnostics_local/`, **not committed**).

- **Exit mix (winner, 376 trades):** **stop** 194 trades **ΣR ≈ −199.6**; **target** 152 **ΣR ≈ +223.5**; **max_hold** 30 **ΣR ≈ +11.6**. Stops dominate downside; targets carry gross upside.
- **Win/loss shape:** mean R on wins **~+1.38** vs losses **~−0.99**; gross R PF (wins/|losses|) **~1.17** — modest edge per trade; **0.02 slip** compresses net PF toward 1.
- **Risk:** median `risk_per_share` **~0.37** with **0.05** combiner floor on Layer 2 v2 — still meaningful **cost_as_R** at higher slip.
- **RSI:** strict `strict_batch1_tuned` detailed run shows squeeze + RSI **lowers** portfolio `total_r` vs squeeze-only; RSI does **not** improve the path.

## 4. Tuned v2 Layer 1

- **Config:** `src/strategies/testing_parameters/bollinger_squeeze_breakout_tuned_v2.yaml`
- **Sweep:** `sweep_20260509_232104_layer1_v2_batch1_tuned_v2_qqq_2023_2024` (saved under `testing_parameters_results/`, gitignored)
- **Result rows:** 72 (504 grid rows skipped as duplicate `normalized_param_key`)
- **Best row (illustrative):** **268** trades, **total_r ≈ 6.82**, **PF ≈ 1.048**, **max_dd_r ≈ −21.4**
- **Jan 2025 smoke:** non-zero trades; top of capped sample **PF ~1.23** on **14** trades (not comparable to full window).

**Selection:** **No candidates** — **no row** meets **min_profit_factor ≥ 1.10** with **min_trades ≥ 40** (and other strict gates). No `selected_candidates/*.yaml` were written.

## 5. Tuned v2 Layer 2

**Not run** — prerequisite candidate library empty.

## 6. Comparison table (Layer 2 leaders where available)

| Snapshot | baseline trades | baseline total_r | baseline PF | 0.02 total_r | 0.02 PF | 0.03 total_r | behavior_unique | cost_robust rows |
|----------|----------------:|-----------------:|------------:|-------------:|--------:|-------------:|----------------:|-----------------:|
| Original Batch 1 L2 | ~488 | ~34.6 | ~1.15 | ~−0.02 | ~1.04 | negative | 1 | 0 |
| Tuned v1 L2 | 376 | ~35.4 | ~1.113 | **~+10.96** | **~1.008** | ~−10.22 | 1 | 10 |
| Tuned v2 L2 | — | — | — | — | — | — | — | — |

Tuned v2 **Layer 1** alone shows **lower** baseline PF vs tuned v1 after **stricter** risk and frequency controls.

## 7. Decision

**`DEFER_BATCH1_AND_RETURN_TO_REFINED_FAILED_CORE`**

Rationale: tuned v2 **fails** the Layer 1 quality gate (**PF < 1.10** on all rows with sufficient trades). Continuing to squeeze Batch 1 parameters further risks **overfitting** without a new mechanism family. Per plan, **refined failed/gap core** is the better next research lane than another Batch 1 grid pass.

**Explicit non-runs:** mini-WFO v4 **not** run; mini-WFO v5 **not** run; full WFO **not** run.
