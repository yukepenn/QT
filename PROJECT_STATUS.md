# PROJECT_STATUS (handoff)

## 1. Purpose

QT is a **local, in-sample intraday strategy research framework** centered on **QQQ** 1‑minute RTH bars.

- **Layer 1:** per-strategy parameter sweeps → candidate library (`selected_candidates/*.yaml`).
- **Layer 2:** combiner/router that evaluates candidate sets under simple system constraints (currently **max_open_positions=1**).
- **Layer 3:** **smoke v1** + **component diagnosis v1** + **mini-WFO v1** (`src/walkforward/`) — smoke/diagnosis use fixed frozen systems on fixed folds; **mini-WFO** runs one causal train (2023–2024) / test (2025–2026) split with train-only selection; **full** rolling WFO remains future work.

**Non-goals:** live trading, broker execution, portfolio optimizer, ML pipelines, SPY robustness, or profitability claims.

## 2. Current architecture (high level)

- **Raw data:** local only under `data/raw/` (gitignored).
- **Features:** built from raw bars via `src/features/build_features.py`; **FeatureStore v1** provides in-memory reuse.
- **Strategies:** plugins under `src/strategies/strategy/` implementing fast context path:
  `prepare_signal_context` → `generate_signal_arrays_from_context`.
- **PA Batch A–C (Brooks-style branch):** deterministic **`pa_*`** features (`price_action`, `pa_swings`, extended `regime`, optional `levels` proximity) plus **ten** long-only MVP plugins (Batch A: four; Batch B: four; Batch C: strong-close trend, generic breakout pullback); **loader = 35** strategies. Layer 1 QQQ 2023–2024: baseline `layer1_pa_batch_a_qqq_2023_2024/` (**`TUNE_PA_BATCH_A_GRIDS_FIRST`**); **tuned grids v1** `layer1_pa_batch_a_tuned_qqq_2023_2024_v1/` (10 strict YAMLs; design `reduced_layer2_pa_batch_a_tuned_design.md`); **Batch B+C** formal Layer 1 `layer1_pa_batch_bc_qqq_2023_2024/` (**`TUNE_PA_BATCH_BC_GRIDS_FIRST`** — strict YAMLs only `pa_buy_sell_close_trend`; no Batch B/C Layer 2). Reduced Layer 2 executed: `src/combiner/results/layer2_qqq_pa_batch_a_tuned_2023_2024_v1/` → decision **`TUNE_PA_BATCH_A_GRIDS_AGAIN`** (core fails 0.02 cost gate). **mini-WFO / full WFO not run.** See `pa_batch_a_implementation_summary.md`, `layer1_pa_batch_bc_summary.md`.
- **Layer 1 sweep:** `src/backtest/sweep.py` (fast Numba path).
- **Candidate selection:** `src/research/select_candidates.py` exports `selected_candidates/*.yaml`.
- **Layer 2:** `src/combiner/run.py`, `src/combiner/sweep.py`, `src/combiner/postprocess.py`.
- **Engineering accelerators:**
  - **Signal cache (disk):** `.cache/qt/candidate_signals` (gitignored), from `src/combiner/signal_cache.py`.
  - **FeatureStore (memory):** `src/features/feature_store.py`.
- **Layer 3 smoke / diagnosis (research only):** `src/walkforward/runner.py` loads frozen system YAMLs and calls Layer 2 combiner over YAML-defined folds; **no** per-fold Layer 1/2 grid reruns.
- **Layer 3 mini-WFO v1:** `src/walkforward/mini_wfo.py` orchestrates Layer 1 focused sweeps (narrow strategy list), `select_candidates`, Layer 2 sweep + postprocess, frozen `selected_frozen_system.yaml`, and one out-of-sample test — **not** live-ready.

## 3. Active research baselines (current)

### Layer 1 (candidate libraries)

- **PA Batch A — tuned Layer 1 v1 (QQQ 2023–2024):** `src/research/results/layer1_pa_batch_a_tuned_qqq_2023_2024_v1/` — four `*_tuned_v1.yaml` sweeps (≤768 raw rows each), manifest, strict **10** YAMLs (**5** trading-range + **5** failed-trap), signal diagnosis vs baseline, fast-context check; plan `layer1_pa_batch_a_tuning_plan.md`. Decision **`PROCEED_TO_PA_BATCH_A_REDUCED_LAYER2_DESIGN`** (`layer1_pa_batch_a_tuned_v1_summary.md`); design-only **`reduced_layer2_pa_batch_a_tuned_design.md`**. **PA Layer 2 / mini-WFO / full WFO not run.**
- **PA Batch A — tuned Layer 2 (QQQ 2023–2024):** `src/combiner/results/layer2_qqq_pa_batch_a_tuned_2023_2024_v1/` — diagnostics + fixed rollup + 48-combo sweep + behavior dedupe + cost stress. Summary `layer2_pa_batch_a_tuned_summary.md` (**`TUNE_PA_BATCH_A_GRIDS_AGAIN`**). **mini-WFO / full WFO not run.**
- **PA Batch A — formal Layer 1 (QQQ 2023–2024):** `src/research/results/layer1_pa_batch_a_qqq_2023_2024/` — four focused sweeps (108 raw → 18 dedup rows each), manifest, strict selection (**4** YAMLs, `pa_failed_range_breakout_trap` only), diagnostic relaxed subfolder, signal-rate diagnosis, fast-context check. Decision **`TUNE_PA_BATCH_A_GRIDS_FIRST`**. **Superseded for multi-family candidates by tuned v1 root above.**
- **PA Batch B+C — formal Layer 1 (QQQ 2023–2024):** `src/research/results/layer1_pa_batch_bc_qqq_2023_2024/` — six focused sweeps (288–432 raw), manifest, strict **5** YAMLs (**`pa_buy_sell_close_trend` only**), signal diagnosis, fast-context check, optional diagnostic relaxed CSV. Decision **`TUNE_PA_BATCH_BC_GRIDS_FIRST`**. **Batch B/C Layer 2 / mini-WFO / full WFO not run.**
- **Active (post-hardening):**
  - `src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1/`
  - `src/research/results/layer1_all10_qqq_2025_20260430_posthardening_v1/`
- **Reference:** `src/research/results/layer1_all10_qqq_2023_20260430_posthardening_v1/`
- **Strategy Library v2 Batch 1 (QQQ 2023–2024 Layer 1):** `src/research/results/layer1_v2_batch1_qqq_2023_2024/` — all **six** Batch 1 strategies swept (capped when raw grid > 2000; see `sweep_manifest.csv`), manifest-mode `select_candidates`, **20** YAML exports. **Reduced Layer 2 v2 Batch 1** (same window) ran combiner diagnostics + fixed runs + 1296-combo sweep + postprocess — summary `src/combiner/results/layer2_qqq_v2_batch1_2023_2024/layer2_v2_batch1_summary.md` (**cost-sensitive at 0.02**; **mini-WFO v4 not run**). Layer 1 summary: `src/research/results/strategy_library_v2_batch1_summary.md`.
- **Strategy Library v2 Batch 1 tuned v1 (QQQ 2023–2024, strict only):** Layer 1 root `src/research/results/layer1_v2_batch1_tuned_qqq_2023_2024_v1/` (squeeze + RSI sweeps → **10** YAMLs). Reduced Layer 2 tuned root `src/combiner/results/layer2_qqq_v2_batch1_tuned_2023_2024_v1/` (192-combo sweep, cost stress, behavior dedupe). Narrative + decision: `src/research/results/strategy_library_v2_batch1_tuning_summary.md` (**`TUNE_BATCH1_GRIDS_AGAIN`**). **mini-WFO v4/v5 and full WFO not run.**
- **Strategy Library v2 Batch 1 tuned v2 (QQQ 2023–2024, squeeze-only):** `bollinger_squeeze_breakout_tuned_v2.yaml` + manifest `src/research/results/layer1_v2_batch1_tuned_v2_qqq_2023_2024/` — **no** selected YAMLs (strict **PF ≥ 1.10** gate failed). Tuned_v1 winner diagnostics: `src/research/results/batch1_tuned_v1_cost_diagnostics/`. Decision: `src/research/results/strategy_library_v2_batch1_tuning_v2_summary.md` (**`DEFER_BATCH1_AND_RETURN_TO_REFINED_FAILED_CORE`**). Layer 2 tuned_v2 not run (see `src/combiner/results/layer2_qqq_v2_batch1_tuned_v2_2023_2024/layer2_v2_batch1_tuned_v2_summary.md`).
- **Strategy Library v2 completion Layer 1 (QQQ 2023–2024):** `src/research/results/layer1_v2_completion_qqq_2023_2024/` — nine completion strategies swept (manifest + **30** candidate YAMLs; **2** strategies with no candidates). Summary `layer1_v2_completion_summary.md`; run plan `reduced_layer2_v2_completion_run_plan.md`; design `reduced_layer2_v2_completion_design.md`.
- **Strategy Library v2 completion — reduced Layer 2 (QQQ 2023–2024):** `src/combiner/results/layer2_qqq_v2_completion_2023_2024/` — diagnostics, **15** fixed runs, **756-combo** sweep (`sweep_20260510_025424`), postprocess (dedupe / behavior / cost stress). Summary `layer2_v2_completion_summary.md` (**decision: `TUNE_COMPLETION_GRIDS_FIRST`** — reclaim/trap portfolio failure at default `max_trades_per_day=2`; behavior dedupe **1** path; promising `max_trades_per_day=1` corner). **mini-WFO v4/v5 + full WFO not run.**
- **Strategy Library v2 completion — Layer 2 tuned v1 (QQQ 2023–2024):** `src/combiner/results/layer2_qqq_v2_completion_tuned_v1_2023_2024/` — reclaim excluded from core sweep; diagnostics snapshots; **25** fixed runs; **416-combo** sweep (`sweep_20260510_033030`); postprocess. Summary `layer2_v2_completion_tuned_v1_summary.md` (**`TUNE_COMPLETION_GRIDS_AGAIN`** — economics improved on pair/bundle fixed runs; **behavior_unique still 1**). Planning / diagnosis: `src/research/results/layer2_v2_completion_tuning_plan.md`, `layer2_v2_completion_toxic_path_diagnosis.{md,csv}`. **mini-WFO v4/v5 + full WFO not run.**
- **Strategy Library v2 completion — Layer 2 tuned v2 high-trade (QQQ 2023–2024):** `src/combiner/results/layer2_qqq_v2_completion_tuned_v2_high_trade_2023_2024/` — **16** fixed runs; **480-combo** sweep (`sweep_20260510_040358`); postprocess + `rank_high_trade_systems` + `high_trade_cost_review`. Summary `layer2_v2_completion_tuned_v2_high_trade_summary.md` (**`TUNE_COMPLETION_GRIDS_AGAIN`** — **`behavior_unique` = 2** incl. **`stoch_macd_pair`**, but **0.02** cost fails on flagship high-turnover `stoch_macd_pair` @ `max_trades_per_day=2`). Plan `src/research/results/layer2_v2_completion_tuned_v2_high_trade_plan.md`. **mini-WFO v4/v5 + full WFO not run.**

- **Strategy Library v2 completion (code + tests + Jan smoke only):** nine new fast plugins (**16 → 25** loader count) — `sma20_reclaim_reject`, `macd_momentum_turn`, `stochastic_oversold_cross`, `cci_extreme_snapback`, `adx_dmi_trend_continuation`, `supertrend_atr_flip`, `large_candle_failure`, `multi_day_level_trap`, `prior_close_reclaim`. Feature deltas: SuperTrend columns + multi-session lows (`prior_3day_low`, `prior_5day_low`, `previous_week_low`). Curated pack: `src/research/results/strategy_library_v2_completion_*`. **Layer 2 / mini-WFO / full WFO not run** for this phase; next economics step: **`RUN_LAYER1_V2_COMPLETION_2023_2024`**.

### Layer 2 (combiner roots)

- **Active (post-hardening 2020):**
  - `src/combiner/results/layer2_qqq_2020_20260430_posthardening_strict_v1/`
  - `src/combiner/results/layer2_qqq_2020_20260430_posthardening_relaxed_v1/`
- **Active (recent-window check):**
  - `src/combiner/results/layer2_qqq_2025_20260430_recent_check_v1/`
- **Strategy Library v2 completion (QQQ 2023–2024):** `src/combiner/results/layer2_qqq_v2_completion_2023_2024/` — see `layer2_v2_completion_summary.md`.
- **Strategy Library v2 completion — tuned v1 (QQQ 2023–2024):** `src/combiner/results/layer2_qqq_v2_completion_tuned_v1_2023_2024/` — see `layer2_v2_completion_tuned_v1_summary.md`.
- **Strategy Library v2 completion — tuned v2 high-trade (QQQ 2023–2024):** `src/combiner/results/layer2_qqq_v2_completion_tuned_v2_high_trade_2023_2024/` — see `layer2_v2_completion_tuned_v2_high_trade_summary.md`.
- **Reference:** 2023 post-hardening strict/relaxed roots (see `src/combiner/results/RESULTS_INDEX.md`).

## 4. Current strongest in-sample conclusion (research only)

- The **opening / trap / failed‑ORB family** tends to dominate in the current in-sample QQQ baselines.
- Recent-window `trap_family` top‑1 system remains strong but is **in-sample only**.
- Relaxed/VWAP-heavy paths tend to be **more cost-sensitive**.

No live‑ready claim is implied.

## 5. What not to touch casually

- `tests/` (keep committed)
- `data/raw/` (local data; never commit)
- `src/research/results/**/selected_candidates/*.yaml`
- Post-hardening curated summaries under `src/research/results/` and `src/combiner/results/`
- `.cache/` and `data/cache/` are **rebuildable** and **must not** be committed

## 6. Index docs (start here)

- Config index: `src/combiner/configs/CONFIG_INDEX.md`
- Research results index: `src/research/results/RESULTS_INDEX.md`
- Combiner results index: `src/combiner/results/RESULTS_INDEX.md`
- Artifact policy: `docs/ARTIFACT_POLICY.md`
- Pre‑Layer‑3 readiness summary: `src/research/results/pre_layer3_gate_readiness_summary.md`
- Layer 3 smoke plan: `src/research/results/layer3_smoke_plan_v1.md`

## Frozen configs (Layer 3 smoke only)

- Directory: `src/combiner/configs/frozen/` (plus **`frozen/diagnosis/`** for component decomposition runs).
- Purpose: fixed **research** snapshots wired into `src/walkforward/` smoke/diagnosis runs only.
- These are **not** production or live-trading configs.

## 7. Next intended phases

1. Keep repo hygiene / indexing work mergeable.
2. **Layer 3 smoke v1** and **component diagnosis v1** are runnable on QQQ fixed systems; **causal mini-WFO** remains **not approved** by default — review diagnosis outputs first (`src/walkforward/results/layer3_smoke_v1_diagnosis_qqq_components/`).

