# Layer 2 v2 Batch 1 — QQQ 2023–2024

## 1. Purpose

Reduced Layer 2 on **Strategy Library v2 Batch 1** only: combine the **20** Layer 1 YAMLs (strict RSI + Bollinger squeeze; relaxed fade + exhaustion) under `max_open_positions=1`, daily limits, cooldown, and conflict policies. **Mini-WFO v4/v5 and full WFO were not run.**

## 2. Candidate universe

| Bucket | Count | Notes |
|--------|------:|-------|
| Total YAMLs | 20 | From `layer1_v2_batch1_qqq_2023_2024/selected_candidates/` |
| Strict (warnings off) | 10 | `rsi_failure_swing` ×5, `bollinger_squeeze_breakout` ×5 |
| Relaxed (warnings on) | 10 | `bollinger_band_fade_chop` ×5, `consecutive_bar_exhaustion` ×5 |
| Excluded from combiner sets | 0 files | `intraday_ma_crossover`, `donchian_channel_breakout` had **no** Layer 1 candidates — not referenced in YAML `candidate_sets` |

Configs: `src/combiner/configs/layer2_qqq_v2_batch1_2023_2024.yaml`, sweep `layer2_sweep_qqq_v2_batch1_2023_2024.yaml`.

## 3. Diagnostics (`relaxed_batch1`, top 5 per strategy)

- **Candidates:** 20  
- **Total raw signals (sum over candidates):** 7788  
- **By strategy:** `bollinger_band_fade_chop` 2453; `bollinger_squeeze_breakout` 2326; `consecutive_bar_exhaustion` 2069; `rsi_failure_swing` 940  
- **Overlap:** High same-bar overlap within each strategy’s multi-YAML grid (expected — near-duplicate parameter rows). **Opposite-side same-bar** counts were negligible in the top pairs (see `diagnostics/candidate_conflict_summary.csv` / `diagnostics_summary.md`).  
- **Artifacts:** `diagnostics/candidate_signal_summary.csv`, `candidate_overlap_matrix.csv`, `candidate_conflict_summary.csv`, `diagnostics_summary.md`, `candidate_precompute_profile*.csv|md`

Signal cache root (local, not committed): `%LOCALAPPDATA%\qt\layer2_v2_batch1_candidate_signals`.

## 4. Fixed runs (Numba path, `--no-detailed`)

| # | Tag | candidate_set | top | trades | total_r | PF | max_dd_r |
|---|-----|-----------------|----:|-------:|--------:|---:|---------:|
| 1 | fixed_oscillator_reversal_top1 | oscillator_reversal | 1 | 197 | 0.12 | 1.26 | -20.4 |
| 2 | fixed_oscillator_reversal_top5 | oscillator_reversal | 5 | 210 | 1.50 | 1.26 | -23.0 |
| 3 | fixed_volatility_breakout_top1 | volatility_breakout | 1 | 479 | **30.96** | **1.35** | -20.1 |
| 4 | fixed_volatility_breakout_top5 | volatility_breakout | 5 | 643 | **52.82** | 1.23 | -19.7 |
| 5 | fixed_strict_batch1_top1 | strict_batch1 | 1 | 666 | 28.88 | 1.30 | -24.3 |
| 6 | fixed_strict_batch1_top5 | strict_batch1 | 5 | 820 | 49.14 | 1.22 | -27.1 |
| 7 | fixed_relaxed_batch1_top1 | relaxed_batch1 | 1 | 1309 | 35.80 | 1.17 | -34.2 |
| 8 | fixed_relaxed_batch1_top5 | relaxed_batch1 | 5 | 1346 | 50.20 | 1.19 | -36.3 |
| 9 | fixed_range_mean_reversion_diagnostic_top5 | range_mean_reversion_diagnostic | 5 | 685 | 12.69 | 1.08 | -48.1 |
| 10 | fixed_price_action_exhaustion_diagnostic_top5 | price_action_exhaustion_diagnostic | 5 | 558 | 9.93 | 1.06 | -28.2 |

- **Best strict core (single-strategy):** `volatility_breakout` **top5** — highest `total_r` / strong PF (still high trade count → cost-sensitive).  
- **Best strict core (single leg):** `volatility_breakout` **top1** — `BOLLINGER_SQUEEZE_BREAKOUT_001` alone.  
- **Best relaxed blend:** `relaxed_batch1` **top5** — positive R with all four families; **fade** leg contributes **negative** R at the combiner level (noise vs squeeze/RSI).  
- **RSI-only:** small positive R at top1; stacking with squeeze in `strict_batch1` is dominated by squeeze fills.

Rollup: `fixed_run_summary.csv` / `.md`.

## 5. Sweep

- **Run:** yes (fixed-run gate passed — multiple strict positives).  
- **Grid:** \(6 \times 4 \times 3 \times 3 \times 3 \times 2 = 1296\) combos.  
- **Wall time:** ~108 s sweep phase (~123 s including precompute refresh) on warm signal cache.  
- **Output dir (local heavy):** `sweep_20260509_221124/` (gitignored except curated exports at root).  
- **Best `top_unique` (config-deduped):** `volatility_breakout`, `top_per_strategy=5`, `max_trades_per_day=1`, `daily_max_loss_r=-1.5`, `cooldown_after_loss_minutes=0`, `metadata_priority` — **488** trades, **total_r ≈ 34.56**, **PF ≈ 1.15**, **max_dd_r ≈ -12.46** (see `top_unique_systems.csv`).  
- **Best `behavior_unique`:** **1** strong hash bucket in the inspected top — dominated by the same squeeze-heavy trade path; 15/30 inspected rows lacked detailed `trades.csv` for behavior hash (see `behavior_unique_systems.md`).  
- **`cost_robust_systems.csv`:** empty at default postprocess thresholds (high trade counts vs `min-trades-cost-rank`).

## 6. Cost stress (top unique ranks 1–10)

Slippage ladder on the leading **volatility_breakout** systems (see `cost_stress/cost_stress_summary.md`):

| Slippage / share | total_r (illustr.) | PF | Label |
|------------------|-------------------:|---:|-------|
| 0.01 (baseline) | ~34.6 | ~1.15 | in-family strong |
| 0.02 | ~−0.02 | ~1.04 | **edge ~flat** |
| 0.03 | strongly negative | <1 | **cost_fragile** |

Postprocess label: **`positive_but_sensitive`** (not **`robust_positive_at_0_02`**).

## 7. Interpretation

- **Did RSI survive Layer 2?** **Marginally** as a standalone lane (small positive R, PF > 1 at baseline slippage); **does not carry** the portfolio once `bollinger_squeeze_breakout` is present (priority + signal density favor squeeze).  
- **Did Bollinger squeeze survive?** **Yes** — it is the **primary** Batch 1 contributor; sweep leaders are almost entirely squeeze stacks.  
- **Did relaxed fade/exhaustion help?** **Mixed** — including them raises trade count and drawdown; **fade** contributed **negative** R in `relaxed_batch1_top1` attribution. Treat as **diagnostic**, not core, until grids are retuned.  
- **Behavior-distinct?** **No** — behavior dedupe collapsed to **one** dominant pattern among reruns with trades; many grid rows are **parameter-tweaks** of the same path.  
- **Cost-robust enough for mini-WFO v4?** **Not yet** — at **0.02** slippage the best unique systems are ~**flat** on R; **0.03** fails. Combined with weak behavior diversity → **do not** greenlight mini-WFO v4 on this snapshot alone.

## 8. Decision

**`TUNE_BATCH1_GRIDS_FIRST`**

Rationale vs proceed rule: strict Batch 1 **does** show positive R and PF > 1.05 at **baseline** 0.01 slip, but **0.02** stress does **not** clear, **behavior_unique** is **not** plural/meaningful, and drawdown on relaxed stacks is heavy. Prefer **fewer, higher-quality squeeze/RSI rows** (or higher bar on Layer 1 relaxed exports) before designing mini-WFO v4.

---

**Explicit non-runs:** mini-WFO v4 **not** run; mini-WFO v5 **not** run; full WFO **not** run.
