# Layer 2 v2 completion — tuned v2 high-trade rerank plan (QQQ 2023–2024)

## Why tuned v1 chose `TUNE_COMPLETION_GRIDS_AGAIN`

- **`prior_close_reclaim`** toxicity was **removed** from core sweep (diagnostic-only in v1 confirmed ~**-234** R standalone).
- **High-trade fixed paths** were strong (**`stoch_macd_pair`**, **`completion_no_reclaim`**, **`oscillator_momentum_trend`** ~**50–52** R @ 0.01 slip, **~502** trades, PF ~**1.21**).
- **But:** **`behavior_unique` count stayed 1** — trade-sequence dedupe collapsed to the **low-trade `cci_only` / `CCI_EXTREME_SNAPBACK_001`** sweep leaderboard path.
- **`cost_robust_systems.csv`** was **empty** under default thresholds (**min_trades** / PF / DD filters), so **high-trade leaders were not represented** in cost-robust or behavior-deep slices (`--detail-top` too small vs low-trade winners).

**Conclusion:** mini-WFO v4 design **remains blocked** until we prove **high-trade** systems survive **behavior** coverage and **0.02 / 0.03** cost stress, not only score-ranked **`cci_only`**.

## Tuned v2 objective

**`layer2_qqq_v2_completion_tuned_v2_high_trade_2023_2024`:** narrow candidate sets to **pairs / bundles / cores** that showed **~500** trade scale in v1 fixed runs; default **`max_trades_per_day: 2`** in base YAML; sweep **`max_trades_per_day` ∈ {1,2,3}`**; add **`stoch_macd_pair_top_candidates`** (max_per_strategy **2**); isolate **`cci_only_diagnostic`** (not mixed into completion bundles).

Postprocess: **`--detail-top 60`**, **`--behavior-dedupe-top 60`**, **`--dedupe-top 80`**, **`--cost-stress-top 20`**, plus generic **`--min-trades-rank 400`** / **`--rank-high-trade-top 30`** on **`top_unique_systems.csv`**.

Optional **`high_trade_layer2_cost_review.py`:** pivot **`cost_stress_results.csv`** onto **high-trade** `top_unique` rows (no strategy-ID hardcoding in repo core — script is data-driven).

## High-trade leaders to force-rerank / stress

| Family / set | Role |
|--------------|------|
| **`stoch_macd_pair`** | Primary high-trade pair |
| **`stoch_macd_pair_top_candidates`** | Tighter YAML pool (top 2 per leg) |
| **`oscillator_momentum_trend`** | Full oscillator + MACD + Supertrend |
| **`completion_no_reclaim`** | Completion without reclaim / trap |
| **`completion_no_prior_close`** | Adds **`multi_day_level_trap`** only here |
| **`trend_only_pair`** | MACD + Supertrend only |
| **`macd_core`**, **`atr_core`** | Positive singles in v1 |
| **`stochastic_only`** | Stoch baseline |
| **`cci_only_diagnostic`** | Low-trade high-PF reference only |

**Excluded:** `prior_close_reclaim`, `adx_dmi_trend_continuation`, `sma20_reclaim_reject`, `large_candle_failure`.

## Pass / fail gates (this phase)

**Sweep gate (fixed runs):**

- **`stoch_macd_pair`** or **`completion_no_reclaim`** remains **> 40** `total_r` with **PF > 1.10** @ baseline slip (0.01 in config).
- **`trend_only_pair`** or **`macd_core`** / **`atr_core`** stays **positive** `total_r`.
- No **`prior_close_reclaim`** in any candidate set.
- **`collect-fixed-runs`** succeeds.

**Outcome gate (post-sweep, research-only):**

- Prefer **≥ 2** behavior-distinct hashes if trade-detail coverage allows; at minimum document whether **`stoch_macd_pair`** / **`completion_no_reclaim`** appear as **distinct** behavior paths vs **`cci_only_diagnostic`**.
- High-trade leaders: **`total_r` ≥ 0** and **PF or PF_R > 1.05** @ **0.02** slip where cost stress rows exist.
- If still **behavior_unique = 1** but high-trade cost is **sound** → likely **`TUNE_COMPLETION_GRIDS_AGAIN`** (not mini-WFO v4).
- If high-trade fails **0.02** and only **CCI** survives → **`DEFER_COMPLETION_AND_RETURN_TO_REFINED_FAILED_CORE`**.

## Explicit non-runs

- mini-WFO **v4** / **v5**
- **Full WFO**
- **SPY** / **IBKR pull**
- New strategies / **signal logic** / **Layer 1 grids** / **refined_failed_orb** integration
- **Live / paper**
