# Research results index (`src/research/results/`)

This index classifies **result roots** without moving or deleting them.

## A. Active / current

- **Global strategy audit v1 (2026-05-10)** — `global_strategy_audit_v1/` (`strategy_eligibility_matrix.*`, `strategy_side_support_matrix.*`, `global_strategy_audit_summary.md`); script `src/research/global_strategy_audit.py`.
  - **keep:** yes

- **Global Layer 1 QQQ 2023–2024 v1 (2026-05-10)** — `global_layer1_qqq_2023_2024_design.md`, `layer1_global_qqq_2023_2024_v1/` (manifest, skipped strategies, strict **`selected_candidates/`** ×81, diversity + fast-context outputs, `layer1_global_summary.md`, `global_layer2_gate_decision.md`); runner `src/research/run_global_layer1.py`; `global_branch_leaderboard_v1.{csv,md}`; `global_candidate_signal_diversity_qqq_2023_2024_v1/`; `global_layer2_qqq_2023_2024_design.md` (design-only; **Layer 2 not run** — gate fails: 81 YAMLs > 80 cap).
  - **keep:** yes

- **Feature build performance v2 verify (2026-05-11)** — `feature_build_performance_v2/verify_after/` + `feature_warning_verify.md` (post-`51bfe17` fragmentation check before Global L1 v2).
  - **keep:** yes

- **Trade quality / regime-context diagnostics v1 (2026-05-10)** — `trade_quality_router_v1/` (`trade_quality_router_v1_summary.md`, `regime_router_design_from_evidence_v1.md`, `setup_taxonomy_v1.{csv,md}`, `analysis/**` bucket summaries, `quality_score/threshold_simulation_*.csv`, `quality_score/pnl_by_quality_decile_*.csv`, `quality_score/score_rules_resolved_*.json`, manifest + schema inventory); scripts `src/research/enrich_combiner_trades.py`, `analyze_trade_quality.py`, `score_trade_quality_offline.py`, `trade_quality_helpers.py`; research YAMLs `layer2_diag_vwap_lower_turnover.yaml`, `layer2_diag_indicator_mtp1.yaml`. **Local-only (not committed):** `trade_quality_router_v1/local_runs/`, `enriched_trades/*_enriched.csv`, `quality_score/scored_trades_*.csv`. **Router decision:** **`NEED_MORE_TRADE_ENRICHMENT`**.
  - **keep:** yes

- **Trade quality router diagnostics v1.5 (2026-05-10)** — `trade_quality_router_v1_5/` (`trade_quality_router_v1_5_summary.md`, `router_readiness_decision_v15.md`, `baseline_inventory.md`, `unknown_regime/**`, `holdout/**`, `exit_slip/**`, `indicator_mtp_diagnostics/**`, `quality_score_v15/**`, diag YAMLs `layer2_diag_indicator_mtp{2,3}.yaml`); scripts `decompose_regime_unknown.py`, `validate_trade_quality_holdout.py`, `analyze_exit_slip_attribution.py`, `build_indicator_mtp_diagnostics.py`, `score_trade_quality_v15.py`, `trade_quality_unknown.py`; tests `test_decompose_regime_unknown.py`, `test_validate_trade_quality_holdout.py`, `test_analyze_exit_slip_attribution.py`. **Local-only:** `trade_quality_router_v1_5/local_runs/**`, `enriched_staging/**`, raw `trades.csv`. **No** strategy / feature / combiner / candidate-YAML changes. **Router decision:** **`NEED_MORE_TRADE_ENRICHMENT`**.
  - **keep:** yes

- **Fixed-profile out-of-window validation v1 (2026-05-11)** — `fixed_profile_oow_v1/` (`fixed_profile_oow_v1_summary.md`, `fixed_profile_oow_decision.md`, `execution_runbook.md`, `run_discovery_manifest.csv`, `run_execution_manifest.csv`, `run_commands_multiline.md`, `run_commands_powershell.ps1`, `fixed_profile_definitions.{md,csv}`, `data_availability.{md,csv}`, `configs/layer2_fixed_*.yaml`, `oow/**`, `insample_sanity/**`, `exit_slip/**`, `quality_score_transfer/**`, `regime_stability/**`, `trade_number/**`, `fixed_profile_oow_key_findings.csv`); CLI `src/research/fixed_profile_oow.py` (`inspect-data`, `run`, `enrich`, `postprocess`, `print-commands`); `fixed_profile_oow_lib.py`; tests `test_fixed_profile_oow_lib.py`. **Local-only:** `fixed_profile_oow_v1/local_runs/**` (`trades.csv`, `trades_enriched.csv`). **No** strategy / feature / combiner behavior / candidate-YAML / WFO / live / SPY / Global L1 / broad L2 grid changes. **Decision (executed OOW):** **`REVISIT_LAYER2_CANDIDATE_SELECTION`**.
  - **keep:** yes

- **Layer2 candidate robustness v1 (2026-05-11)** — `layer2_candidate_robustness_v1/` (`baseline_inventory.md`, `candidate_robustness_audit_design.md`, `candidate_oow_summary.md`, `candidate_oow_metrics.csv` (**198** rows), `candidate_oow_wide_metrics.csv`, `candidate_robustness_labels.csv`, `family_oow_summary.csv`, `strategy_oow_summary.csv`, `full_*_interpretation.{md,csv}`, `l2_core_failure_analysis.{md,csv}`, `l2_core_policy_v2*`, `layer2_candidate_robustness_{decision,v1_summary}.md`, `layer2_candidate_robustness_key_findings.csv`, `remaining_candidate_inventory.*`, `extended_audit_inventory.md`, `robust_core_dry_run/**`, manifests, `side_flip/**`); CLIs `src/research/audit_l2_candidates_oow.py` (`inspect-data`, `print-commands`, `inventory`, `run`, `postprocess`), `audit_l2_candidates_oow_lib.py`, `audit_l2_candidates_oow_report.py`, `side_flip_diagnostic.py`; tests `test_audit_l2_candidates_oow.py`, `test_side_flip_diagnostic.py`, `test_l2_core_policy_v2.py`. **Local-only:** `layer2_candidate_robustness_v1/local_runs/**`. **Audit coverage:** l2_core **66 / 66** YAMLs × **3** windows = **198** singleton combiner runs (all `status=OK` in metrics grid); **no** strategy / feature / selected-candidate YAML / combiner behavior changes; **no** WFO / live / SPY / Global L1 / broad L2. **Decision:** **`CREATE_ROBUST_L2_CORE_V2_DESIGN`** (dry-run manifest `robust_core_dry_run/`).
  - **keep:** yes

- **Robust l2_core v2 design (2026-05-11, design-only)** — `robust_l2_core_v2_design/` (`baseline_inventory.md`, `robust_candidate_dedupe_table.csv`, `effective_signal_clusters.csv` (metric-identical + **trade-identical** dedupe; raw vs design rep), `robust_candidate_overlap_matrix.csv` + summary (compact overlap only; raw trades local-only), `representative_candidate_manifest.*`, `candidate_sets_design.*`, `core_watchlist_drop_policy.md`, `core_watchlist_drop_actions.csv`, `design_artifact_validation.*`, `design_cleanup_inventory.md`, `future_diagnostic_runbook.md`, `future_diagnostic_commands_draft.md`, `robust_l2_core_v2_design.md`, `robust_l2_core_v2_decision.md`, `robust_l2_core_v2_design_summary.md`, `robust_l2_core_v2_key_findings.csv`, `config_skeletons/**` marked **DESIGN ONLY — NOT RUN**); scripts `src/research/design_robust_l2_core_v2.py`, `src/research/validate_research_artifacts.py`. **No** Layer2 sweep / WFO / live / SPY / strategy changes / feature changes / selected YAML edits; **no** raw `trades.csv` committed.

- **Robust l2_core v2 diagnostic v1 (2026-05-11, executed small grid)** — `robust_l2_core_v2_diagnostic_v1/` (`baseline_inventory.md`, `run_plan.csv`, `run_execution_manifest.csv`, `run_discovery_manifest.csv`, `diagnostic_results.csv`, `candidate_set_summary.csv`, `grid_axis_summary.csv`, `window_summary.csv`, `top_systems_{overall,by_window}.csv`, `diagnostic_summary.md`, `robust_l2_core_v2_diagnostic_{summary,decision}.md`, `robust_l2_core_v2_diagnostic_key_findings.csv`, `exit_slip/robust_core_exit_slip_scenarios.csv`, `complementarity/*`). Script `src/research/run_robust_l2_core_diagnostic.py`. **No** broad Layer2 / WFO / live / SPY / router / YAML edits; raw `local_runs/**` local-only.

- **Fixed robust-profile OOW v1 (2026-05-11, executed locked profiles)** — `fixed_robust_profile_oow_v1/` (`fixed_profile_definitions.*`, `run_plan.csv`, `run_execution_manifest{,_sanitized}.csv`, `run_discovery_manifest.csv`, `fixed_profile_results.csv`, `profile_{window,overall}_summary.csv`, `monthly/quarterly/yearly_summary.csv`, `drawdown_summary.csv`, `trade_number_summary.csv`, `exit_reason_summary.csv`, `exit_slip/fixed_profile_exit_slip_scenarios.csv`, `fixed_robust_profile_oow_{summary,decision}.md`, `fixed_robust_profile_oow_key_findings.csv`, `CHATGPT_REVIEW_BUNDLE.md`, `fixed_profile_artifact_validation.*`). Script `src/research/run_fixed_robust_profile_oow.py`. **No** broad Layer2 / WFO / live / SPY / router / YAML edits; raw `local_runs/**` local-only.
  - **keep:** yes

- **Layer3 fixed-profile smoke design v1 (2026-05-11, design-only)** — `layer3_fixed_profile_smoke_design_v1/` (profile selection, gate design, run plan, expected outputs schema, risk register, command draft, decision + summary + key findings, `CHATGPT_REVIEW_BUNDLE.md`, `SOURCE_MAP.csv`, artifact validation). **Design decision:** **`RUN_LAYER3_FIXED_PROFILE_SMOKE`**. Execution lives in **`layer3_fixed_profile_smoke_v1/`** (separate result root below).
  - **keep:** yes

- **Layer3 fixed-profile smoke v1 (2026-05-11, executed CORE only)** — `layer3_fixed_profile_smoke_v1/` (8 combiner replays: `pa_only_mtp1_meta`, `pa_gap_mtp2_meta` × four windows; `run_plan.csv`, `run_execution_manifest{,_sanitized}.csv`, `run_discovery_manifest.csv`, profile/monthly/quarterly/yearly/drawdown/exit/trade summaries, `fixed_oow_comparison.csv`, gates + risk flags, `exit_slip/*`, `complementarity/*`, decision + summary + key findings, `CHATGPT_REVIEW_BUNDLE.md`, `SOURCE_MAP.csv`, `layer3_smoke_artifact_validation.*`). Script `src/research/run_layer3_fixed_profile_smoke.py`; tests `tests/test_run_layer3_fixed_profile_smoke.py`. **No** broad Layer2 / WFO / live / SPY / router; **no** strategy/feature/selected-candidate YAML edits; **`local_runs/**` and `local_configs/**` local-only (not committed). **CORE-only decision (historical):** **`RUN_OPTIONAL_LAYER3_BASELINE_ABLATION`**.
  - **keep:** yes

- **Layer3 fixed-profile smoke optional v1 (2026-05-11, executed optional baseline/ablation)** — `layer3_fixed_profile_smoke_optional_v1/` (**12** runs: `primary_mtp2_meta`, `pa_gap_mtp1_meta`, `pa_only_mtp2_meta` × four windows; dry-run validation; manifests; same summary/gate/risk/exit-slip/complementarity pattern as CORE; `layer3_optional_*` decision/summary/key findings; `CHATGPT_REVIEW_BUNDLE.md`; `SOURCE_MAP.csv` repo-relative paths; `layer3_optional_artifact_validation.*`). Runner `postprocess --smoke-kind optional`. **`local_runs/**` / `local_configs/**` local-only.
  - **keep:** yes

- **Layer3 fixed-profile smoke complete v1 (2026-05-11, merged CORE + optional)** — `layer3_fixed_profile_smoke_complete_v1/` (`complete_profile_window_summary.csv`, `complete_profile_full_available_summary.csv`, `complete_gate_results.*`, `complete_risk_flags.*`, `complete_ranking.csv`, `core_vs_optional_comparison.csv`, `complete_exit_slip_*`, `complete_candidate_contribution.*`, `layer3_complete_smoke_{decision,summary,key_findings}.*`, `CHATGPT_REVIEW_BUNDLE.md`, `SOURCE_MAP.csv`, `layer3_complete_artifact_validation.*`). Subcommand `merge-complete`. **Five-profile** review. **Decision:** **`PROCEED_TO_LAYER3_EXPANDED_STABILITY_DESIGN`**. **No** WFO/live/SPY/router/strategy/feature/YAML edits.
  - **keep:** yes

- **Layer3 expanded stability design v1 (2026-05-11, design-only)** — `layer3_expanded_stability_design_v1/` (profile selection; weak-period + market-context label designs; gate design; **non-executed** run plan; expected outputs for future `layer3_expanded_stability_v1/`; risk register; `CHATGPT_REVIEW_BUNDLE.md`; `SOURCE_MAP.csv`; `chatgpt_key_tables.csv`; decision **`RUN_LAYER3_EXPANDED_STABILITY`**; artifact validation). Tests `tests/test_layer3_expanded_stability_design.py`. **No** expanded stability execution; **no** WFO/mini-WFO/live/SPY/broad L2/router/strategy/feature/YAML edits.
  - **keep:** yes

- **Layer3 expanded stability v1 (2026-05-11, executed postprocess)** — `layer3_expanded_stability_v1/` (monthly/quarterly/rolling stability from `complete_*` summaries; QQQ market context from local `data/raw/ibkr` parquet; weak-period context + PnL ranks; window-anchored cost stress; exit + contribution tables; gate rollup + risk flags; `expanded_stability_profile_labels.csv`; decision **`PROCEED_TO_PRE_WFO_STABILITY_DESIGN`**; `CHATGPT_REVIEW_BUNDLE.md`, `SOURCE_MAP.csv`, `chatgpt_key_metrics.csv`, manifests + `layer3_expanded_stability_artifact_validation.*`). Runner **`src/research/run_layer3_expanded_stability.py`**; tests **`tests/test_run_layer3_expanded_stability.py`**. **No** combiner / trading rerun; **no** WFO / mini-WFO / live / paper / SPY / broad L2 / router / strategy / feature / selected-candidate YAML edits; period-sliced exit/candidate rows marked **`REQUIRES_LOCAL_DETAILED_REPLAY`** where curated smoke lacks quarter trade tables.
  - **keep:** yes

- **Playbook Router Research Cycle v1 (2026-05-11, design + diagnostics)** — `playbook_router_research_cycle_v1/` (`baseline_inventory.md`, `champion_v0_freeze.*`, `trade_context_panel_schema.*`, `trade_context_panel_v1/*` aggregated-only, `context_diagnostics_v1/*`, `router_metadata_v1/candidate_playbook_metadata.*`, `router_design_v1/offline_router_rule_design.*` + **`router_v1_config_draft.yaml`** with **`enabled: false`**, **`mode: offline_diagnostic`**, `trade_quality_score_v2/*`, `exit_overlay_design_v1/*`, `scalp_strategy_roadmap_v1/*`, `short_strategy_roadmap_v1/*`, `next_3layer_sweep_roadmap.*`, `playbook_router_cycle_v1_decision.md` **`RUN_LOCAL_DETAILED_TRADE_CONTEXT_REPLAY`**, `CHATGPT_REVIEW_BUNDLE.md`, `SOURCE_MAP.csv`, `chatgpt_key_tables.csv`, `playbook_router_cycle_v1_artifact_validation.*`). Scripts **`src/research/build_trade_context_panel.py`**, **`src/research/analyze_playbook_context.py`**; tests **`tests/test_playbook_router_cycle_v1.py`**. **Champion v0 frozen** (`pa_only_mtp1_meta`, `pa_gap_mtp2_meta`, `primary_mtp2_meta` reference). **No** WFO/live/SPY/broad L2/Global L1/combiner rerun; **no** production router wiring; **no** new strategies / short / scalp code; **no** YAML/signal edits; **no** raw trades or row-level trade panel commits.
  - **keep:** yes

- **Global strategy audit v2 + Global Layer 1 v2 + l2_core (2026-05-11)** — `global_strategy_audit_v2/`; `layer1_global_qqq_2023_2024_v2/` (30 sweeps, **81** strict YAMLs, diversity `global_candidate_signal_diversity_qqq_2023_2024_v2/`, fast-context, gate + summary); **`selected_candidates_l2_core/`** (66 YAMLs, builder `create_layer2_candidate_core.py`); diversity `global_candidate_signal_diversity_l2_core_qqq_2023_2024_v2/`; `global_branch_leaderboard_v2.{csv,md}`; `build_global_branch_leaderboard_v2.py`; `global_research_summary_v2.md`; `global_layer2_qqq_2023_2024_v2_design.md`; `global_layer2_gate_decision_v2.md`; `layer2_global_diagnostics_smoke_q1_2023.md` (Q1 combiner diagnostics summary — heavy combiner `diagnostics/` folder local-only). Runner gains `--diversity-output-root`, `--branch-leaderboard-*`, `--copy-gate-md-to`; audit summary variant for v2; `emit_global_layer2_v2_configs.py`; combiner configs `layer2_qqq_global_2023_2024_v2.yaml` + sweep. **Full-window Global Layer 2 v2 curated outputs:** `src/combiner/results/layer2_qqq_global_2023_2024_v2/layer2_global_full_summary.md` (heavy `sweep_*` / `top_runs/` remain local-only); evaluation decision **`TUNE_LAYER2_COST_TURNOVER`**. **Cost/turnover follow-on** (curated diagnostics + gate in same combiner root): **`TUNE_LAYER2_COST_TURNOVER_AGAIN`** (`layer2_cost_turnover_gate_decision.md`).
  - **keep:** yes

- **Feature build performance v1 (2026-05-10)** — `feature_build_performance_v1/` (before/after `feature_build_benchmark.*`, `feature_performance_hardening_summary.md`); `feature_output_snapshot_{before,after}/`; `feature_numba_fastpath_design.md` (design only); scripts `src/research/feature_build_benchmark.py`, `feature_output_snapshot.py`; batch-concat refactors in `volume.py`, `volatility.py`, `vwap.py`, `price_action.py`, `orb.py`, `levels.py`; tests `test_feature_performance_equivalence.py`. **No** Global Layer 1/2 rerun; **no** mini-WFO/full WFO/live.
  - **keep:** yes

- **PA Batch A (price-action branch — planning + smokes)** — curated docs:
  - `pa_batch_a_plan.md`, `pa_repo_formatting_check.md`, `pa_feature_foundation_summary.md`
  - `pa_batch_a_parity_smoke.{md,csv}`, `pa_batch_a_jan2025_smoke.{md,csv}`, `pa_batch_a_implementation_summary.md`
  - **status:** feature foundation + four strategies in `loader`; formal economics in **`layer1_pa_batch_a_qqq_2023_2024/`** (see below).
  - **keep:** yes

- **PA Batch B (implementation + smokes)** — `pa_batch_b_c_implementation_plan.md`, `pa_batch_b_implementation_summary.md`, `pa_batch_b_parity_smoke.{md,csv}`, `pa_batch_b_jan2025_smoke.{md,csv}`
  - **status:** four plugins; formal Layer 1 economics in **`layer1_pa_batch_bc_qqq_2023_2024/`** (with Batch C)
  - **keep:** yes

- **PA Batch C (+ library handoff)** — `pa_batch_c_implementation_summary.md`, `pa_batch_c_parity_smoke.{md,csv}`, `pa_batch_c_jan2025_smoke.{md,csv}`, `pa_overlap_refinements_backlog.md`, `pa_strategy_library_completion_summary.md`
- **PA `context_key` cache scope (engineering, 2026-05-10)** — `pa_context_key_cache_scope_audit.md`, `pa_context_key_signal_fingerprint_check.md`, `pa_context_key_cache_reuse_smoke.md`, `pa_context_key_cache_optimization_summary.md` (performance-only; tests `tests/test_pa_context_key_scope.py`)
  - **status:** two plugins; formal Layer 1 economics in **`layer1_pa_batch_bc_qqq_2023_2024/`**
  - **keep:** yes

- **PA Brooks framework primitives (features + helpers, 2026-05-10)** — `pa_brooks_framework_optimization_plan.md`, `pa_brooks_feature_primitives_summary.md`, `pa_brooks_strategy_compatibility_audit.md`, `pa_brooks_feature_smoke.{md,csv}`, `pa_brooks_framework_parity_smoke.{md,csv}`, `pa_brooks_framework_optimization_summary.md`; tests `tests/test_pa_bar_primitives.py`, `tests/test_pa_swing_primitives.py`, `tests/test_pa_regime_router_features.py`, `tests/test_pa_level_magnet_features.py`, `tests/test_pa_common.py`, `tests/test_pa_required_features_no_lookahead.py`
  - **status:** shared `pa_*` feature columns + `strategy/pa_common.py`; **no** Layer 1/2/WFO reruns; **no** new strategies
  - **keep:** yes

- **PA Brooks primitives cleanup (namespace + registry + swing ages, 2026-05-10)** — `strategy_helper_namespace_audit.md`, `pa_brooks_feature_registry_audit.md`, `pa_brooks_numba_fastpath_audit.md`, `pa_common_adoption_policy.md`, `pa_brooks_primitives_cleanup_summary.md`; code `src/strategies/common/pa.py`, shims `strategy/pa_batch_a_utils.py`, `strategy/pa_common.py`; `pa_swings` side-specific ages; tests `test_strategy_helper_namespace.py`, `test_pa_swing_side_specific_primitives.py`, `test_pa_brooks_feature_registry.py`
  - **status:** engineering-only; loader **35** unchanged; **no** Layer 1/2/WFO
  - **keep:** yes

- **`layer1_pa_batch_bc_qqq_2023_2024/`**
  - **status:** formal **PA Batch B + C** Layer 1 (QQQ 2023–01–01 → 2024–12–31), tag `layer1_pa_batch_bc_qqq_2023_2024`
  - **purpose:** six `*_focused.yaml` sweeps → manifest → strict selection (**5** YAMLs, **`pa_buy_sell_close_trend` only**); `signal_rate_diagnosis.*`, optional `diagnostic_relaxed_selection/` (DIAGNOSTIC ONLY); `candidate_fast_context_check.*`
  - **decision:** **`TUNE_PA_BATCH_BC_GRIDS_FIRST`** (`layer1_pa_batch_bc_summary.md`). **PA Batch B/C Layer 2 / mini-WFO / full WFO / live not run.**
  - **keep:** yes

- **`layer1_pa_batch_bc_tuned_qqq_2023_2024_v1/`**
  - **status:** PA Batch B+C **tuned grids v1** Layer 1 (QQQ 2023–01–01 → 2024–12–31), tag `layer1_pa_batch_bc_tuned_qqq_2023_2024_v1`
  - **purpose:** tuned `*_tuned_v1.yaml` sweeps → manifest → strict selection (**5** YAMLs, **`pa_climax_reversal` only**); tuned `signal_rate_diagnosis.*`; `candidate_fast_context_check.*`; optional `diagnostic_relaxed_selection/` (**DIAGNOSTIC ONLY**; CSV + `DIAGNOSTIC_ONLY.md` only)
  - **decision:** **`TUNE_PA_BATCH_BC_GRIDS_AGAIN`** (`layer1_pa_batch_bc_tuned_v1_summary.md`). **PA Batch B/C Layer 2 / mini-WFO / full WFO / live not run.**
  - **keep:** yes

- **`layer1_pa_batch_bc_tuned_qqq_2023_2024_v3/`**
  - **status:** PA Batch B+C **tuned grids v3** Layer 1 (QQQ 2023–01–01 → 2024–12–31), tag `layer1_pa_batch_bc_tuned_qqq_2023_2024_v3`
  - **purpose:** diversity-aware grids (`*_tuned_v3.yaml`) → gate preflight `pa_batch_bc_gate_diagnostics_v3_preflight/` → sweeps (two strategies) → **10** strict YAMLs; `pa_batch_bc_candidate_signal_diversity_v3/`; optional `selected_candidates_diverse/`; `pa_batch_bc_exit_diagnostics_v3/`; `candidate_signal_diversity.py` / `select_diverse_candidates.py`
  - **decision (strict top-5):** **`TUNE_PA_BATCH_BC_GRIDS_AGAIN`** (`layer1_pa_batch_bc_tuned_v3_summary.md`) — climax strict set still **one** `pure_signal_hash` among the **score-top five**
  - **repair (selector / raw audit, 2026-05-10):** `pa_batch_bc_climax_diversity_repair_plan.md`, `pa_batch_bc_raw_signal_diversity_v3/`, `src/research/sweep_result_signal_diversity.py`, `src/research/export_diverse_candidates_from_results.py`, `selected_candidates_repaired/`, `pa_batch_bc_candidate_signal_diversity_repaired_v3/`, `repaired_candidate_decision.md` (**RUN_LAYER2_REPAIRED_V3**). **Layer 2 repaired v3** (`src/combiner/results/layer2_qqq_pa_batch_bc_repaired_v3_2023_2024/`): post-behavior gate decision **`TUNE_PA_BATCH_BC_GRIDS_AGAIN`** — see combiner **`RESULTS_INDEX.md`** + `layer2_pa_batch_bc_repaired_v3_behavior_completion.md`.
  - **keep:** yes

- **`pa_batch_bc_diversity_repair_summary.md`**
  - **status:** cross-cutting write-up for climax diversity repair + repaired Layer 2 follow-up
  - **keep:** yes

- **`layer1_pa_batch_bc_tuned_qqq_2023_2024_v2/`**
  - **status:** PA Batch B+C **tuned grids v2** Layer 1 (QQQ 2023–01–01 → 2024–12–31), tag `layer1_pa_batch_bc_tuned_qqq_2023_2024_v2`
  - **purpose:** diagnostic-first `*_tuned_v2.yaml` → gate preflight (`pa_batch_bc_gate_diagnostics_v2_preflight/`) → sweeps (four strategies; two skipped preflight) → manifest → **10** strict YAMLs (**5** `pa_buy_sell_close_trend` + **5** `pa_climax_reversal`); `signal_rate_diagnosis.*`; `candidate_fast_context_check.*`; `pa_batch_bc_exit_diagnostics_v2/`; optional `diagnostic_relaxed_selection/` (**DIAGNOSTIC ONLY**)
  - **decision (Layer 1):** **`PROCEED_TO_PA_BATCH_BC_REDUCED_LAYER2_DESIGN`** (`layer1_pa_batch_bc_tuned_v2_summary.md`) — combiner design `reduced_layer2_pa_batch_bc_tuned_v2_design.md`
  - **Layer 2:** executed reduced combiner pass → `src/combiner/results/layer2_qqq_pa_batch_bc_tuned_v2_2023_2024/` — summary **`layer2_pa_batch_bc_tuned_v2_summary.md`** (**`TUNE_PA_BATCH_BC_GRIDS_AGAIN`**; **mini-WFO / full WFO / live not run**)
  - **keep:** yes

- **`pa_batch_bc_gate_diagnostics_v1/`**
  - **purpose:** gate pass-rate CSV/MD for tuned **v1** PA YAMLs (QQQ 2023–2024); bottleneck analysis (`pa_gate_diagnostics.py`).
  - **keep:** yes

- **`pa_batch_bc_gate_diagnostics_v2_preflight/`**
  - **purpose:** gate pass-rate CSV/MD for tuned **v2** YAMLs before sweeps (`pa_gate_diagnostics.py`).
  - **keep:** yes

- **`pa_batch_bc_exit_diagnostics_v1/`**
  - **purpose:** exit / slippage-stress summaries from existing Layer 1 candidate YAMLs (`pa_exit_diagnostics.py`).
  - **keep:** yes

- **`pa_batch_bc_exit_diagnostics_v2/`**
  - **purpose:** exit / **0.02** slippage stress on **tuned v2 strict** candidates (`pa_exit_diagnostics.py`).
  - **keep:** yes

- **`layer1_pa_batch_a_tuned_qqq_2023_2024_v1/`**
  - **status:** PA Batch A **tuned grids v1** Layer 1 (QQQ 2023–01–01 → 2024–12–31)
  - **purpose:** `*_tuned_v1.yaml` sweeps → **10** strict YAMLs (trading-range + failed-trap); `signal_rate_diagnosis.*`, `layer1_pa_batch_a_tuned_v1_summary.md`
  - **decision:** **`PROCEED_TO_PA_BATCH_A_REDUCED_LAYER2_DESIGN`**; design sketch `reduced_layer2_pa_batch_a_tuned_design.md`
  - **Layer 2:** executed reduced Layer 2 under `src/combiner/results/layer2_qqq_pa_batch_a_tuned_2023_2024_v1/` → decision **`TUNE_PA_BATCH_A_GRIDS_AGAIN`** (cost stress @ 0.02 fails for core)
  - **keep:** yes

- **`layer1_pa_batch_a_qqq_2023_2024/`**
  - **status:** formal PA Batch A Layer 1 (QQQ 2023–01–01 → 2024–12–31)
  - **purpose:** focused sweeps → `sweep_manifest.*` → strict `select_candidates` (**4** YAMLs, `pa_failed_range_breakout_trap` only) + optional `diagnostic_relaxed_selection/` + `signal_rate_diagnosis.*` + `candidate_fast_context_check.*`
  - **decision:** **`TUNE_PA_BATCH_A_GRIDS_FIRST`** (`layer1_pa_batch_a_summary.md`). **PA Layer 2 / mini-WFO / full WFO not run.**
  - **keep:** yes

- **`layer1_all10_qqq_2020_20260430_posthardening_v1/`**
  - **status**: active baseline
  - **window**: 2020‑01‑01 → 2026‑04‑30
  - **purpose**: post-hardening Layer 1 manifest + selected candidate YAML library
  - **keep**: yes

- **`layer1_all10_qqq_2025_20260430_posthardening_v1/`**
  - **status**: active baseline (recent window)
  - **window**: 2025‑01‑01 → 2026‑04‑30
  - **purpose**: recent Layer 1 manifest + selected candidates
  - **keep**: yes

- **`layer1_v2_batch1_qqq_2023_2024/`**
  - **status**: active Strategy Library v2 Batch 1 Layer 1
  - **window**: 2023‑01‑01 → 2024‑12‑31
  - **purpose**: six-strategy capped sweeps → **20** selected YAMLs; manifest + `MANIFEST_CONSISTENCY_NOTE.md`
  - **Layer 2 follow-up:** `src/combiner/results/layer2_qqq_v2_batch1_2023_2024/layer2_v2_batch1_summary.md`
  - **keep**: yes

- **`layer1_v2_batch1_tuned_qqq_2023_2024_v1/`**
  - **status**: active Batch 1 **tuned** Layer 1 (squeeze + RSI only)
  - **window**: 2023‑01‑01 → 2024‑12‑31
  - **purpose**: tuned grids → **10** selected YAMLs; `sweep_manifest.*` + selection docs
  - **Layer 2 follow-up:** `src/combiner/results/layer2_qqq_v2_batch1_tuned_2023_2024_v1/layer2_v2_batch1_tuned_summary.md`
  - **keep**: yes

- **`batch1_cost_fragility_diagnostics_v1/`**
  - **status**: reference diagnostics pack (original Batch 1 Layer 2 cost attribution)
  - **keep**: yes (CSV + MD summaries only)

- **`strategy_library_v2_batch1_tuning_summary.md`**
  - **status**: Batch 1 tuning v1 narrative + decision (`TUNE_BATCH1_GRIDS_AGAIN`)
  - **keep**: yes

- **`strategy_library_v2_batch1_tuning_v2_summary.md`**
  - **status**: Batch 1 tuning v2 narrative + **`DEFER_BATCH1_AND_RETURN_TO_REFINED_FAILED_CORE`**
  - **keep**: yes

- **`layer1_v2_batch1_tuned_v2_qqq_2023_2024/`**
  - **status**: tuned_v2 Layer 1 manifest only (**no** `selected_candidates/*.yaml`)
  - **window**: 2023‑01‑01 → 2024‑12‑31
  - **keep**: yes (manifest + selection docs)

- **`batch1_tuned_v1_cost_diagnostics/`**
  - **status**: tuned_v1 winner trade-quality / bucket diagnostics
  - **keep**: yes

- **`layer2_v2_completion_tuning_plan.md`**, **`layer2_v2_completion_toxic_path_diagnosis.md`** (+ `.csv`)
  - **status**: Layer 2 v2 completion **tuned v1** planning + toxic-path diagnosis (QQQ 2023–2024)
  - **keep**: yes

- **`strategy_library_v2_completion_summary.md`** (+ `strategy_library_v2_completion_*.{md,csv}`)
  - **status**: Strategy Library v2 **completion** pack (9 new plugins + feature deltas + Jan smoke health)
  - **keep**: yes (no heavy sweep outputs)

- **`layer1_v2_completion_qqq_2023_2024/`**
  - **status**: Layer 1 **completion** QQQ 2023–2024 (nine strategies; full focused grids; manifest + **30** selected YAMLs)
  - **window**: 2023‑01‑01 → 2024‑12‑31
  - **purpose**: economics + candidate library for v2 completion track; summary `layer1_v2_completion_summary.md`
  - **Layer 2 follow-up:** `src/combiner/results/layer2_qqq_v2_completion_2023_2024/layer2_v2_completion_summary.md` (run plan `reduced_layer2_v2_completion_run_plan.md`; design `reduced_layer2_v2_completion_design.md`); **tuned v1** `src/combiner/results/layer2_qqq_v2_completion_tuned_v1_2023_2024/layer2_v2_completion_tuned_v1_summary.md` (plan `layer2_v2_completion_tuning_plan.md`; toxic-path diagnosis `layer2_v2_completion_toxic_path_diagnosis.md`); **tuned v2 high-trade** `src/combiner/results/layer2_qqq_v2_completion_tuned_v2_high_trade_2023_2024/layer2_v2_completion_tuned_v2_high_trade_summary.md` (plan `layer2_v2_completion_tuned_v2_high_trade_plan.md`)
  - **keep**: yes

- **`layer2_v2_completion_tuned_v2_high_trade_plan.md`**
  - **status**: tuned v2 high-trade rerank plan + gates
  - **keep**: yes

## B. Reference / engineering docs

- **Repo maintenance (2026-05-09):** `repo_maintenance_formatting_summary.md` (formatting-only pass; no source edits)
- **Research script audit:** `research_script_organization_audit.md` / `research_script_organization_audit.csv`
- **Testing grid index:** `src/strategies/testing_parameters/GRID_INDEX.md`
- **Hardening docs**: `hardening_*`, `rerun_plan_after_hardening.md`, `PRE_HARDENING_STALE.md` markers
- **Engineering summaries (Layer 2):**
  - `layer2_precompute_cleanup_plan.md`, `layer2_precompute_cleanup_summary.md`
  - `layer2_signal_cache_summary.md`
  - `feature_store_v1_plan.md`, `feature_store_v1_summary.md`
- **Pre‑Layer‑3 gate docs:**
  - `pre_layer3_cache_benchmark_plan.md`
  - `pre_layer3_cache_benchmark_comparison.csv`
  - `pre_layer3_cache_benchmark_summary.md`
  - `pre_layer3_cache_benchmark_full_summary.md` (may be SKIPPED if local benchmark outputs weren’t retained)
  - `pre_layer3_gate_readiness_summary.md`
- **Data coverage docs:** `data_backfill_spy_qqq_2020_20260430/` (SPY incomplete; QQQ is the research symbol)

## C. Removed from repository (2026-05-10)

The following **stale** roots were deleted from the working tree (see `repo_cleanup_summary.md`); use **post-hardening** replacements in §A–B:

- **`layer1_all10_qqq_2020_20260430_v1/`** — pre-hardening (`PRE_HARDENING_STALE.md`) → **`layer1_all10_qqq_2020_20260430_posthardening_v1/`**
- **`layer1_all10_qqq_v1/`** — legacy (`STALE.md`) → **`layer1_all10_qqq_*_posthardening_v1/`**

## D. Stale / superseded (historical index only — paths above removed 2026-05-10)

The bullets below describe **what these roots were** before removal; they are **not** present in the repo anymore:

- **`layer1_all10_qqq_2020_20260430_v1/`**
  - **status**: stale (pre-hardening)
  - **marker**: included `PRE_HARDENING_STALE.md`
  - **replacement**: `layer1_all10_qqq_2020_20260430_posthardening_v1/`

- **`layer1_all10_qqq_v1/`**
  - **status**: legacy seed baseline (pre post-hardening reruns)
  - **replacement**: post-hardening 2020/2025 roots

## Notes

- **Do not delete** `selected_candidates/*.yaml` or curated summaries.
- Heavy sweep folders are intentionally gitignored elsewhere; this folder contains curated artifacts and docs.

