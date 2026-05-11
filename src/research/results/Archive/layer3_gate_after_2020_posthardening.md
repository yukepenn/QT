# Layer 3 gate — after QQQ 2020–2026 post-hardening v1

## 1. Purpose

Record **research-only** criteria for any **future** Layer 3 smoke (walk-forward / holdout), without implementing or running Layer 3 in this phase.

## 2. What would qualify for Layer 3 smoke

A system would be worth **considering** only if, **at minimum**:

- **Behavior-unique** (not merely a parameter permutation of the same trade path).
- **`total_r > 0`** at **baseline** (0.01 slip in current harness).
- **`total_r > 0`** at **0.02** slippage in **`cost_stress`** replay.
- **`profit_factor_r > 1.0`** when available.
- **`max_drawdown_r`** not catastrophic **relative** to R (no fixed dollar claim).
- **Monthly / quarterly** attribution **not** a single isolated burst (manual review of period CSVs).
- Not **purely** **relaxed_warning** candidates unless explicitly justified.

## 3. Candidate systems from strict

- **Config- / behavior-unique leader:** `opening_family`, **`FAILED_ORB_001` + `GAP_ACCEPTANCE_FAILURE_001`**, ~**986** trades, **`total_r≈42.3`** @ 0.01 slip.
- **Cost stress:** **`robust_positive_at_0_02`** in summary MD; **fails by 0.03** slip.
- **Combiner score:** still **negative** at baseline (research penalty object).

## 4. Candidate systems from relaxed

- **Leader:** `vwap_control_family`, **`VWAP_RECLAIM_REJECT_001` + `VWAP_TREND_PULLBACK_001`**, **`total_r≈30.7`** @ 0.01 slip.
- **Cost stress:** **`positive_but_sensitive`** — **negative** **`total_r`** already at **0.02** slip in `cost_stress_summary.md`.
- **`cost_robust_systems.csv`:** **empty** at configured thresholds.

## 5. Cost robustness check

Strict opening pair: **passes** **0.02** replay in cost-stress tables; **does not** pass **0.03**. Relaxed VWAP pair: **fails** **0.02**.

## 6. Period stability check

Not auto-certified: inspect **`fixed_runs/**/period_breakdown*.csv`** locally (artifacts mostly git-ignored).

## 7. Recommendation

- **Do not** run Layer 3 smoke **yet**.
- Next manual step: **out-of-sample design** (dates, embargo, cost model) before any Layer 3 implementation.

## 8. Explicit statement

- **Layer 3 was not built.**
- **No Layer 3 command was run** in this phase (no walk-forward engine invocation, no new Layer 3 scripts).
