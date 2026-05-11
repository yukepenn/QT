# Layer 2 — QQQ 2020–2026 strict vs relaxed (post-hardening v1)

In-sample full-history research (2020-01-01 → 2026-04-30). **Not live-ready.** Layer 3 was **not** built or executed.

## 1. Executive summary

- **Strict** sweep leaders are dominated by **`opening_family`** with **`FAILED_ORB_001` + `GAP_ACCEPTANCE_FAILURE_001`**, `top_per_strategy=1`, tight daily caps. Baseline **`total_r ≈ 42.3`**, **`profit_factor ≈ 1.13`** at 0.01 slip; cost stress stays **`robust_positive_at_0_02`** but turns negative by **0.03** slip on the stressed replay.
- **Relaxed** grid surfaces **`vwap_control_family`** (`VWAP_RECLAIM_REJECT_001` + `VWAP_TREND_PULLBACK_001`) at higher **`combiner_score`** than strict-only grids, with **`total_r ≈ 30.7`** at baseline — but cost stress is **`positive_but_sensitive`**: **fails at 0.02** slippage on the same stress harness.
- **Precompute filtering (strict sweep):** **15 / 27** candidates in the union (warning-heavy ORB/VWAP YAMLs excluded from strict `candidate_sets`). Relaxed sweep precomputed **all 27** (grid includes `all_with_relaxed`).

## 2. Layer 1 candidate universe

- **27** candidates (15 strict threshold / 12 relaxed), **8** strategies; **`midday_compression_breakout`** and **`vwap_reversal`** empty. See `layer1_2020_posthardening_summary.md`.

## 3. Strict summary

- **Root:** `layer2_qqq_2020_20260430_posthardening_strict_v1/`
- **Diagnostics:** 15 candidates, **18,271** gross candidate signals (subset of full library).
- **Sweep:** `sweep_20260506_005804_sweep_strict_2020_posthardening` — **1440** combos; **~30.8 s** precompute, **~166.6 s** Numba sweep phase (**~180 s** total logged).
- **Best config-unique (rank 1):** `opening_family`, `top_per_strategy=1`, `max_trades_per_day=1`, `daily_max_loss_r=-1.5`, `cooldown_after_loss_minutes=0`, **`FAILED_ORB_001` + `GAP_ACCEPTANCE_FAILURE_001`**, **986** trades, **`total_r=42.32`**, **`profit_factor=1.133`**, **`max_drawdown_r≈-18.99`**.

## 4. Relaxed summary

- **Root:** `layer2_qqq_2020_20260430_posthardening_relaxed_v1/`
- **Diagnostics:** 27 candidates, **18,271** signals (full library).
- **Sweep:** `sweep_20260506_010141_sweep_relaxed_2020_posthardening` — **3360** combos; **~58.7 s** precompute, **~453 s** sweep phase (**~474 s** total logged).
- **Best config-unique (rank 1):** `vwap_control_family`, `top_per_strategy=1`, `max_trades_per_day=2`, `daily_max_loss_r=-1.5`, `cooldown_after_loss_minutes=30`, **`VWAP_RECLAIM_REJECT_001` + `VWAP_TREND_PULLBACK_001`**, **1000** trades, **`total_r=30.72`**, **`profit_factor=1.021`**, **`max_drawdown_r≈-27.85`**.

## 5. Best config-unique system comparison

| Mode | Family | Key IDs | Trades | total_r | PF | Max DD R |
|------|--------|---------|--------|---------|-----|----------|
| Strict | opening_family | FO_001, GAF_001 | 986 | 42.32 | 1.133 | -18.99 |
| Relaxed | vwap_control_family | VWAP_RR_001, VWAP_TP_001 | 1000 | 30.72 | 1.021 | -27.85 |

Strict opening pair delivers higher **R** and **PF** with smaller **drawdown** in this replay.

## 6. Best behavior-unique system comparison

Postprocess reported **one** strong behavior hash in the **top-100** config scan for each mode (many configs map to the same trade sequence):

- **Strict:** `opening_family` / **`FAILED_ORB_001` + `GAP_ACCEPTANCE_FAILURE_001`** — **`total_r=42.32`** (see `behavior_unique_systems.csv`).
- **Relaxed:** `vwap_control_family` / **`VWAP_RECLAIM_REJECT_001` + `VWAP_TREND_PULLBACK_001`** — **`total_r=30.72`**.

## 7. Cost-robust comparison

- **Strict:** `cost_robust_systems.csv` **non-empty** at configured thresholds (0.02 slip replay): leaders still **`robust_positive_at_0_02`**.
- **Relaxed:** `cost_robust_systems.csv` **empty** at the same thresholds — VWAP-heavy leaders do not clear the **0.02** stress bar in this pass.

## 8. Cost stress at 0.01 / 0.02 / 0.03

From `cost_stress_summary.md`:

- **Strict rank-1:** `total_r` **42.32 → 20.39** (0.01 → 0.02); **negative by 0.03** slip.
- **Relaxed rank-1:** `total_r` **30.72 → -46.95** (0.01 → 0.02); **`positive_but_sensitive`**.

## 9. Fixed runs vs sweep winners

`fixed_vs_sweep_comparison.csv`: best **fixed** opening-only run (`opening_family` top5, 10 candidates) shows **`total_r=41.73`** / **1019** trades vs sweep best **`42.32`** / **986** trades — sweep favors a **smaller, higher-priority** pair (`top_per_strategy=1`).

## 10. Daily trade number profile

Relaxed behavior row shows most activity on **daily trade #1** with a thinner tail on **#2** (see `trades_by_daily_trade_number_json` in `behavior_unique_systems.csv`).

## 11. Monthly / quarterly consistency

Period breakdown CSVs were written under **`fixed_runs/`** per run (ignored in git except summaries); review locally before trusting stability claims.

## 12. Family dominance

| Family | Strict | Relaxed |
|--------|--------|---------|
| trap_family | Present in grid; not top unique rank-1 | Same |
| opening_family | **Dominates** top unique | Still strong in grid |
| core5_no_vwap | Collapses to trap-equivalent selection (no ORB in strict subset) | Adds ORB when warnings allowed in other combos |
| vwap_control_family | N/A (warnings excluded) | **Ranks #1** in relaxed dedupe |
| all_strict / all_with_relaxed | Strict: 15-candidate core only | Relaxed: full 27 |

**Note:** YAMLs for **`orb_continuation`**, **`vwap_reclaim_reject`**, etc. carry **`relaxed_filter`** warnings; **`strict_core`** in YAML lists `vwap_reclaim_reject` but **`include_warnings: false`** drops those rows — effective strict core matches **trap + gap + prior** only.

## 13. Compare against 2023 shorter-window conclusions

- **Strict trap / opening:** Still **cost-meaningful** at **0.02** in this longer window; leader is **opening** (failed_orb + gap) rather than a wider trap stack.
- **Relaxed VWAP:** Remains **cost-sensitive** ( **`positive_but_sensitive`** , fails 0.02 stress on leaders).
- **ORB / retest / failed_orb:** **failed_orb** + **gap** remain the **dominant** strict pair; ORB continuation candidates are mostly **relaxed-only** and did not drive strict sweep winners.

## 14. Research conclusion

- Labels: **`robust_candidate_found`** (strict, **conditional** — only through **0.02** slip in this harness), **`positive_but_cost_sensitive`** (relaxed VWAP leaders), **`no_clear_system`** for deployment (single-window, negative combiner_score on many rows, Layer 3 absent).

## 15. Layer 3 smoke gate

No system is recommended for **immediate** Layer 3 smoke: relaxed leaders **fail** cost stress at **0.02**; strict leaders **degrade** sharply by **0.03** and show **negative combiner_score** at baseline. See `layer3_gate_after_2020_posthardening.md`.
