# Layer 2 v2 completion — toxic path diagnosis (curated inputs only)

**Sources:** `src/combiner/results/layer2_qqq_v2_completion_2023_2024/fixed_run_summary.csv`, `top_unique_systems.csv` (row 1), `diagnostics/candidate_conflict_summary.csv`, `layer2_v2_completion_summary.md`.  
**No** new sweep or trade-file regeneration for this diagnosis.

## Q1 — `prior_close_reclaim` IDs in toxic runs

- **`level_reclaim_family` top1:** `MULTI_DAY_LEVEL_TRAP_001`, `PRIOR_CLOSE_RECLAIM_001`.
- **`level_reclaim_family` top3:** `MULTI_DAY_LEVEL_TRAP_001–003`, `PRIOR_CLOSE_RECLAIM_001–003`.
- **`strict_completion_core` top1 / top3:** always includes `PRIOR_CLOSE_RECLAIM_001` (and `_002`, `_003` in top3) alongside the other six-strategy `#1`/`#3` YAMLs.

## Q2 — Most negative R contributors (level_reclaim)

From `r_by_strategy_json` on **`fixed_level_reclaim_family_top1`**:

| Strategy | Approx R |
|----------|----------|
| `prior_close_reclaim` | **-218.40** |
| `multi_day_level_trap` | **-0.34** |

**Conclusion:** **`PRIOR_CLOSE_RECLAIM_001`** (family) is the **dominant** toxic contributor; multi-day is **not** the driver of ~-219 R.

## Q3 — Multi-day vs reclaim

**`multi_day_level_trap`** is **roughly flat to slightly negative** in these combiner portfolios; **`prior_close_reclaim`** supplies the **large negative** tail. Layer 1 alone had positive reclaim rows; **combiner interaction + priority + max_trades** turns reclaim toxic here.

## Q4 — Supertrend 0 fills (top strict core, `max_trades_per_day=1`)

The ranked **`strict_completion_core`** winner (`top_unique_systems.csv`, `max_trades_per_day=1`) allocates trades to **`stochastic_oversold_cross`**, **`macd_momentum_turn`**, **`prior_close_reclaim`**, **`multi_day_level_trap`**, **`cci_extreme_snapback`** — **`supertrend_atr_flip` trade count = 0** because **only one trade per day** is allowed and **higher-priority / higher-score** candidates consume the slot on overlapping days.

## Q5 — Stochastic vs CCI (distinctness)

In **`oscillator_reversal_family` top1**: **500** stoch trades vs **109** cci trades; R split ~**38** vs ~**19**. Stochastic **dominates** frequency and R; CCI is **additive** but **not** a separate behavior path at the trade-sequence level until CCI gets more slots (higher `max_trades_per_day` or isolation).

## Q6 — MACD vs Supertrend overlap

Standalone **`macd_momentum_family`** and **`atr_trend_family`** are both **positive**. Diagnostics **`candidate_conflict_summary.csv`** shows **non-trivial same-bar contention** between MACD and Supertrend candidates — they can be **complementary** when reclaim is removed and daily caps allow both, but **crowding** can still occur under `metadata_priority`.

## Machine-readable table

See `layer2_v2_completion_toxic_path_diagnosis.csv`.
