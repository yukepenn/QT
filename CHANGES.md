### [Unreleased] – 2026-05-06

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
