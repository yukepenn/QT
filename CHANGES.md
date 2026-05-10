### [Unreleased] – 2026-05-10

- Fix(core): PA **`pa_swings`** session-scoped prior bar for `close_back_inside`; **normalized_param_key** on PA strategies includes entry window / risk thinning fields + **MTR `wedge_push_min`** + TCP climax keys; **`combiner/simulator.py`** legacy path uses **`validate_trade_setup`**; docs **`pa_normalized_param_key_audit.md`**, **`pa_structural_target_semantics.md`**; tests (`test_pa_swings_session_boundary`, `test_strategy_normalized_param_keys`, `test_combiner_detailed_validation_parity`, `test_pa_structural_targets`).
- Feat(research): **PA Batch B/C diagnostics v1** — `pa_gate_diagnostics.py`, `pa_exit_diagnostics.py`; curated **`pa_batch_bc_gate_diagnostics_v1/`**, **`pa_batch_bc_exit_diagnostics_v1/`** (CSV/MD); **`p0_correctness_cleanup_summary.md`**; tests `test_pa_gate_diagnostics.py`, `test_pa_exit_diagnostics.py`; indexes **`RESULTS_INDEX.md`**, **`ARTIFACT_POLICY.md`**.
- Style(core): **Black** formatting for loader/features/backtest/combiner/walkforward/`select_candidates`/PA strategies; `.gitignore` comment sections only; docs `format_core_modules_for_maintainability.md`, `p0_correctness_cleanup_plan.md`.
- Chore(walkforward): commit curated mini-WFO **train** exports — `layer3_mini_wfo_qqq_*_v1` (candidates + `train_layer2_top_unique_systems.*`); `layer3_mini_wfo_v2a_*` / `v2b_*` (candidates + selected YAMLs + train Layer2 configs); `layer3_mini_wfo_v3_refined_gap_failed_*` (train Layer2 configs). Layer 2 **precompute dumps** (`candidate_precompute_profile.csv`, `feature_store_stats.json`) remain local per `ARTIFACT_POLICY.md`.
- Feat(research): **PA Batch B+C tuned Layer 1 v1 (QQQ 2023–2024)** — tuned grids `pa_*_tuned_v1.yaml`; curated `layer1_pa_batch_bc_tuned_qqq_2023_2024_v1/` (prior row diagnosis, tuned grid review, sweep manifest, tuned signal diagnosis, strict **5** YAMLs for **`pa_climax_reversal`**, fast-context check, diagnostic relaxed CSV note); summary `layer1_pa_batch_bc_tuned_v1_summary.md`. Decision **`TUNE_PA_BATCH_BC_GRIDS_AGAIN`**. **PA Batch B/C Layer 2 / mini-WFO / full WFO / live not run.**
- Feat(research): **PA Batch B+C formal Layer 1 (QQQ 2023–2024)** — curated `layer1_pa_batch_bc_qqq_2023_2024/` (manifest, signal diagnosis, strict **5** YAMLs for **`pa_buy_sell_close_trend` only**, fast-context check, diagnostic relaxed CSV note); summary `layer1_pa_batch_bc_summary.md`. Decision **`TUNE_PA_BATCH_BC_GRIDS_FIRST`**. **PA Batch B/C Layer 2 / mini-WFO / full WFO / live not run.**
- Feat(strategies): **PA Batch C** — `pa_buy_sell_close_trend`, `pa_generic_breakout_pullback` + YAMLs + tests + `pa_batch_c_*` smokes; loader **33 → 35**; docs `pa_overlap_refinements_backlog.md`, `pa_strategy_library_completion_summary.md`. **No formal Layer 1/2 / WFO.**
- Feat(strategies+features): **PA Batch B** — four plugins (`pa_broad_channel_zone`, `pa_climax_reversal`, `pa_second_entry_pullback`, `pa_wedge_reversal`) + YAMLs + focused grids; extended `regime.py` (broad channel scores, bar-range expansion, signed VWAP distance), `pa_swings.py` (`pa_higher_low_proxy_*`), `pa_batch_a_utils.py` (VWAP target + stop aliases); loader **29 → 33** strategies; tests + curated `src/research/results/pa_batch_b_*`. Jan 2025 parity + capped sweep smokes only; **no formal Layer 1/2 for Batch B yet**.
- Feat(combiner): **PA Batch A tuned v1 reduced Layer 2 (QQQ 2023–2024)** — configs `layer2_qqq_pa_batch_a_tuned_2023_2024_v1.yaml` + `layer2_sweep_qqq_pa_batch_a_tuned_2023_2024_v1.yaml` (48 combos); curated root `src/combiner/results/layer2_qqq_pa_batch_a_tuned_2023_2024_v1/` (diagnostics, fixed rollup, top/behavior dedupe, cost stress) + summary `layer2_pa_batch_a_tuned_summary.md` (**`TUNE_PA_BATCH_A_GRIDS_AGAIN`**; core fails 0.02 cost gate). **mini-WFO / full WFO not run.**
- Feat(research): **PA Batch A tuned Layer 1 v1** — `pa_*_tuned_v1.yaml` (576–768 raw), sweeps + `layer1_pa_batch_a_tuned_qqq_2023_2024_v1/` (10 strict YAMLs, 2 families; decision **`PROCEED_TO_PA_BATCH_A_REDUCED_LAYER2_DESIGN`**); `layer1_pa_batch_a_tuning_plan.md`; `reduced_layer2_pa_batch_a_tuned_design.md` (no combiner run). **Fix** `run_layer1_focused.py` — `raw_grid_size` from override testing YAML. **PA Layer 2 / mini-WFO / full WFO not run.**
- Feat(research): **PA Batch A formal Layer 1 QQQ 2023–2024** — curated `layer1_pa_batch_a_qqq_2023_2024/` (manifest, selection, diagnosis, summary; decision **`TUNE_PA_BATCH_A_GRIDS_FIRST`**). **`run_layer1_focused.py`:** richer sweep manifest + `ok_zero_trade`; **`select_candidates.py`:** treat `ok_zero_trade` like `ok` for manifest CSV paths. **PA Layer 2 / mini-WFO / full WFO not run.**
- Docs: `README.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `src/research/results/RESULTS_INDEX.md`, `src/strategies/testing_parameters/GRID_INDEX.md`, `docs/ARTIFACT_POLICY.md`.
- Feat(strategies+features): **PA Batch A foundation** — `pa_swings` + PA bar/regime/proximity features; four PA plugins (long-only MVP), YAMLs, loader **29** strategies, `metadata.yaml`; tests `test_pa_features_no_lookahead.py`, `test_pa_strategy_registration.py`, `test_pa_*_signal.py`; curated `src/research/results/pa_batch_a_*` (plan, parity/Jan smokes, implementation summary). Jan 2025 QQQ wiring + parity smokes only; **Layer 1 / Layer 2 / WFO not run.**
- Docs(research): PA Batch A — `pa_batch_a_*`, `GRID_INDEX.md` (PA section), `src/research/results/RESULTS_INDEX.md`; `README.md`, `PROJECT_STATUS.md`, `docs/ARTIFACT_POLICY.md`.
- Docs(combiner): `src/combiner/results/RESULTS_INDEX.md` — PA Batch A has no Layer 2 root yet (pointer to research summary).
- Feat(combiner): **Layer 2 v2 completion tuned v2 high-trade (QQQ 2023–2024)** — `layer2_qqq_v2_completion_tuned_v2_high_trade_2023_2024.yaml`, `layer2_sweep_qqq_v2_completion_tuned_v2_high_trade_2023_2024.yaml`; curated `src/combiner/results/layer2_qqq_v2_completion_tuned_v2_high_trade_2023_2024/` (16 fixed runs, **480-combo** sweep postprocess, `rank_high_trade_systems.*`, `high_trade_cost_review.*`). Summary `layer2_v2_completion_tuned_v2_high_trade_summary.md` (**`TUNE_COMPLETION_GRIDS_AGAIN`**). **mini-WFO v4/v5 + full WFO not run.**
- Feat(combiner): `postprocess.py` — `--min-trades-rank` / `--rank-high-trade-top` for generic **`rank_high_trade_systems`** leaderboard from `top_unique_systems.csv`.
- Feat(research): `high_trade_layer2_cost_review.py` — pivot `cost_stress_results.csv` onto high-trade `top_unique` rows.
- Test(combiner): `test_combiner_postprocess_high_trade_rank.py`.
- Docs(research): `layer2_v2_completion_tuned_v2_high_trade_plan.md`.
- Chore(gitignore): force-include tuned v2 high-trade curated Layer 2 paths.
- Docs: `README.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `CONFIG_INDEX.md`, both `RESULTS_INDEX.md`, `curated_artifact_sanity.py` (+ regenerated `curated_artifact_sanity_check.md`).
- Feat(combiner): **Layer 2 v2 completion tuned v1 (QQQ 2023–2024)** — `layer2_qqq_v2_completion_tuned_v1_2023_2024.yaml`, `layer2_sweep_qqq_v2_completion_tuned_v1_2023_2024.yaml`; curated `src/combiner/results/layer2_qqq_v2_completion_tuned_v1_2023_2024/` (diagnostics + snapshots, fixed rollup, **416-combo** sweep postprocess). Summary `layer2_v2_completion_tuned_v1_summary.md` (**`TUNE_COMPLETION_GRIDS_AGAIN`**). **mini-WFO v4/v5 + full WFO not run.**
- Docs(research): `layer2_v2_completion_tuning_plan.md`, `layer2_v2_completion_toxic_path_diagnosis.{md,csv}`.
- Chore(gitignore): force-include tuned v1 completion Layer 2 curated paths under `layer2_qqq_v2_completion_tuned_v1_2023_2024/`.
- Feat(combiner): **reduced Layer 2 v2 completion (QQQ 2023–2024)** — `layer2_qqq_v2_completion_2023_2024.yaml`, `layer2_sweep_qqq_v2_completion_2023_2024.yaml`; curated `src/combiner/results/layer2_qqq_v2_completion_2023_2024/` (diagnostics, 15 fixed runs, **756-combo** sweep `sweep_20260510_025424`, postprocess). Summary `layer2_v2_completion_summary.md` (**`TUNE_COMPLETION_GRIDS_FIRST`**). **mini-WFO v4/v5 + full WFO not run.**
- Chore(gitignore): force-include completion Layer 1 + Layer 2 curated paths (`layer1_v2_completion_qqq_2023_2024/*`, `layer2_qqq_v2_completion_2023_2024/*` summaries).
- Docs: `README.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CONFIG_INDEX.md`, both `RESULTS_INDEX.md`, `ARTIFACT_POLICY.md`, `curated_artifact_sanity.py` (+ regenerated `curated_artifact_sanity_check.md`).
- Docs(research): `repo_maintenance_formatting_summary.md`, `research_script_organization_audit.{md,csv}`, `reduced_layer2_v2_completion_run_plan.md`, `src/strategies/testing_parameters/GRID_INDEX.md`.
- Feat(research): **Layer 1 v2 completion QQQ 2023–2024** — `run_layer1_v2_completion.py`, curated root `layer1_v2_completion_qqq_2023_2024/` (manifest, **30** YAMLs, fast-context check); `check_selected_candidates_fast_context.py`.
- Fix(research): **`unflatten_config_from_row`** uses `set_nested` for nested `features.indicators.*` / `risk.*` paths so candidate YAMLs round-trip through `build_features_from_config`.
- Feat(research): manifest **`--relaxed-max-avg-bars-held`** for relaxed fallback (completion used **150** vs strict **120**).
- Test(research): `test_unflatten_config_nested_features_indicators` in `test_select_candidates_manifest.py`; `tests/test_run_layer1_v2_completion.py`.
- Docs(research): `layer1_v2_completion_summary.md`, `reduced_layer2_v2_completion_design.md` (design). Layer 2 completion economics: see **`layer2_v2_completion_summary.md`** (this release).

- Feat(strategies): **Strategy Library v2 completion** — nine new plugins (`sma20_reclaim_reject`, `macd_momentum_turn`, `stochastic_oversold_cross`, `cci_extreme_snapback`, `adx_dmi_trend_continuation`, `supertrend_atr_flip`, `large_candle_failure`, `multi_day_level_trap`, `prior_close_reclaim`) with parameters + focused YAMLs; loader **16 → 25** strategies; `metadata.yaml` entries.
- Feat(features): **SuperTrend** indicator columns (`supertrend_line_*`, `supertrend_dir_*`) + `supertrend_tuples` in `IndicatorsFeatureConfig` / `feature_key`; **multi-session lows** `prior_3day_low`, `prior_5day_low`, `previous_week_low` in `levels.py`.
- Test(strategies): `test_strategy_library_v2_completion_registration.py`, `test_strategy_library_v2_completion_features.py`, `test_levels_multiday_no_lookahead.py`; indicator test updated for SuperTrend + `atr_like_15`.
- Docs(research): `strategy_library_v2_completion_{summary,health,audit,feature_audit,repo_inventory,implementation_plan}.*` (+ CSV companions). **Layer 2 / mini-WFO v4–v5 / full WFO not run.** Superseded for economics by **`layer1_v2_completion_qqq_2023_2024/`** (2026‑05‑10).
- Feat(strategies): **Batch 1 squeeze tuned_v2** — `bollinger_squeeze_breakout_tuned_v2.yaml` (stricter bandwidth + `min_risk_per_share: 0.05`; 576-combo grid).
- Feat(research): **tuned_v1 winner diagnostics** — `gen_batch1_tuned_v1_cost_diagnostics.py`, curated `batch1_tuned_v1_cost_diagnostics/` (exit-reason / risk / entry-hour buckets).
- Feat(research): **Layer 1 slippage stress helper** — `layer1_row_slippage_eval.py` (re-sim top filtered rows at alternate `slippage_per_share`).
- Docs(research): **Batch 1 tuning v2** — `layer1_v2_batch1_tuned_v2_qqq_2023_2024/` manifest + selection docs (**0** YAML exports); `strategy_library_v2_batch1_tuning_v2_summary.md` (**`DEFER_BATCH1_AND_RETURN_TO_REFINED_FAILED_CORE`**).
- Docs(combiner): **Layer 2 tuned_v2 skipped** — `layer2_qqq_v2_batch1_tuned_v2_2023_2024/layer2_v2_batch1_tuned_v2_summary.md` (no candidate library).
- Feat(strategies): **Batch 1 tuned grids v1** — `bollinger_squeeze_breakout_tuned_v1.yaml`, `rsi_failure_swing_tuned_v1.yaml` (cost-aware strict families; `min_risk_per_share` where supported).
- Feat(research): **Batch 1 cost fragility diagnostics** — `gen_batch1_cost_fragility_diagnostics.py` + curated `batch1_cost_fragility_diagnostics_v1/` (local detailed reruns under `layer2_qqq_v2_batch1_2023_2024_diagnostics_local/`, gitignored).
- Feat(research): **Layer 1 tuned** — `layer1_v2_batch1_tuned_qqq_2023_2024_v1/` (manifest, **10** YAMLs, selection docs).
- Feat(combiner): **Batch 1 tuned Layer 2** — `layer2_qqq_v2_batch1_tuned_2023_2024_v1.yaml`, `layer2_sweep_qqq_v2_batch1_tuned_2023_2024_v1.yaml`; curated `layer2_qqq_v2_batch1_tuned_2023_2024_v1/` (diagnostics, fixed rollup, **192-combo** sweep postprocess, cost stress, behavior dedupe, cost-robust leaderboard). Summaries: `layer2_v2_batch1_tuned_summary.md`, `strategy_library_v2_batch1_tuning_summary.md`. Decision **`TUNE_BATCH1_GRIDS_AGAIN`**. **mini-WFO v4/v5 and full WFO not run.**
- Chore(gitignore): ignore `layer2_qqq_v2_batch1_2023_2024_diagnostics_local/`; local `layer2_qqq_v2_batch1_tuned_2023_2024_v1_diagnostics_local/`; force-include tuned Layer 1/2 curated paths + `batch1_tuned_v1_cost_diagnostics` + tuned_v2 manifest pack + `rank_by_*.csv` exclusion under tuned v1 root.
- Docs: README, PROJECT_STATUS, PROGRESS, `CONFIG_INDEX.md`, both `RESULTS_INDEX.md`, `ARTIFACT_POLICY.md`.
- Feat(combiner): **Batch 1 reduced Layer 2** — `layer2_qqq_v2_batch1_2023_2024.yaml`, `layer2_sweep_qqq_v2_batch1_2023_2024.yaml`; curated results `src/combiner/results/layer2_qqq_v2_batch1_2023_2024/` (diagnostics, fixed rollup, sweep dedupe, behavior dedupe, cost stress, fixed-vs-sweep). Summary `layer2_v2_batch1_summary.md`; decision **`TUNE_BATCH1_GRIDS_FIRST`**. **mini-WFO v4/v5 and full WFO not run.**
- Fix(research): remove duplicate `main()` in `gen_batch1_audit.py` (single idempotent writer for audit CSV/MD).
- Docs(research): `layer1_v2_batch1_qqq_2023_2024/MANIFEST_CONSISTENCY_NOTE.md`; expanded `reduced_layer2_v2_batch1_design.md`.
- Chore(gitignore): force-include curated `layer2_qqq_v2_batch1_2023_2024/*` summaries (heavy `run_*` / `sweep_*` / `fixed_runs/` / `top_runs/` still ignored).
- Feat(research): **Batch 1 Layer 1 complete** — six-strategy QQQ 2023–2024 sweeps + `sweep_manifest.{csv,md}` + manifest `select_candidates` → 20 YAMLs; `no_candidate_strategies.txt`, `candidate_selection_config.md`, `layer1_v2_batch1_summary.md` updates.
- Feat(features): batch column concat in `indicators.py`, `channels.py`, `regime.py` (no formula change; removes pandas fragmentation warnings).
- Feat(strategies): `donchian_channel_breakout_focused.yaml` grid retuned (≤1728 raw combos, less restrictive width / entry).
- Test(research): `tests/test_select_candidates_manifest.py` (multi-strategy manifest selection).
- Docs(research): `strategy_library_v2_batch1_audit.{md,csv}`, `strategy_library_v2_batch1_grid_review.{md,csv}`, `strategy_library_v2_batch1_summary.md`; helpers `gen_batch1_audit.py`, `run_batch1_jan_smokes.py`, `run_batch1_layer1_sweeps.py`.
- Docs: README, PROJECT_STATUS, PROGRESS, `docs/ARTIFACT_POLICY.md`, `.gitignore` (curated Batch 1 manifest + selection artifacts).
- Chore(walkforward): complete curated **mini-WFO v3** tree — `train_layer1_manifest.csv`, Layer 2 summary CSV/MD (`train_layer2_*`), `train_candidates/` (selected YAMLs + manifests); `.gitignore` for duplicate unprefixed `test/*.csv` exports and heavy `layer3_smoke_v1_diagnosis_qqq_components/system_*/` per-system folders.

### [Unreleased] – 2026-05-08

- Feat(walkforward): **Layer 3 causal mini-WFO v1** — `src/walkforward/mini_wfo.py`, `mini_wfo_selection.py`, config `src/walkforward/configs/qqq_mini_wfo_2023_2024_train_2025_202604_test_v1.yaml` (QQQ train 2023–2024 / test 2025–2026; narrowed strategies; ~288-combo Layer 2 grid); CLI `--validate-only`, `--resume-from {layer2,after_sweep}`; curated results root `src/walkforward/results/layer3_mini_wfo_qqq_2023_2024_train_2025_202604_test_v1/`; tests `tests/test_walkforward_mini_wfo_*.py`. **Not** full WFO; **not** live-ready. Example outcome (local run): **CAUTION** — test PF_R > 1 but **0.02 slippage stress negative** and Dec‑2025 drawdown cluster.
- Feat(walkforward): mini-WFO **selection audit** + **oracle (lookahead) diagnostic** — `selection_audit.{csv,md,json}` and `oracle_diagnostic.{csv,md}` (explicitly labeled NOT selectable); helper `explain_row_eligibility` in `mini_wfo_selection.py`.
- Feat(walkforward): mini-WFO v2A/v2B configs + runs — `qqq_mini_wfo_v2a_2023_2024_train_2025_202604_test.yaml`, `qqq_mini_wfo_v2b_2020_2024_train_2025_202604_test.yaml` with curated outputs under `src/walkforward/results/layer3_mini_wfo_v2{a,b}_.../`.
- Feat(walkforward): mini-WFO comparison report — `src/walkforward/mini_wfo_compare.py` writes `src/walkforward/results/mini_wfo_comparison_v1_v2.md` + `.csv`.
- Feat(research): gap/failed family diagnostics — `src/research/gap_failed_diagnostics.py` regenerates compact trades locally for small windows and writes curated Dec-2025 summaries + gap/failed train/test bucket diagnostics under `src/research/results/gap_failed_family_diagnostics_v1/`.
- Docs(research): gap/failed improvement plan — `src/research/results/strategy_family_improvement_gap_failed_v1.md`.
- Chore(gitignore): `src/walkforward/results/**/sweep_*/` (heavy Layer 2 sweep trees under mini-WFO train).
- Docs: README, PROJECT_STATUS, PROGRESS, `layer3_smoke_plan_v1.md`, `CONFIG_INDEX.md`, `ARTIFACT_POLICY.md`. — `src/walkforward/diagnosis.py`, frozen YAMLs `src/combiner/configs/frozen/diagnosis/`, config `qqq_fixed_system_diagnosis_v1.yaml`, runner hook `outputs.write_diagnosis_report`; curated aggregates under `src/walkforward/results/layer3_smoke_v1_diagnosis_qqq_components/`; tests `tests/test_walkforward_diagnosis.py`.
- Fix(combiner): `run_combiner_fixed_config` no longer writes `trades.csv` when `save_compact_trades=False` (monthly/daily breakdown still use in-memory trades).
- Refactor(metrics): `mean_fold_pf` / `mean_fold_pf_r` alias mean-of-fold PF; `drawdown_exceeds_insample` / `drawdown_exceeds_source_baseline` unset (NA) until a real baseline exists.
- Feat(walkforward): Layer 3 **fixed-system temporal-stability smoke v1** — `src/walkforward/` (folds, frozen systems, runner, metrics, reports), `run_combiner_fixed_config()` in `src/combiner/run.py`, frozen YAMLs in `src/combiner/configs/frozen/`, smoke config `qqq_fixed_system_smoke_v1.yaml`, curated results `src/walkforward/results/layer3_smoke_v1_qqq_fixed_systems/`; tests `tests/test_walkforward_*.py`.
- Docs: README, PROJECT_STATUS, PROGRESS, `src/combiner/configs/CONFIG_INDEX.md`, `docs/ARTIFACT_POLICY.md`, `src/research/results/layer3_smoke_plan_v1.md`; `.gitignore` patterns for heavy `src/walkforward/results/**` outputs.
- Feat(combiner): persistent Layer 2 **candidate signal** disk cache — `signal_cache.py`, `precompute.py` integration, CLI + YAML `precompute`, profile/summary columns; tests `test_combiner_signal_cache.py`, `test_combiner_precompute_signal_cache.py`.
- Chore(gitignore): `.cache/`, `data/cache/`, `*.npy` / `*.npz` / `*.memmap`, `PROJECT_STRUCTURE_AND_SCRIPTS.txt`.
- Docs(results): `layer2_signal_cache_summary.md`.

### [Unreleased] – 2026-05-06

- Feat(features): FeatureStore v1 — `src/features/feature_store.py` in-memory raw/feature reuse; wired into `src/backtest/sweep.py` and `src/combiner/precompute.py`; Layer 2 writes `feature_store_stats.json`.
- Test(features): `test_feature_store.py`, `test_combiner_precompute_feature_store.py`.
- Docs(results): `feature_store_v1_plan.md`, `feature_store_v1_summary.md`.

### [Unreleased] – 2026-05-06

- Refactor(combiner): Layer 2 precompute — new `precompute.py` (context cache key, strategy cache, profile + aggregated summary), `diagnostics.py` (overlap/conflict CSVs); `candidate.py` candidate-only + lazy `__getattr__` re-exports; `run.py` / `sweep.py` / `postprocess.py` import precompute directly; tests `test_combiner_precompute_{cache_key,profile}.py`, `test_combiner_module_boundaries.py`.
- Docs(results): `layer2_precompute_cleanup_plan.md`, `layer2_precompute_cleanup_summary.md`.
- Docs(results): Layer 2 QQQ 2020–2026 post-hardening **strict** + **relaxed** roots (`layer2_qqq_2020_20260430_posthardening_{strict,relaxed}_v1/`), comparison MD, Layer 3 gate note (`layer3_gate_after_2020_posthardening.md`); curated CSV/MD only (sweep `top_runs/` + `fixed_runs/` remain ignored).
- Feat(combiner): configs for 2020 post-hardening Layer 2 strict/relaxed — `layer2_qqq_2020_20260430_posthardening_{strict,relaxed}.yaml`, `layer2_sweep_qqq_2020_20260430_posthardening_{strict,relaxed}.yaml`.
- Docs(results): Layer 1 QQQ **2020-01-01 → 2026-04-30** post-hardening candidate library — `layer1_all10_qqq_2020_20260430_posthardening_v1/` (manifest, **27** YAMLs, `layer1_2020_posthardening_summary.md`).
- Feat(combiner): configs for QQQ **2025-01-01 → 2026-04-30** recent-window Layer 2 check — `layer2_qqq_2025_20260430_recent_check_v1.yaml`, `layer2_sweep_qqq_2025_20260430_recent_check_v1.yaml`.

### [Unreleased] – 2026-05-05

- Feat(combiner): Layer 2 precompute — candidate-level progress logs, optional `candidate_precompute_profile.csv`, in-memory feature/context reuse, generic `resolve_candidate_universe_for_grid` wired into `sweep.py`; `run.py` (diagnostics + saved runs) and `postprocess.py` cost stress emit profile CSVs.
- Test(combiner): `test_combiner_candidate_filtering.py` — warning include/exclude and grid union (no real strategy names).
- Chore(gitignore): allow-list placeholders for QQQ 2020 post-hardening Layer 1 / Layer 2 / comparison / Layer 3 gate MD paths.
- Docs(results): Layer 1 QQQ **2025-01-01 → 2026-04-30** post-hardening candidate library — `layer1_all10_qqq_2025_20260430_posthardening_v1/` (manifest, **40** YAMLs, `layer1_2025_posthardening_summary.md`, top-by-metric CSVs).

### [Unreleased] – 2026-05-05

- Docs(results): post-hardening QQQ 2023–2026 Layer 2 **strict** + **relaxed** sweep outputs, comparison MD, and Layer 1 summary linkage under `layer1_all10_qqq_2023_20260430_posthardening_v1/` and `layer2_qqq_2023_20260430_posthardening_{strict,relaxed}_v1/` (curated CSV/MD only; large sweep logs remain ignored).

### [Unreleased] – 2026-05-02

- Feat(research): `select_candidates.py` — manifest relaxed fallback thresholds configurable via **`--relaxed-min-trades`**, **`--relaxed-min-profit-factor`**, **`--relaxed-min-total-r`**, **`--relaxed-max-drawdown-r`** (defaults match 2020-window spec: 80 / 1.0 / -10 / -100).
- Feat(research): `equity_data_coverage_report.py` — **first/last 20** low-row session lists in CSV and summary MD.
- Feat(combiner): configs for 2020-window v2 relaxed grid — `layer2_qqq_2020_20260430_v2_relaxed.yaml`, `layer2_sweep_qqq_2020_20260430_v2_relaxed.yaml` (candidate_root → `layer1_all10_qqq_2020_20260430_v1/selected_candidates`).
- Docs(progress): Phase 1 coverage refresh; **QQQ backfill incomplete** on disk — Layer 1 2020 rebuild deferred until parquet complete.

### [Unreleased] – 2026-05-05

- Docs(research): hardening closeout (`hardening_closeout_20260505.md`), live status (`hardening_status_current.md`), validation log (`hardening_validation_20260505.md`).
- Docs(research): post-hardening **`rerun_plan_after_hardening.md`** (commands documented only; not executed).
- Docs(results): **`PRE_HARDENING_STALE.md`** for pre-hardening Layer 1 / Layer 2 roots; stale banners on `layer1_2020_summary.md` / `layer2_v2_2020_summary.md`.
- Test(docs): **`tests/README.md`** — test groups and light smoke commands.
- Chore(research): **`hardening_audit_plan.md`** — Commit E consolidation noted.
- Feat(combiner): behavior-level dedupe and stable trade-sequence hash (`behavior.py`, `behavior_unique_*` postprocess artifacts).
- Feat(metrics): cost-as-R helpers, `profit_factor_r`, daily and monthly/quarterly `period_breakdown`, extended `summarize_trades` kwargs for execution cost.
- Feat(postprocess): period CSV exports, rank leaderboards, cost-robust research filter, optional fixed-vs-sweep comparison; CLI flags for behavior dedupe and cost thresholds.
- Feat(combiner/metrics): pass execution slippage/commission/quantity into `summarize_combiner`; daily_trade_number and extra rejection attribution JSON.
- Test(combiner): `test_combiner_behavior.py`, `test_cost_as_r_metrics.py`, `test_daily_metrics.py`, `test_combiner_postprocess.py`.
- Docs(research): `hardening_commit_d_plan.md`; `hardening_audit_plan.md` marks Commit D complete and points to Commit E.

### [Unreleased] – 2026-05-05

- Feat(strategies): `validate_config` hooks and shared `src/utils/config_validation.py` (strategy + combiner YAML checks).
- Fix(cache): `context_key` audit for ATR/window/buffer params used in `prepare_signal_context`; combiner/run/sweep validate base YAML.
- Chore(config): remove unused `features.midday_window` from afternoon continuation YAMLs; reject fake axes in validation.
- Test(strategies): `test_strategy_config_validation.py`, `test_strategy_context_keys.py`.
- Fix(combiner): speed up diagnostics by vectorizing same-bar and same-day overlap; replace slow minute-diff loop with an approximate median-minute diff; add progress prints and safe partial writes.
- Fix(data): `pull_ibkr_1min.py` — `reqHistoricalData` on **qualified** equity contract; **3** request retries; **reconnect backoff** (multi-attempt `ensure_ib_connected`).
- Feat(research): `equity_data_coverage_report.py` — session/month stats + `data_coverage.csv` / `data_coverage_summary.md` for SPY/QQQ windows.
- Docs(readme/progress): long-history pull + coverage command; backfill notes under `src/research/results/data_backfill_spy_qqq_2020_20260430/`.
- Docs(research): add platform hardening audit + plan (`hardening_audit_20260505.md`, `hardening_audit_plan.md`).
- Fix(backtest): start max_drawdown from zero; validate stop/target side + finite prices.
- Fix(combiner): prevent cooldown leaking across sessions; add fast daily_trade_number; add explicit rejection reasons for invalid stop/target and opposite-direction conflicts.
- Test(unit): add pytest + initial execution/drawdown tests.
- Docs(research): refresh hardening plan for HEAD `6bc1c7c` (mark Commit A done; prep Commit B).
- Feat(features): make full-session aggregates explicit (`full_session_*_LOOKAHEAD`); add intraday-safe `intraday_high_so_far` / `intraday_low_so_far`; add ORB `*_known` columns.
- Fix(cache): centralize feature cache key (`FeatureBuildConfig` + `feature_key_from_config`) and use across backtest sweep, combiner precompute, and research parity.
- Test(features): add no-lookahead and feature-key unit tests.

### [Unreleased] – 2026-05-02

- Feat(combiner): restore generic `postprocess.py` (grid dedupe key, `top_unique_*`, `top_unique_run_map.csv`, diagnostics MD, fixed-run collector, cost stress with generic `cost_robustness_label`).
- Chore(repo): `.gitignore` — ignore `data/raw/`, caches, heavy combiner/sweep outputs; un-ignore curated summaries and Layer 1 `selected_candidates/*.yaml`.
- Docs(readme/progress/results): recovery notes, postprocess CLI, `recovery_status_before.md`, `layer2_summary.md` regeneration template; cost stress placeholder.

### [Unreleased] – 2026-05-02

- Feat(combiner): Layer 2 v1 — Numba combiner core, `precompute_candidate_signal_matrices` once per sweep, `build_enabled_mask`, candidate-set profiles in YAML, `sweep.py` grid (`layer2_sweep_qqq_v1.yaml`), diagnostics (`diagnostics/`), `combiner_score` in `metrics.py`, `run.py` / `sweep.py` CLIs, results under `src/combiner/results/layer2_qqq_v1/`.
- Docs(readme/progress): Layer 2 workflow commands.

### [Unreleased] – 2026-05-05

- Feat(research): **`run_layer1_focused.py`** — generic multi-strategy sweep orchestration, incremental **`sweep_manifest.csv` / `.md`**, resume.
- Feat(research): **`select_candidates.py`** — **`--manifest`**, **`--output-root`**, **`--top-per-strategy`**, **`--allow-relaxed-fallback`**; candidate YAML includes **`metadata`** / **`selection`**.
- Refactor(loader): **`load_testing_config`** falls back to **`{name}_focused.yaml`** when **`{name}.yaml`** is missing.
- Refactor(strategies): remove **`df_signal_strategy.py`** (superseded by true fast cores).
- Docs(readme/progress): Layer 1 bundle commands; artifact cleanup note.

### [Unreleased] – 2026-05-06

- Chore(repo): expand `.gitignore` to also ignore heavy `src/research/results/**` artifacts and `*.parquet`.
- Chore(results): local-only cleanup of generated Layer 2 artifacts (`equity.csv`, `trades.csv`, `top_runs/`, `run_*`, `sweep_*`) under `src/combiner/results/**`.
- Docs(results): add pre‑Layer‑3 cache benchmark plan + comparison + summary (Layer 2 recent; cache_off/cold/warm outputs consistent; warm cache hit-rate improves runtime).
- Docs(results): regenerate active Layer 2 diagnostics summaries (`diagnostics/diagnostics_summary.md`) and add pre‑Layer‑3 readiness summary.

### [Unreleased] – 2026-05-02

- Refactor(strategies): migrate eight Strategy Library v1 plugins from **`DfSignalStrategy`** to **`BaseStrategy`** true context + Numba cores (`failed_orb`, `orb_retest_continuation`, `vwap_trend_pullback`, `vwap_reclaim_reject`, `prior_day_level_trap`, `gap_acceptance_failure`, `midday_compression_breakout`, `afternoon_continuation`); shared helpers in **`fast_utils.py`** only; **`df_signal_strategy`** documented as MVP adapter (**`B_df_adapter_fast_compatible`**).
- Feat(research): generic **`check_strategy_fast_parity.py`** (readable `generate_signals` vs fast arrays).
- Docs(readme/progress): migration note, parity command, **`strategy_fast_core_migration_v1_*.csv`** results.

### [Unreleased] – 2026-05-04

- Docs(progress/readme): Strategy Library v1 health audit artifact paths (`strategy_library_v1_health.csv`, `strategy_library_v1_audit_report.md`).

### [Unreleased] – 2026-05-02

- Feat(features): `price_action`, `volume`, `gap_prior_range_norm`, VWAP slopes (20/30/60), close above/below VWAP, session VWAP persistence (10/20/30/60); `build_basic_features` wires all modules.
- Feat(strategies): eight new plugins (`failed_orb`, `orb_retest_continuation`, `vwap_trend_pullback`, `vwap_reclaim_reject`, `prior_day_level_trap`, `gap_acceptance_failure`, `midday_compression_breakout`, `afternoon_continuation`) plus shared `DfSignalStrategy` / defaults / focused testing YAMLs (QQQ, slippage **0.01**, `min_risk_per_share` **0.03** in grids).
- Feat(strategies): `metadata.yaml` + `metadata.py`; **Layer 1 candidate selector reads metadata** instead of hardcoded ORB/VWAP-only defaults (`conflict_group` optional on exported YAML).
- Feat(risk): **`risk.min_risk_per_share`** helpers and filtering on ORB/VWAP + new strategies; combiner rejects **`risk_too_small`**; **`risk_too_small_rejections`** in metrics.
- Docs(readme): Strategy Library v1 section and **`min_risk_per_share`** semantics.
- Feat(backtest): `backtest.max_hold_minutes` with exit reason `max_hold`; metrics `max_hold_count` (readable `engine.py` + Numba `fast.py`).
- Feat(sweep): `--testing-config`, `--tag`, display-only execution-style filters (`--max-avg-bars-held`, `--max-eod-count`, `--max-end-of-data-count`, `--min-profit-factor`, `--min-total-r`, `--max-drawdown-r`); broader console columns when present (`max_hold_count`, `avg_bars_held`, EOD counts).
- Feat(strategies): `normalized_param_key` includes `max_hold_minutes` for ORB and VWAP (sweep dedupe).
- Research(config): add `orb_continuation_focused.yaml` and `vwap_reversal_focused.yaml` (do not replace broad grids).
- Docs(readme): max-hold semantics, focused grids, focused sweep examples and interpretation.
- Initial strategy / backtest framework: `BaseStrategy`, ORB plugin, YAML configs, readable engine, generic Numba execution in `fast.py`, sweep runner, loader.

### [Unreleased] – 2026-05-04

- Feat(research): `select_candidates.py` + `scoring.py` to build a Layer 1 candidate library (`selected_candidates.csv` + per-candidate YAML) from sweep `results.csv` (glob-friendly paths).
- Feat(combiner): MVP Layer 2 (`candidate.py`, `simulator.py`, `metrics.py`, `run.py`) — one open position, YAML routing (`configs/orb_vwap_simple.yaml`), daily limits, priority selection, **`candidate_signal_log.csv`** / **`rejected_signals.csv`**, slippage default **0.01** / commission **0**; no strategy params hardcoded in combiner code.
- Docs(readme): Layer 1 → Layer 2 workflow and example commands.

### [Unreleased] – 2026-05-03

- Feat(strategies): add `vwap_reversal` plugin with readable and context-based Numba fast paths.
- Feat(strategies): add `vwap_reversal` default + sweep YAML and loader registration.
- Refactor(strategies): add context-based fast interface (`prepare_signal_context`, `context_key`, `generate_signal_arrays_from_context`, `normalized_param_key`) on `BaseStrategy`.
- Feat(strategies): add `fast_utils.py` for session prev / rolling / thinning Numba helpers (not in `backtest/fast.py`).
- Refactor(orb): ORB fast path uses `ORBContinuationContext` and shared thinning helpers.
- Refactor(vwap): VWAP fast path uses `VWAPReversalContext` and Numba signal core (sweep no longer calls readable pandas for signal arrays).
- Refactor(sweep): cache strategy signal contexts; skip duplicate effective parameter sets via `normalized_param_key` per symbol.
- Refactor(sweep): flatten all `features` / `signal` / `risk` / `backtest` params into `results.csv`; narrow display columns for console and `summary.txt`.
- Perf(vwap): full-range capped VWAP sweep dropped from ~564s / 300 combos to seconds-level (context cache + Numba).
- Docs(readme): context fast path, sweep caching, dynamic results columns, VWAP full sweep save command.
