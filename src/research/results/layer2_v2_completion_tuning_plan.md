# Layer 2 v2 completion — tuned v1 plan (QQQ 2023–2024)

## 1. Why the prior decision was `TUNE_COMPLETION_GRIDS_FIRST`

The first reduced Layer 2 completion (`layer2_qqq_v2_completion_2023_2024/`) showed:

- A **strong** config corner at **`max_trades_per_day=1`**, **`strict_completion_core`**, **`top_per_strategy=1`** (~**54.3** `total_r` @ 0.01 slip, PF ~**1.26**, maxDD ~**-13.1** R).
- **Cost stress:** still **>0** `total_r` and PF **>1.05** at **0.02** slip on that corner; **0.03** slip turns negative.
- **Behavior dedupe collapsed to 1** path among detailed top runs — not mini-WFO v4-ready.
- **`level_reclaim_family`** and any set including **`prior_close_reclaim`** with **`multi_day_level_trap`** produced **catastrophic** portfolio R (~**-219** R): attribution shows **`prior_close_reclaim`** carrying ~**-218** R while **`multi_day_level_trap`** is near flat/slightly negative in those fixed runs.
- **`supertrend_atr_flip`** had **zero executed trades** in the sweep’s best **`strict_completion_core`** row at **`max_trades_per_day=1`** — crowded out by higher-priority / higher-score oscillators and MACD.
- **ADX** remained weak diagnostic-only.

So: economics were **not** a total loss, but **composition and behavior diversity** failed.

## 2. What worked (preserve)

| Area | Evidence |
|------|----------|
| **Oscillator stack** | `oscillator_reversal_family` fixed runs: up to **62** `total_r`, PF ~**1.26** (top3). |
| **MACD alone** | `macd_momentum_family` positive (**~16–26** R). |
| **Supertrend alone** | `atr_trend_family` positive (**~17–21** R). |
| **Tight daily cap** | Sweep winners concentrated at **`max_trades_per_day=1`**. |

## 3. What failed (fix in this pass)

| Issue | Action in tuned v1 |
|-------|---------------------|
| **`prior_close_reclaim` toxicity** | **Exclude** from all core / sweep candidate sets; optional **`prior_close_diagnostic`** fixed-run only. |
| **Behavior collapse** | Narrow grids + pairs (`stoch_macd_pair`, `macd_supertrend_pair`, …) to seek **≥2** distinct trade paths. |
| **Supertrend starvation** | Sets that **omit** reclaim and optionally isolate **MACD + Supertrend** pairs. |
| **ADX noise** | **Omit** from tuned configs entirely. |

## 4. Tuned candidate sets (exact)

Defined in `layer2_qqq_v2_completion_tuned_v1_2023_2024.yaml`:

- `oscillator_core`, `stochastic_only`, `cci_only`
- `macd_core`, `atr_core`, `momentum_trend_core` (MACD + Supertrend)
- `stoch_macd_pair`, `stoch_supertrend_pair`, `macd_supertrend_pair`
- `oscillator_momentum_trend` (four strategies, no reclaim)
- `multi_day_only`
- `completion_no_prior_close` (stoch, cci, macd, supertrend, multi_day)
- `completion_no_reclaim` (stoch, cci, macd, supertrend — no multi_day)
- **`prior_close_diagnostic`** — `prior_close_reclaim` only; **fixed runs only**, **not** in sweep grid.

**Excluded:** `prior_close_reclaim` from core sets, `adx_dmi_trend_continuation`, `sma20_reclaim_reject`, `large_candle_failure`.

## 5. Sweep grid (focused)

File: `layer2_sweep_qqq_v2_completion_tuned_v1_2023_2024.yaml`

`13 × 2 × 2 × 2 × 2 × 2 = **416**` combos (`candidate_set` × `top_per_strategy` × `max_trades_per_day` × `daily_max_loss_r` × `cooldown` × `priority_policy`).

**Not in this phase:** `top_per_strategy=3`, `max_trades_per_day=3`, relaxed candidates.

## 6. Pass / fail gates

**Fixed-run gate (before sweep):**

- `oscillator_core` **or** `stochastic_only` stays clearly **positive** on `total_r` and PF.
- `macd_core` **or** `atr_core` stays **positive**.
- At least **one** pair / `momentum_trend_core` remains **positive** and not far worse than the best single-family baseline.
- **`prior_close_diagnostic`** (if run) must **not** be folded into core sets if deeply negative; it is diagnostic-only.

**Sweep gate:** run **416** sweep only if the fixed-run gate passes.

**Outcome gates (for `PROCEED_TO_MINI_WFO_V4_DESIGN` in summary):**

- **≥2** behavior-unique systems with strong hashes.
- **0.02** slip: `total_r ≥ 0` and PF or PF_R **> 1.05** on leading configs.
- No dependence on **`prior_close_reclaim`** in top systems.
- Not **only** `stochastic_only` clones at the top.

## 7. Explicit non-runs

- **mini-WFO v4 / v5** — not run  
- **Full WFO** — not run  
- **Live / paper** — not run  
- **Layer 1 grid changes** — not run  
- **Strategy signal logic changes** — not run  
- **refined_failed_orb integration** — not run (this phase is completion-only combiner tuning)
