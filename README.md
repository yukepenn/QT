# QT — Strategy Research Framework

This is a **local research framework** for IBKR historical 1-minute data.

- **Current focus:** strategy discovery and fast parameter sweeps.
- **Not in scope yet:** live trading, dashboard, ML, portfolio optimizer, walk-forward automation, or multiprocessing in the sweep.

Data pull into Parquet is already solved; ongoing work centers on **strategy plugins**, **backtesting**, and **sweeps**.

## Research platform hardening (before Layer 3)

**Current state**

- Layer **1** (per-strategy sweeps + candidate YAMLs) and Layer **2** (combiner run/sweep/postprocess) **exist** on `main`.
- Layer **3 full walk-forward** (rolling train→freeze→test automation) is **not** implemented.
- **Layer 3 smoke v1** (`src/walkforward/`) evaluates **frozen** Layer 2 systems on fixed date folds — **not** parameter search and **not** live-ready.
- **Layer 3 smoke diagnosis v1** uses additional frozen **component** configs (`src/combiner/configs/frozen/diagnosis/`) to explain smoke outcomes — still **not** WFO and **not** live-ready.
- **QQQ** is the **complete** research symbol for 2020–2026 RTH on a typical backfill; **SPY** is often **incomplete** — do not use SPY for robustness until coverage matches.

**Hardening completed (Commits A–D)**

- Execution validation, **max_drawdown** from **zero**, stop/target/finite checks, combiner cooldown + **`daily_trade_number`**
- No-lookahead hygiene: **`full_session_*_LOOKAHEAD`**, intraday **so-far** columns, ORB **`*_known`**, centralized **`FeatureBuildConfig` / `feature_key`**
- **`BaseStrategy.validate_config`** + **`src/utils/config_validation.py`**, **`context_key`** / **`normalized_param_key`** audit
- Combiner **behavior-level dedupe**, **cost-as-R**, **`profit_factor_r`**, period breakdowns, cost-aware leaderboards (research filters only)

**Conventions (summary)**

- **Next-bar open** execution model per engine/combiner docs; validate stop/target **sides** and **finite** prices.
- Strategies must **not** require LOOKAHEAD columns in **`required_features`**; prefer ORB **`*_known`** for gated logic.
- **`context_key`**: any config field that changes **`prepare_signal_context`** outputs belongs in the key.
- **`normalized_param_key`**: any field that changes **final signals** belongs in the key.
- **PA plugins (2026-05-10):** `context_key` was narrowed to **window / ATR-column selectors only** (plus a fixed strategy tag); score gates, entry windows, and risk/backtest axes stay in **`normalized_param_key`**. Rationale + tables: `src/research/results/pa_context_key_cache_optimization_summary.md`.
- **PA Brooks primitives (2026-05-10):** Shared bar / swing / regime-router / magnet columns in `src/features/`; canonical PA helpers live in **`src/strategies/common/pa.py`** with **`strategy/pa_common.py`** / **`pa_batch_a_utils.py`** as import shims. Plan + summary: `pa_brooks_framework_optimization_summary.md`; cleanup note: `pa_brooks_primitives_cleanup_summary.md`. **No** Layer 2 / mini-WFO reruns.
- Layer 2 postprocess: **`top_unique_*`** = config dedupe; **`behavior_unique_*`** = trade-sequence dedupe from **`trades.csv`**.

**Rerun warning**

- Saved Layer 1 / Layer 2 roots from **before** A–D (e.g. `layer1_all10_qqq_2020_20260430_v1`, `layer2_qqq_2020_20260430_v2_relaxed`) are marked **`PRE_HARDENING_STALE.md`**. **Do not use their rankings for Layer 3** until you rerun from **`rerun_plan_after_hardening.md`**.

**Next phase**

- **PA Batch B/C diagnostics v1:** Gate + exit summaries under `src/research/results/pa_batch_bc_gate_diagnostics_v1/` and `pa_batch_bc_exit_diagnostics_v1/` — historical design aid.
- **PA Batch B/C tuned v2 Layer 1:** Curated root `src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v2/` (manifest, strict YAMLs for **`pa_buy_sell_close_trend`** + **`pa_climax_reversal`**, gate preflight `pa_batch_bc_gate_diagnostics_v2_preflight/`, exit `pa_batch_bc_exit_diagnostics_v2/`). Layer 1 decision **`PROCEED_TO_PA_BATCH_BC_REDUCED_LAYER2_DESIGN`** — combiner design: `src/research/results/reduced_layer2_pa_batch_bc_tuned_v2_design.md`.
- **PA Batch B/C tuned v3 Layer 1:** Curated root `src/research/results/layer1_pa_batch_bc_tuned_qqq_2023_2024_v3/` (`*_tuned_v3.yaml`, **1152×2** sweeps, diversity diagnostics `pa_batch_bc_candidate_signal_diversity_v3/`, exit `pa_batch_bc_exit_diagnostics_v3/`). Summary `layer1_pa_batch_bc_tuned_v3_summary.md` — **`TUNE_PA_BATCH_BC_GRIDS_AGAIN`** (climax `pure_signal_hash` still **1** across strict **score-top five**). **Reduced Layer 2 v3 (strict original root) not run.**
- **PA Batch B/C climax diversity repair + repaired Layer 2 v3:** Raw sweep signal audit `pa_batch_bc_raw_signal_diversity_v3/` (`sweep_result_signal_diversity.py`); repaired YAMLs `layer1_pa_batch_bc_tuned_qqq_2023_2024_v3/selected_candidates_repaired/` + `pa_batch_bc_candidate_signal_diversity_repaired_v3/`; narrative `pa_batch_bc_diversity_repair_summary.md`. Reduced combiner **`src/combiner/results/layer2_qqq_pa_batch_bc_repaired_v3_2023_2024/`** — behavior + cost completion **`layer2_pa_batch_bc_repaired_v3_behavior_completion.md`**; summary decision **`TUNE_PA_BATCH_BC_GRIDS_AGAIN`** (**mini-WFO not run**).
- **PA Batch B/C tuned v2 reduced Layer 2 (QQQ 2023–2024):** Curated root `src/combiner/results/layer2_qqq_pa_batch_bc_tuned_v2_2023_2024/` (diagnostics, fixed rollup, **144-combo** sweep postprocess). Summary **`layer2_pa_batch_bc_tuned_v2_summary.md`** — decision **`TUNE_PA_BATCH_BC_GRIDS_AGAIN`**. **mini-WFO / full WFO / live not run.**
- **Layer 3 smoke v1:** Run fixed-system temporal checks with `python src/walkforward/runner.py --config src/walkforward/configs/qqq_fixed_system_smoke_v1.yaml` (see `PROJECT_STATUS.md`). Still **not** full walk-forward and **not** live-ready.
- **Layer 3 smoke diagnosis v1:** Component decomposition run: `python src/walkforward/runner.py --config src/walkforward/configs/qqq_fixed_system_diagnosis_v1.yaml --tag layer3_diagnosis --use-signal-cache` (optional `--signal-cache-root` on OneDrive). Outputs: `src/walkforward/results/layer3_smoke_v1_diagnosis_qqq_components/`. **Not** mini-WFO.
- **Layer 3 mini-WFO v1 (causal single split):** Train 2023–2024 → select Layer 1 + Layer 2 on train only → freeze → test 2025–2026 once: `python src/walkforward/mini_wfo.py --config src/walkforward/configs/qqq_mini_wfo_2023_2024_train_2025_202604_test_v1.yaml --tag mini_wfo_v1 --use-signal-cache --signal-cache-root <cache>` (`--validate-only`, `--resume-from layer2`, `--resume-from after_sweep`). Curated outputs: `src/walkforward/results/layer3_mini_wfo_qqq_2023_2024_train_2025_202604_test_v1/`. **Not** full WFO.
- User-approved **post-hardening** Layer 1 → selection → Layer 2 strict/relaxed → postprocess remains the baseline research loop. Details: `src/research/results/hardening_closeout_20260505.md`, `rerun_plan_after_hardening.md`, `tests/README.md`.
- **Layer 2 precompute cleanup (2026-05-06):** `src/combiner/candidate.py` split into `candidate` / `precompute` / `diagnostics`; Layer 2 context cache matches Layer 1 intent **`(strategy, feature_key, strategy.context_key(cfg))`** (normalized); strategy instances cached; `candidate_precompute_profile_summary.csv` next to `candidate_precompute_profile.csv`. Summary: `src/research/results/layer2_precompute_cleanup_summary.md`. **No strategy logic or sweep grid changes.**
- **Layer 2 persistent signal cache:** Optional on-disk cache for per-candidate signal arrays (`src/combiner/signal_cache.py`); default root `.cache/qt/candidate_signals` (gitignored). Flags: `--use-signal-cache`, `--signal-cache-root`, `--refresh-signal-cache`; optional YAML block `precompute:`. Summary: `src/research/results/layer2_signal_cache_summary.md`. Safe to delete cache dirs; research outputs only.
- **FeatureStore v1:** Centralized in-memory feature DataFrame caching (`src/features/feature_store.py`) for reuse across Layer 1 sweep and Layer 2 precompute. Preserves `feature_key_from_config` + `build_features_from_config` behavior (no formula changes). Summary: `src/research/results/feature_store_v1_summary.md`.

## 0. Current project status

**Implemented**

- Historical IBKR 1-min pull into Parquet.
- Raw data reader (`src/data/read_bars.py`).
- In-memory feature layer (`src/features/build_features.py`).
- Strategy plugin interface (`BaseStrategy` in `src/strategies/strategy/base.py`).
- Strategy plugins including ORB continuation (`orb_continuation`), VWAP reversal (`vwap_reversal`), **Strategy Library v1** additions (`failed_orb`, `orb_retest_continuation`, `vwap_trend_pullback`, `vwap_reclaim_reject`, `prior_day_level_trap`, `gap_acceptance_failure`, `midday_compression_breakout`, `afternoon_continuation`), and **Strategy Library v2 Batch 1** (`intraday_ma_crossover`, `rsi_failure_swing`, `bollinger_squeeze_breakout`, `bollinger_band_fade_chop`, `donchian_channel_breakout`, `consecutive_bar_exhaustion` — see **Strategy Library v2 Batch 1** below), plus **PA Batch A** (`pa_trading_range_bls_hs`, `pa_failed_range_breakout_trap`, `pa_tight_channel_pullback`, `pa_mtr_reversal`), **PA Batch B** (`pa_broad_channel_zone`, `pa_climax_reversal`, `pa_second_entry_pullback`, `pa_wedge_reversal`), and **PA Batch C** (`pa_buy_sell_close_trend`, `pa_generic_breakout_pullback` — deterministic `pa_*` feature layer; formal Layer 1 QQQ 2023–2024: Batch A `layer1_pa_batch_a_qqq_2023_2024/` + **tuned v1** `layer1_pa_batch_a_tuned_qqq_2023_2024_v1/`; **Batch B+C** baseline `layer1_pa_batch_bc_qqq_2023_2024/` (decision **`TUNE_PA_BATCH_BC_GRIDS_FIRST`**) + tuned v1 `layer1_pa_batch_bc_tuned_qqq_2023_2024_v1/` (decision **`TUNE_PA_BATCH_BC_GRIDS_AGAIN`**); reduced Layer 2 root `src/combiner/results/layer2_qqq_pa_batch_a_tuned_2023_2024_v1/` — decision **`TUNE_PA_BATCH_A_GRIDS_AGAIN`**; see `pa_batch_a_implementation_summary.md`, `pa_batch_b_implementation_summary.md`, `layer1_pa_batch_bc_summary.md`, `layer1_pa_batch_bc_tuned_v1_summary.md`).
- YAML default parameters (`src/strategies/parameters/`).
- YAML sweep grids (`src/strategies/testing_parameters/`).
- Readable / debug backtest engine (`src/backtest/engine.py`).
- Generic Numba fast execution (`src/backtest/fast.py`).
- Dynamic sweep runner: `load_strategy` → cached `prepare_signal_context` → `strategy.generate_signal_arrays_from_context` → `run_fast_backtest_from_arrays` (`src/backtest/sweep.py`).

## Active baseline quick links

- **Project handoff:** `PROJECT_STATUS.md`
- **Artifact policy:** `docs/ARTIFACT_POLICY.md`
- **Layer 2 config index:** `src/combiner/configs/CONFIG_INDEX.md`
- **Research results index:** `src/research/results/RESULTS_INDEX.md`
- **Combiner results index:** `src/combiner/results/RESULTS_INDEX.md`
- **Layer 3 smoke plan:** `src/research/results/layer3_smoke_plan_v1.md`
- **Walk-forward smoke runner:** `src/walkforward/runner.py` + configs under `src/walkforward/configs/`
- **Frozen smoke configs (not live):** `src/combiner/configs/frozen/` and `src/combiner/configs/frozen/diagnosis/`
- **Layer 3 smoke v1 results:** `src/walkforward/results/layer3_smoke_v1_qqq_fixed_systems/`
- **Layer 3 diagnosis v1 results:** `src/walkforward/results/layer3_smoke_v1_diagnosis_qqq_components/`
- **Layer 3 mini-WFO v1 results:** `src/walkforward/results/layer3_mini_wfo_qqq_2023_2024_train_2025_202604_test_v1/`

**Active baselines (QQQ, post-hardening):**

- Layer 1: `src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1/`, `src/research/results/layer1_all10_qqq_2025_20260430_posthardening_v1/`
- Layer 2: `src/combiner/results/layer2_qqq_2020_20260430_posthardening_{strict,relaxed}_v1/`, `src/combiner/results/layer2_qqq_2025_20260430_recent_check_v1/`

- Sweep result archival under `src/strategies/testing_parameters_results/`.

**Strategy Library v1 (plugins)**

Phase scope: **strategy plugins + YAML + smoke/capped sweeps only** — not a full Layer 1 production sweep across every strategy. Next stage is broader focused sweeps and candidate selection.

Registered plugins (see `src/strategies/loader.py`):

- `orb_continuation`
- `vwap_reversal`
- `failed_orb`
- `orb_retest_continuation`
- `vwap_trend_pullback`
- `vwap_reclaim_reject`
- `prior_day_level_trap`
- `gap_acceptance_failure`
- `midday_compression_breakout`
- `afternoon_continuation`

**Strategy Library v2 Batch 1 (plugins, QQQ, long-only MVP v1)**

Orthogonal mechanism families (MA / oscillator / Bollinger / Donchian / exhaustion); not ORB/VWAP/gap/trap duplicates. Curated plan + smoke health + interpretation:

- `src/research/results/strategy_library_v2_batch1_plan.md`
- `src/research/results/strategy_library_v2_batch1_audit.md` / `strategy_library_v2_batch1_audit.csv`
- `src/research/results/strategy_library_v2_batch1_grid_review.md` / `strategy_library_v2_batch1_grid_review.csv`
- `src/research/results/strategy_library_v2_batch1_health.csv` / `strategy_library_v2_batch1_health.md`
- `src/research/results/strategy_library_v2_batch1_summary.md`
- Layer 1 (QQQ 2023–2024): `src/research/results/layer1_v2_batch1_qqq_2023_2024/` (`sweep_manifest.*`, `selected_candidates/`, `candidate_selection_config.md`, `MANIFEST_CONSISTENCY_NOTE.md`)
- Reduced Layer 2 v2 Batch 1 (QQQ 2023–2024): configs `src/combiner/configs/layer2_qqq_v2_batch1_2023_2024.yaml` + `layer2_sweep_qqq_v2_batch1_2023_2024.yaml`; curated results `src/combiner/results/layer2_qqq_v2_batch1_2023_2024/layer2_v2_batch1_summary.md` (**cost-sensitive at 0.02**; **mini-WFO v4 not run**)
- Reduced Layer 2 **v2 completion** (QQQ 2023–2024): `layer2_qqq_v2_completion_2023_2024.yaml` + sweep; curated `src/combiner/results/layer2_qqq_v2_completion_2023_2024/` (`layer2_v2_completion_summary.md`, diagnostics, fixed rollup, **756-combo** postprocess). **`TUNE_COMPLETION_GRIDS_FIRST`**. **mini-WFO v4/v5 + full WFO not run.**
- Layer 2 **v2 completion tuned v2 high-trade** (QQQ 2023–2024): `layer2_qqq_v2_completion_tuned_v2_high_trade_2023_2024.yaml` + sweep; curated `src/combiner/results/layer2_qqq_v2_completion_tuned_v2_high_trade_2023_2024/` (`layer2_v2_completion_tuned_v2_high_trade_summary.md`, fixed rollup, **480-combo** postprocess, `rank_high_trade_systems`, `high_trade_cost_review`). **`TUNE_COMPLETION_GRIDS_AGAIN`** (**`behavior_unique` = 2**; **0.02** stress fails on primary **`stoch_macd_pair`** @ `max_trades_per_day=2`). Plan `layer2_v2_completion_tuned_v2_high_trade_plan.md`. **mini-WFO v4/v5 + full WFO not run.**
- Layer 2 **v2 completion tuned v1** (QQQ 2023–2024): `layer2_qqq_v2_completion_tuned_v1_2023_2024.yaml` + sweep; curated `src/combiner/results/layer2_qqq_v2_completion_tuned_v1_2023_2024/` (`layer2_v2_completion_tuned_v1_summary.md`, diagnostics snapshots, fixed rollup, **416-combo** postprocess). **`TUNE_COMPLETION_GRIDS_AGAIN`**. **mini-WFO v4/v5 + full WFO not run.**
- **Tuned v1 (strict squeeze + RSI only):** testing grids `bollinger_squeeze_breakout_tuned_v1.yaml`, `rsi_failure_swing_tuned_v1.yaml`; Layer 1 `src/research/results/layer1_v2_batch1_tuned_qqq_2023_2024_v1/`; Layer 2 `src/combiner/configs/layer2_qqq_v2_batch1_tuned_2023_2024_v1.yaml` + sweep; curated results `src/combiner/results/layer2_qqq_v2_batch1_tuned_2023_2024_v1/layer2_v2_batch1_tuned_summary.md`; narrative `src/research/results/strategy_library_v2_batch1_tuning_summary.md` (**decision: `TUNE_BATCH1_GRIDS_AGAIN`**; mini-WFO v4/v5 + full WFO **not** run)
- **Tuned v2 (squeeze-only grid, stricter min_risk / bandwidth):** `bollinger_squeeze_breakout_tuned_v2.yaml`; Layer 1 manifest `src/research/results/layer1_v2_batch1_tuned_v2_qqq_2023_2024/` (**no YAML exports** — baseline PF gate failed); tuned_v1 winner trade-quality pack `src/research/results/batch1_tuned_v1_cost_diagnostics/`; narrative `strategy_library_v2_batch1_tuning_v2_summary.md` (**`DEFER_BATCH1_AND_RETURN_TO_REFINED_FAILED_CORE`**). Layer 2 tuned_v2 **skipped** (stub `src/combiner/results/layer2_qqq_v2_batch1_tuned_v2_2023_2024/layer2_v2_batch1_tuned_v2_summary.md`). **mini-WFO v4/v5 + full WFO not run.**
- Design + rationale: `src/research/results/reduced_layer2_v2_batch1_design.md`

Registered plugins (also in `loader.py`):

- `intraday_ma_crossover`
- `rsi_failure_swing`
- `bollinger_squeeze_breakout`
- `bollinger_band_fade_chop`
- `donchian_channel_breakout`
- `consecutive_bar_exhaustion`

**Strategy Library v1 snapshot:** Use **post-hardening** Layer 1 bundles (e.g. **`src/research/results/layer1_all10_qqq_2023_20260430_posthardening_v1/sweep_manifest.csv`**) instead of removed legacy `layer1_all10_qqq_v1/`. The loader currently registers **35** strategies (**v1 + v2 Batch 1 + v2 completion + PA Batch A–C** plugins); completion plugin pack: **`src/research/results/strategy_library_v2_completion_summary.md`**. **QQQ 2023–2024 Layer 1 economics** for the nine completion names: **`src/research/results/layer1_v2_completion_qqq_2023_2024/`** (manifest + **30** candidate YAMLs; summary `layer1_v2_completion_summary.md`). **Reduced Layer 2 v2 completion** (same window): configs `layer2_qqq_v2_completion_2023_2024.yaml` + `layer2_sweep_qqq_v2_completion_2023_2024.yaml`; curated results **`src/combiner/results/layer2_qqq_v2_completion_2023_2024/layer2_v2_completion_summary.md`** (**decision: `TUNE_COMPLETION_GRIDS_FIRST`**). **Layer 2 v2 completion tuned v1:** configs `layer2_qqq_v2_completion_tuned_v1_2023_2024.yaml` + `layer2_sweep_qqq_v2_completion_tuned_v1_2023_2024.yaml`; curated **`src/combiner/results/layer2_qqq_v2_completion_tuned_v1_2023_2024/layer2_v2_completion_tuned_v1_summary.md`** (**`TUNE_COMPLETION_GRIDS_AGAIN`**). **Layer 2 v2 completion tuned v2 high-trade:** configs `layer2_qqq_v2_completion_tuned_v2_high_trade_2023_2024.yaml` + `layer2_sweep_qqq_v2_completion_tuned_v2_high_trade_2023_2024.yaml`; curated **`src/combiner/results/layer2_qqq_v2_completion_tuned_v2_high_trade_2023_2024/layer2_v2_completion_tuned_v2_high_trade_summary.md`** (**`TUNE_COMPLETION_GRIDS_AGAIN`**; **`behavior_unique` = 2**; high-trade **0.02** issue documented). mini-WFO v4/v5 + full WFO **not** run. Design / run plan: `reduced_layer2_v2_completion_design.md`, `reduced_layer2_v2_completion_run_plan.md`; tuning plan / toxic-path diagnosis: `layer2_v2_completion_tuning_plan.md`, `layer2_v2_completion_toxic_path_diagnosis.md`; tuned v2 plan: `layer2_v2_completion_tuned_v2_high_trade_plan.md`.

**Generic risk hygiene (`risk.min_risk_per_share`)**

Optional YAML under `risk`: **`min_risk_per_share`**. If set **> 0**, Layer 1 preview signals with **`sig_risk_per_share` below the threshold are invalidated** (pandas path + fast arrays). This avoids microscopic dollar-at-risk trades where fixed **slippage_per_share** dominates R-multiples — **not** VWAP-specific. The Layer 2 combiner also refuses an entry when **actual** entry-to-stop risk is below the candidate’s threshold (**rejection reason `risk_too_small`**). Missing / **0** disables the filter.

**Current supported instruments**

- Equity ETFs: SPY, QQQ (sample data paths in layout below).
- Futures raw layout may exist, but the documented workflow here emphasizes **equity** 1-min bars.

**Important limitations**

- `sweep.py` is dynamic at the strategy **interface** level, but a strategy must set **`supports_fast = True`** and implement the fast array contract (typically **`generate_signal_arrays`** delegating to **`prepare_signal_context`** + **`generate_signal_arrays_from_context`**) to be sweepable.
- New strategies are registered in **`loader.py`** (`_STRATEGY_BY_NAME` → **`available_strategies()`** / **`load_strategy()`**).

### Strategy config and context-cache validation

- Every strategy plugin may implement **`validate_config(config)`** (optional hook on `BaseStrategy`); invalid combos fail early in the readable backtest, Layer 1 sweep, Layer 2 precompute, parity checks, and `run_layer1_focused` grid preflight.
- Shared rules live in **`src/utils/config_validation.py`** (`validate_common_strategy_config`, `validate_common_combiner_config`, etc.).
- **`context_key(config)`** must include any parameter that changes arrays built in **`prepare_signal_context`** (so sweep/combiner context caches stay correct). **`normalized_param_key(config)`** should include parameters that change final signals or gating; unsupported or ignored YAML axes are removed or rejected (no fake grid uniqueness). Price-action (`pa_*`) strategies follow the same rule after the cache-scope pass documented under **`src/research/results/pa_context_key_cache_scope_audit.md`**.
- Several plugins are **long-only (or single-level) MVPs**; mis-specified `side` / `level_type` / unused keys (e.g. former `features.midday_window` on `afternoon_continuation`) are rejected with clear errors.

## 1. Architecture overview

```
data/raw parquet
  -> src/data/read_bars.py
  -> src/features/build_features.py
  -> src/strategies/strategy/<strategy>.py
  -> src/backtest/engine.py      (readable / debug single run)
  -> src/backtest/sweep.py       (Numba fast parameter sweep)
  -> src/strategies/testing_parameters_results/<strategy>/...
```

### Data layer

- `src/data/pull_ibkr_1min.py` — fetch bars into Parquet.
- `src/data/read_bars.py` — read bars into a DataFrame.
- **Raw parquet is never modified** by features, strategies, or backtests.

### Feature layer

- `src/features/build_features.py` — builds reusable **market-state** columns in memory (time/session, VWAP, ORB, levels, volatility).
- Feature code is **strategy-agnostic**; strategies declare what they need via `required_features()`.
- **No-lookahead conventions (Commit B hardening):**
  - Full-session aggregates are explicitly named **`full_session_*_LOOKAHEAD`** and must **not** be used by intraday strategies.
  - Intraday-safe cumulative anchors are available as **`intraday_high_so_far`** / **`intraday_low_so_far`**.
  - ORB broadcast anchors are safe only when gated by `after_orb`; prefer **`orb_*_known`** columns (NaN/False before ORB completion).
  - Feature cache keys are centralized in `src/features/feature_key.py` (`FeatureBuildConfig` + `feature_key_from_config`).

### Strategy layer

- `src/strategies/strategy/` — one plugin per strategy, subclassing `BaseStrategy`.
- **Readable path:** `generate_signals(df, config)` → standard signal **DataFrame** columns (pandas, correctness / debugging).
- **Fast research path:** immutable **context** built once per feature slice (and per `context_key(config)` when needed), then **`generate_signal_arrays_from_context(ctx, config)`** → NumPy / Numba arrays, then generic Numba execution in **`fast.py`**.
- **`generate_signal_arrays(df, config)`** remains the compatibility entry point; fast strategies usually implement **`prepare_signal_context`**, **`generate_signal_arrays_from_context`**, optional **`context_key`** (cache partitioning) and **`normalized_param_key`** (sweep duplicate suppression).
- Shared session / rolling / thinning helpers for signal math live in **`src/strategies/strategy/fast_utils.py`** (not in **`backtest/fast.py`**).
- Serious sweeps use **`prepare_signal_context`** → Numba **`generate_signal_arrays_from_context`** (tier **`A_true_context_fast_core`**). Legacy pandas adapter code was removed from the repo after migration.
- Fast-capable strategies set **`supports_fast = True`** and implement the fast array dict contract (see [Standard signal schema](#7-standard-signal-schema)).

**Layer 1 focused sweep bundle (all registered strategies, saved results):**

```bash
python src/research/run_layer1_focused.py --asset equity --symbols QQQ --start 2023-01-01 --end 2026-04-30 --strategies all --tag layer1_qqq_posthardening_2023 --output-root src/research/results/layer1_all10_qqq_2023_20260430_posthardening_v1 --top 50 --min-trades 30 --progress-every 50 --resume
```

Then select candidates from **`sweep_manifest.csv`**:

```bash
python src/research/select_candidates.py --manifest src/research/results/layer1_all10_qqq_2023_20260430_posthardening_v1/sweep_manifest.csv --output-root src/research/results/layer1_all10_qqq_2023_20260430_posthardening_v1 --top-per-strategy 5 --min-trades 50 --min-profit-factor 1.05 --min-total-r 0 --max-drawdown-r -40 --max-avg-bars-held 90 --max-eod-count 0 --max-end-of-data-count 0 --allow-relaxed-fallback
```

**Readable vs fast array parity (QQQ Jan sample):**

```bash
python src/research/check_strategy_fast_parity.py --strategy failed_orb --asset equity --symbol QQQ --start 2025-01-01 --end 2025-01-31 --testing-config src/strategies/testing_parameters/failed_orb_focused.yaml --max-combos 10
```

Repeat with each strategy’s **`*_focused.yaml`**. Pass **`--orb-open-minutes`** when it must match feature construction (same as sweep defaults).

### Backtest layer

- **`engine.py`** — readable / debug: full `trades` / `equity`, slower, best for inspection.
- **`fast.py`** — generic Numba execution and metrics; **no** strategy-specific signal math.
- **`metrics.py`** — shared metric helpers.

### Sweep / results layer

- **`sweep.py`** reads YAML grids and runs many parameter combinations.
- Per symbol it caches **feature DataFrames**, **`prepare_backtest_arrays`** outputs, and **strategy signal contexts** keyed by `(feature_key, strategy.context_key(cfg))`.
- Before each backtest it skips grid rows whose **`normalized_param_key(cfg)`** was already seen for that symbol (redundant axes such as irrelevant slope modes when the slope filter is off), counting **`combinations_skipped_duplicate`**.
- **`results.csv`** includes **all flattened YAML parameters** under dotted keys (`signal.extension_band`, `risk.swing_lookback`, …) plus sweep metadata and metric columns; **`params_json`** is the sorted JSON snapshot of those params.
- Optional **`--testing-config PATH`** loads a grid YAML. If omitted, **`load_testing_config(<strategy>)`** uses **`testing_parameters/<strategy>.yaml`** when present, otherwise **`testing_parameters/<strategy>_focused.yaml`**. The file’s **`strategy:`** field must match **`--strategy`**. Optional **`--tag`** appends a sanitized suffix to the result folder name (**`sweep_<timestamp>_<tag>`**).
- Optional **display-only** filters narrow the printed top table and **`summary.txt`** ( **`results.csv`** stays complete): **`--max-avg-bars-held`**, **`--max-eod-count`**, **`--max-end-of-data-count`**, **`--min-profit-factor`**, **`--min-total-r`**, **`--max-drawdown-r`**. **`--min-trades`** still applies first.
- Console output and **`summary.txt`** “top” sections use a **narrow display column set** (metrics + common param keys when present) so wide grids stay readable.
- Outputs go to **`src/strategies/testing_parameters_results/<strategy>/sweep_<timestamp>/`** or **`sweep_<timestamp>_<tag>/`** (`results.csv`, `summary.txt`, `base_config.yaml`, `testing_config.yaml`).
- **Focused** grids are **`testing_parameters/<strategy>_focused.yaml`**. Prefer **`--testing-config`** with an explicit focused YAML for reproducible Layer 1 runs.

## 2. Folder layout

```
QT/
  data/
    raw/
      ibkr/
        equity/bars_1min/symbol=SPY/year=YYYY/month=MM/data.parquet
        futures/bars_1min/root=.../contract=.../year=.../month=.../data.parquet
  src/
    data/
    features/
    strategies/
      strategy/                 # Python strategy plugins
      parameters/               # default one-run YAML per strategy
      testing_parameters/     # sweep grid YAML per strategy
      testing_parameters_results/   # timestamped sweep outputs
      loader.py
    backtest/
      engine.py
      fast.py
      sweep.py
      metrics.py
  README.md
  requirements.txt
```

- **`parameters/`** — default config for a single detailed run (readable engine or smoke tests).
- **`testing_parameters/`** — Cartesian grid + `fixed` overrides for sweeps.
- **`testing_parameters_results/`** — archived `results.csv`, `summary.txt`, and copied YAMLs per sweep run.
- **`strategy/`** — strategy implementations only (signal logic lives here, not in `fast.py`).

## 3. Install and environment

Use **system Python**; a venv is optional, not required for this repo.

```bash
pip install -r requirements.txt
```

- **IB Gateway / TWS** is only needed when **pulling** fresh data into Parquet. Reading bars, building features, running the engine, and running sweeps on **existing** Parquet do **not** require a live IBKR connection.
- Default **paper** API port for pull scripts is **4002** (override via CLI where supported).

## 4. Data workflow

**When to pull:** raw Parquet is missing or needs updating for a symbol/date range.

**When not to pull:** backtests and sweeps only read existing Parquet; no IBKR session required.

- Equities pulled with **`--rth`** are stored as **regular trading hours** bars.
- Futures at the raw layer are **explicit quarterly contracts**, not continuous futures.

Pull SPY and QQQ (example):

```bash
python src/data/pull_ibkr_1min.py --asset equity --symbols SPY QQQ --start 2025-01-01 --end 2026-04-30 --rth --chunk-days 5 --sleep 1.0 --client-id 101
```

Long history (e.g. main research window **2020-01-01 → 2026-04-30**) uses the same CLI; writes **monthly** `data.parquet` incrementally. If IB disconnects, restart Gateway and rerun the same command (months are **merge + dedupe**). After a large pull, summarize coverage:

```bash
python src/research/equity_data_coverage_report.py --symbols SPY QQQ --start 2020-01-01 --end 2026-04-30 --output-dir src/research/results/data_backfill_spy_qqq_2020_20260430
```

Read SPY, January 2025:

```bash
python src/data/read_bars.py --asset equity --symbol SPY --start 2025-01-01 --end 2025-01-31
```

## 5. Feature workflow

- Features are computed **in memory**; raw Parquet is **not** enriched or overwritten.
- Strategy plugins list required columns in **`required_features()`**.
- If a new strategy needs new market-state columns, add them in **`src/features/`** first, then declare them in **`required_features()`**.

```bash
python src/features/build_features.py --asset equity --symbol SPY --start 2025-01-01 --end 2025-01-31 --orb-open-minutes 15
```

## 6. Strategy plugin workflow

Standard steps to add a **new** strategy (example placeholder: **`intraday_breakout`**):

1. **Create** `src/strategies/strategy/intraday_breakout.py`.
2. **Implement** `class IntradayBreakoutStrategy(BaseStrategy)`:
   - `name = "intraday_breakout"`
   - `supports_fast = True` **or** `False` (sweep requires `True` + fast array contract)
   - `required_features(self) -> list[str]`
   - `generate_signals(self, df, config)` — readable / debug DataFrame with standard signal columns
   - Optional fast-path hooks (see `BaseStrategy` defaults): **`prepare_signal_context`**, **`context_key`**, **`generate_signal_arrays_from_context`**, **`normalized_param_key`**
   - `generate_signal_arrays(self, df, config)` — if `supports_fast`, return the fast array dict (usually `prepare` → `from_context`; see [Standard signal schema](#7-standard-signal-schema))
3. **Create** `src/strategies/parameters/intraday_breakout.yaml` (default run config).
4. **Create** `src/strategies/testing_parameters/intraday_breakout.yaml` (sweep grid).
5. **Register** in `src/strategies/loader.py` (`available_strategies`, `load_strategy`).
6. **Smoke test** (add a `main` or CLI block similar to existing strategies):  
   `python src/strategies/strategy/intraday_breakout.py ...`
7. **Readable backtest:**  
   `python src/backtest/engine.py --strategy intraday_breakout ...`
8. **Fast sweep** (only if `supports_fast=True`):  
   `python src/backtest/sweep.py --strategy intraday_breakout ...`

**Live examples in this repo:** `orb_continuation`, `vwap_reversal` (see §11–§13 for commands).

**Guidelines**

- **`generate_signals`** — correctness, debugging, and detailed trades via `engine.py`.
- **`prepare_signal_context` / `generate_signal_arrays_from_context`** — optimized sweeps: invariant NumPy work once per cached context, cheap per combo.
- **`generate_signal_arrays`** — compatibility wrapper used by tests and callers; `sweep.py` prefers **`from_context`** with a cached context.
- If **`supports_fast=False`**, `sweep.py` exits with a clear error; use `engine.py` until a fast path exists.
- **Do not** add strategy-specific logic to `sweep.py`.
- **Do not** add strategy-specific execution or signal rules to `backtest/fast.py`.
- **Do** keep all strategy-specific signal math inside the strategy plugin.

Loader utilities:

```bash
python src/strategies/loader.py --strategy orb_continuation --show-config

python src/strategies/loader.py --strategy orb_continuation --show-testing-grid
```

## 7. Standard signal schema

### Readable signal DataFrame (`generate_signals`)

The readable engine consumes these columns; it does **not** depend on ORB-specific field names beyond what the strategy writes into the standard schema.

| Column | Role |
|--------|------|
| `sig_strategy` | Strategy name |
| `sig_side` | `1` long, `-1` short, `0` flat |
| `sig_entry_ref` | Reference price on the signal bar (not necessarily the fill) |
| `sig_stop` | Stop price |
| `sig_target` | Preview level for `fixed_r`, or explicit target for `fixed_price` |
| `sig_target_mode` | e.g. `fixed_r`, `fixed_price` |
| `sig_target_r` | R multiple when mode is `fixed_r` |
| `sig_risk_per_share` | Risk per share at signal bar |
| `sig_reason` | Short tag for debugging |
| `sig_valid` | If true, row is treated as an executable signal |

**Execution note:** the engine fills at **next bar open**; `sig_entry_ref` is the signal-bar reference, not the fill price.

### Fast signal arrays (`generate_signal_arrays`)

| Key | Role |
|-----|------|
| `side` | int8, `1` / `-1` / `0` |
| `valid` | bool, executable signal |
| `stop` | float64 stop |
| `target_preview` | float64 (preview or explicit per `target_mode_code`) |
| `target_mode_code` | int8; use `TM_NONE`, `TM_FIXED_R`, `TM_FIXED_PX` from `src/backtest/fast.py` |
| `target_r` | float64, used for fixed-R mode |
| `risk_preview` | float64 risk-per-share preview at signal bar |

**`run_fast_backtest_from_arrays`** performs execution and metrics from these arrays; it stays strategy-agnostic.

## 8. Risk / target schema

- **`risk.stop_mode`** — strategy-defined anchor (e.g. ORB `orb_mid` / `orb_opposite`; other strategies may define their own modes in YAML + code).
- **`risk.stop_buffer`** — shifts the stop away from the anchor (long: stop lower; short: stop higher).
- **`risk.target_mode`**
  - **`fixed_r`:** target from entry ± **R × actual risk** (risk = \|entry − stop\| after fill rules).
  - **`fixed_price`:** target is the explicit price in **`sig_target`** / array equivalent.
- **`risk.target_r`** — used when `target_mode` is `fixed_r`.
- **`sig_target`** — preview at signal bar for `fixed_r`; actual target level for `fixed_price`.
- **`backtest.recompute_target_from_entry: true`** — for `fixed_r`, recompute target from **actual** next-bar entry and **actual** risk so the target matches real execution (signal at bar close, entry at next open).

### Max holding time (`backtest.max_hold_minutes`)

- **`null`** or omitted — no maximum hold; exits follow stop, target, EOD, or end-of-session/data only.
- **Positive integer** — after entry at the **next bar open**, count **1-minute bars in position**; on each bar, **intrabar stop and target are evaluated first**; if neither hits and bars held ≥ the limit, exit at that bar’s **close** with exit reason **`max_hold`**. Then existing EOD / end-of-data logic applies when still open.
- CLI override: **`python src/backtest/engine.py ... --max-hold-minutes N`** (optional; omits override when not passed).
- Metrics include **`max_hold_count`** (readable engine and fast path). Use this to favor **short/medium intraday** holds instead of results that depend on **holding to EOD**.

**Future-friendly examples (not all implemented as separate strategies yet):**

- ORB: stop anchored at `orb_mid` / `orb_opposite`.
- VWAP reversion: `fixed_price` target at VWAP.
- Breakouts: `fixed_r` or targets at prior high/low.

**Out of scope for now:** partial profit-taking, trailing stops, and similar exit rules are intentionally not implemented.

## 9. Single detailed backtest workflow

Use **`src/backtest/engine.py`** when you need:

- One parameter set, step-by-step debugging
- Full **`trades`** and **`equity`** DataFrames
- Export of **`trades.csv`**, **`equity.csv`**, **`metrics.json`**, **`config_used.yaml`** (with **`--out-dir`**)
- Comparing or validating signal logic against the fast path (manually or via dev tests)

QQQ, January 2025 (default YAML-driven config):

```bash
python src/backtest/engine.py --strategy orb_continuation --asset equity --symbol QQQ --start 2025-01-01 --end 2025-01-31
```

With CLI overrides:

```bash
python src/backtest/engine.py --strategy orb_continuation --asset equity --symbol QQQ --start 2025-01-01 --end 2025-01-31 --orb-open-minutes 15 --side both --daily-signal-mode first_signal --stop-mode orb_mid --target-r 2.0
```

Optional artifact directory:

```bash
python src/backtest/engine.py --strategy orb_continuation --asset equity --symbol QQQ --start 2025-01-01 --end 2025-01-31 --out-dir out/run1
```

To reproduce one grid point from a sweep, mirror the same overrides (or a small YAML) in `engine.py`; the sweep does not emit per-combo trade ledgers.

## 10. Fast parameter sweep workflow

**`sweep.py` always** uses the Numba fast path (no alternate engine or compare-first CLI switches). Each combo runs:

`load_strategy` → **`strategy.prepare_signal_context`** (cached) → **`strategy.generate_signal_arrays_from_context`** → **`run_fast_backtest_from_arrays`**

Output is **metrics per combination** (e.g. `results.csv`), not full trade logs for every grid point.

Small smoke (no result folder):

```bash
python src/backtest/sweep.py --strategy orb_continuation --asset equity --symbols QQQ --start 2025-01-01 --end 2025-01-31 --top 10 --min-trades 1 --no-save --profile --max-combos 10
```

Full QQQ ORB example (writes a timestamped folder under `testing_parameters_results/orb_continuation/`):

```bash
python src/backtest/sweep.py --strategy orb_continuation --asset equity --symbols QQQ --start 2025-01-01 --end 2026-04-30 --top 30 --min-trades 30 --profile
```

Full QQQ VWAP reversal grid (**same**: omit `--no-save` to persist results under `testing_parameters_results/vwap_reversal/`):

```bash
python src/backtest/sweep.py --strategy vwap_reversal --asset equity --symbols QQQ --start 2025-01-01 --end 2026-04-30 --top 30 --min-trades 30 --profile
```

**Focused QQQ grids** (execution-style: explicit **`max_hold_minutes`**, display filters that down-weight EOD-heavy rows). These are **research families**, not live-ready systems.

```bash
python src/backtest/sweep.py --strategy orb_continuation --testing-config src/strategies/testing_parameters/orb_continuation_focused.yaml --asset equity --symbols QQQ --start 2025-01-01 --end 2026-04-30 --top 30 --min-trades 100 --max-avg-bars-held 60 --max-eod-count 0 --profile --tag focused_orb_qqq
```

```bash
python src/backtest/sweep.py --strategy vwap_reversal --testing-config src/strategies/testing_parameters/vwap_reversal_focused.yaml --asset equity --symbols QQQ --start 2025-01-01 --end 2026-04-30 --top 30 --min-trades 100 --max-avg-bars-held 90 --max-eod-count 0 --profile --tag focused_vwap_qqq
```

**Interpretation:** ORB focused ≈ **early momentum continuation** after the opening range; VWAP focused ≈ **post-open mean reversion / bounce** toward VWAP. Compare to broad-grid winners only directionally — **`max_hold_minutes`** and filters change rankings.

SPY and QQQ:

```bash
python src/backtest/sweep.py --strategy orb_continuation --asset equity --symbols SPY QQQ --start 2025-01-01 --end 2026-04-30 --top 30 --min-trades 30 --profile
```

**Result folder layout** (when not using `--no-save`):

```
src/strategies/testing_parameters_results/<strategy>/sweep_<timestamp>[_<tag>]/
  results.csv          # all flattened config keys + metrics
  summary.txt          # metadata + top rows (display columns only)
  base_config.yaml
  testing_config.yaml
```

### Layer 1 → Layer 2 workflow

1. **Layer 1 sweeps** produce raw **`results.csv`** (many parameter rows per strategy).
2. **`src/research/select_candidates.py`** filters and ranks rows, then writes **`selected_candidates.csv`** plus one YAML per candidate under **`selected_candidates/`** (nested **`config:`** is the full strategy parameter set for that row; no hardcoded ORB/VWAP params in the selector).
3. **`src/combiner/run.py`** loads those YAMLs, applies **combiner-only** rules from **`src/combiner/configs/*.yaml`** (priorities, active windows, daily limits, execution costs), builds aligned fast signal arrays per candidate, and runs the **MVP simulator** (one open position, priority tie-break, rejected-signal logging).
4. Strategy **parameters** always come from candidate YAMLs; combiner YAML controls **routing and portfolio-level risk only**.

**Layer 2 Combiner (post-hardening all-10 example):** candidate YAMLs from **`src/research/results/layer1_all10_qqq_2023_20260430_posthardening_v1/selected_candidates/`**; configs **`src/combiner/configs/layer2_qqq_2023_20260430_posthardening_strict.yaml`** + **`layer2_sweep_qqq_2023_20260430_posthardening_strict.yaml`**; output root **`src/combiner/results/layer2_qqq_2023_20260430_posthardening_strict_v1/`**. Legacy `layer2_qqq_v1` / `layer1_all10_qqq_v1` **result folders were removed** (`repo_cleanup_summary.md`).

```bash
python src/combiner/run.py --candidate-root src/research/results/layer1_all10_qqq_2023_20260430_posthardening_v1/selected_candidates --config src/combiner/configs/layer2_qqq_2023_20260430_posthardening_strict.yaml --asset equity --symbol QQQ --start 2023-01-01 --end 2026-04-30 --diagnostics-only --candidate-set all_with_relaxed --top-per-strategy 5 --output-root src/combiner/results/layer2_qqq_2023_20260430_posthardening_strict_v1

python src/combiner/run.py --candidate-root src/research/results/layer1_all10_qqq_2023_20260430_posthardening_v1/selected_candidates --config src/combiner/configs/layer2_qqq_2023_20260430_posthardening_strict.yaml --asset equity --symbol QQQ --start 2023-01-01 --end 2026-04-30 --candidate-set strict_core --top-per-strategy 3 --tag strict_core_top3 --detailed --output-root src/combiner/results/layer2_qqq_2023_20260430_posthardening_strict_v1

python src/combiner/sweep.py --candidate-root src/research/results/layer1_all10_qqq_2023_20260430_posthardening_v1/selected_candidates --config src/combiner/configs/layer2_sweep_qqq_2023_20260430_posthardening_strict.yaml --asset equity --symbol QQQ --start 2023-01-01 --end 2026-04-30 --output-root src/combiner/results/layer2_qqq_2023_20260430_posthardening_strict_v1 --top 20 --detail-top 10 --progress-every 100 --tag sweep_posthardening
```

**Postprocess** (diagnostics markdown, sweep dedupe, fixed-run rollup, cost stress):

```bash
python src/combiner/postprocess.py --diagnostics-dir src/combiner/results/layer2_qqq_2023_20260430_posthardening_strict_v1/diagnostics --diagnostics-date-range "2023-01-01 — 2026-04-30" --output-root src/combiner/results/layer2_qqq_2023_20260430_posthardening_strict_v1

python src/combiner/postprocess.py --sweep-dir src/combiner/results/layer2_qqq_2023_20260430_posthardening_strict_v1/sweep_<timestamp>_sweep_posthardening --output-root src/combiner/results/layer2_qqq_2023_20260430_posthardening_strict_v1 --dedupe-top 50

python src/combiner/postprocess.py --sweep-dir src/combiner/results/layer2_qqq_2023_20260430_posthardening_strict_v1/sweep_<timestamp>_sweep_posthardening --output-root src/combiner/results/layer2_qqq_2023_20260430_posthardening_strict_v1 --dedupe-top 50 --cost-stress-top 5 --candidate-root src/research/results/layer1_all10_qqq_2023_20260430_posthardening_v1/selected_candidates --config src/combiner/configs/layer2_qqq_2023_20260430_posthardening_strict.yaml --asset equity --symbol QQQ --start 2023-01-01 --end 2026-04-30

python src/combiner/postprocess.py --collect-fixed-runs src/combiner/results/layer2_qqq_2023_20260430_posthardening_strict_v1/fixed_runs --output-root src/combiner/results/layer2_qqq_2023_20260430_posthardening_strict_v1
```

#### Layer 2 postprocess diagnostics (hardened)

- **Config-level dedupe** (`top_unique_systems.csv`): one row per distinct combiner **grid + candidate list** (same as sweep dedupe key).
- **Behavior-level dedupe** (`behavior_unique_systems.csv`): hashes the **actual trade sequence** from detailed `trades.csv` (`behavior_hash_from_trades` in `src/combiner/behavior.py`). Strong hashes prefer `candidate_id` / `entry_idx` / `exit_idx`; weak hashes fall back when columns are missing (called out in the markdown summary).
- **Cost-as-R**: `summarize_trades` / combiner metrics accept execution **slippage**, **commission**, and representative **quantity**; reports `avg_cost_r`, `median_cost_r`, etc.
- **R-multiple distribution**: `profit_factor_r` (gross R wins / gross R losses), quantiles, daily aggregates, and **`daily_trade_number`** JSON breakdowns on combiner runs.
- **Period breakdowns** (detailed folders only): `--write-period-breakdowns` writes `monthly_r.csv`, `quarterly_r.csv`, and optional `strategy_by_month.csv` / `candidate_by_month.csv` under each `top_runs/rank_*` or fixed `run_*` folder (not for every sweep row by default).
- **Leaderboards**: `rank_by_*.csv` (combiner score, total R, PF, PF_R, R/|DD|, cost-sorted ranks with `--min-trades-cost-rank`, and `rank_by_cost_0_02_total_r.csv` when cost stress exists).
- **Cost-robust filter**: `cost_robust_systems.csv` + `.md` with CLI thresholds (`--cost-robust-*`); research filters only.
- **Fixed vs sweep**: `--compare-fixed-runs path/to/fixed_run_summary.csv` (with `--sweep-dir`) emits `fixed_vs_sweep_comparison.*`.

Saved Layer 1/Layer 2 **result folders from before these diagnostics are still stale** until you rerun sweeps with the hardened code; use postprocess outputs only on **fresh** sweep exports.

Artifacts default under **`src/combiner/results/layer2_qqq_2023_20260430_posthardening_strict_v1/`** (`run_<timestamp>_<tag>/`, `diagnostics/`, `sweep_<timestamp>_<tag>/`).

**MVP combiner behavior (legacy ORB+VWAP sample `orb_vwap_simple.yaml`):** one symbol, **max one** open position, session/day caps from YAML, **`no_new_after_minute`**, **`slippage_per_share: 0.01`**, **`commission_per_trade: 0.0`**. Priorities in that sample favor ORB over VWAP when both fire.

**Candidate selection** (latest focused sweep CSVs via glob):

```bash
python src/research/select_candidates.py \
  --result "orb_continuation=src/strategies/testing_parameters_results/orb_continuation/sweep_*focused_orb_qqq/results.csv" \
  --result "vwap_reversal=src/strategies/testing_parameters_results/vwap_reversal/sweep_*focused_vwap_qqq/results.csv" \
  --top-k 3 \
  --min-trades 100 \
  --min-profit-factor 1.2 \
  --max-eod-count 0 \
  --max-end-of-data-count 0 \
  --max-avg-bars-held 90 \
  --out-dir src/research/results/layer1_orb_vwap_qqq \
  --tag layer1_orb_vwap_qqq
```

**Combiner runs** (same candidate library; `--strategies` picks the subsystem):

```bash
python src/combiner/run.py --candidate-root src/research/results/layer1_orb_vwap_qqq/selected_candidates --config src/combiner/configs/orb_vwap_simple.yaml --asset equity --symbol QQQ --start 2025-01-01 --end 2026-04-30 --top-per-strategy 1 --strategies orb_continuation --tag orb_only_top1

python src/combiner/run.py --candidate-root src/research/results/layer1_orb_vwap_qqq/selected_candidates --config src/combiner/configs/orb_vwap_simple.yaml --asset equity --symbol QQQ --start 2025-01-01 --end 2026-04-30 --top-per-strategy 1 --strategies vwap_reversal --tag vwap_only_top1

python src/combiner/run.py --candidate-root src/research/results/layer1_orb_vwap_qqq/selected_candidates --config src/combiner/configs/orb_vwap_simple.yaml --asset equity --symbol QQQ --start 2025-01-01 --end 2026-04-30 --top-per-strategy 1 --strategies orb_continuation vwap_reversal --tag orb_vwap_top1
```

Outputs land under **`src/combiner/results/run_<timestamp>_<tag>/`** or **`layer2_qqq_2023_20260430_posthardening_strict_v1/run_<timestamp>_<tag>/`** (`trades.csv`, `equity.csv`, `metrics.json`, **`candidate_signal_log.csv`**, **`rejected_signals.csv`**, `candidates_used.csv`, `config_resolved.yaml`, `summary.txt`).

## 11. Current ORB continuation baseline

**In-sample research only — not production-ready, not validated out-of-sample.**

A recent full-sample QQQ sweep (**2025-01-01** to **2026-04-30**) had a top region roughly:

- `orb_open_minutes`: **10**
- `signal.side`: **long_only**
- `signal.entry_end_minute`: **60**
- `signal.require_vwap_side`: **true**
- `signal.require_vwap_slope`: **false**
- `risk.stop_mode`: **orb_mid**
- `risk.target_mode`: **fixed_r**
- `risk.target_r`: **2.0**
- **Trades:** ~**204**
- **Profit factor:** ~**1.36**
- **Total R:** ~**42**
- **Max drawdown (R):** ~**−12**

Use this only as a **baseline** for further research (OOS tests, robustness, costs, etc.).

### VWAP reversal (`vwap_reversal`)

**Research / mean-reversion only — not a production strategy, not validated OOS.**

`vwap_reversal` fades **overextensions** beyond session VWAP bands (1σ or 2σ, from existing `vwap_upper_1.0` / `vwap_lower_1.0` / `*_2.0` columns) back toward **VWAP** (`fixed_price`) or a **fixed-R** target. It uses band touch / reclaim-style **confirmations** and optional **VWAP slope** filters. Treat it as a different hypothesis class from **ORB continuation** (trend/continuation). Do not assume profitability from in-sample metrics.

Default parameters: `parameters/vwap_reversal.yaml`. For sweeps, use **`--testing-config src/strategies/testing_parameters/vwap_reversal_focused.yaml`** (or the default loader fallback to `*_focused.yaml` when no broad `testing_parameters/<strategy>.yaml` exists). Use `--max-combos` to cap iteration on large grids.

## 12. Development rules / guardrails

- **Do not** modify raw Parquet from feature, strategy, or backtest code.
- **Do not** add strategy-specific signal logic to **`backtest/fast.py`** (keep it execution-only).
- **Do not** add strategy-specific **`if strategy == …`** branches in **`sweep.py`**; use **`BaseStrategy`** hooks (`prepare_signal_context`, `normalized_param_key`, …) and dynamic config flattening for results.
- **Do not** hardcode strategy names in **`sweep.py`** beyond loading the plugin by CLI `--strategy` (default flag value is OK).
- **Do not** add live trading code at this stage of the repo.
- Keep **readable** (`engine.py`) and **fast research** (`fast.py` + `sweep.py`) paths clearly separated.
- Prefer **YAML** for defaults and sweep grids.
- Add new **feature** columns in **`src/features`** before strategies depend on them.
- Add new **strategies** as plugins, not as large `if/else` branches in sweep or fast code.
- For each new active strategy, ship: implementation file, **`parameters/*.yaml`**, **`testing_parameters/*.yaml`**, **`loader.py`** mapping, and (once real) a **smoke command** documented here.

## 13. Common commands quick reference

**Install**

```bash
pip install -r requirements.txt
```

**Read data**

```bash
python src/data/read_bars.py --asset equity --symbol SPY --start 2025-01-01 --end 2025-01-31
```

**Feature smoke**

```bash
python src/features/build_features.py --asset equity --symbol SPY --start 2025-01-01 --end 2025-01-31 --orb-open-minutes 15
```

**Loader**

```bash
python src/strategies/loader.py --strategy orb_continuation --show-config
python src/strategies/loader.py --strategy orb_continuation --show-testing-grid
```

**Strategy smoke (ORB)**

```bash
python src/strategies/strategy/orb_continuation.py --asset equity --symbol SPY --start 2025-01-01 --end 2025-01-31
```

**Strategy smoke (VWAP reversal)**

```bash
python src/strategies/strategy/vwap_reversal.py --asset equity --symbol QQQ --start 2025-01-01 --end 2025-01-31
```

**Readable backtest**

```bash
python src/backtest/engine.py --strategy orb_continuation --asset equity --symbol QQQ --start 2025-01-01 --end 2025-01-31
python src/backtest/engine.py --strategy vwap_reversal --asset equity --symbol QQQ --start 2025-01-01 --end 2025-01-31
```

**Fast sweep**

```bash
python src/backtest/sweep.py --strategy orb_continuation --asset equity --symbols QQQ --start 2025-01-01 --end 2026-04-30 --top 30 --min-trades 30 --profile
python src/backtest/sweep.py --strategy vwap_reversal --asset equity --symbols QQQ --start 2025-01-01 --end 2025-01-31 --top 10 --min-trades 1 --no-save --profile --max-combos 30
python src/backtest/sweep.py --strategy vwap_reversal --asset equity --symbols QQQ --start 2025-01-01 --end 2026-04-30 --top 30 --min-trades 30 --profile
```

The full-range VWAP command above **saves** outputs (no `--no-save`). Use `--no-save` only for quick smoke runs.

## 14. Next planned extension

**Next possible extensions:** failed opening-range plays, intraday / prior-day breakout templates, cost and slippage robustness passes, walk-forward tooling (not implemented here yet).

New strategies should follow §6 using fresh plugin names, YAMLs, and `loader.py` registration.

---

*Fast vs readable equivalence checks belong in dev-only tests or ad-hoc scripts, not in the sweep CLI.*
