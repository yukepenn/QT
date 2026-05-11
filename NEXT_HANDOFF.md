# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Latest commit before this work | `1ab2da1` — Docs(handoff): record feature perf commit |
| New commit | **Run global Layer 1 after feature hardening** — authoritative SHA: `git rev-parse HEAD` on `main` after pull |
| Push status | **Pushed** `main` → `origin` (`1ab2da1..2ad74fe`) |
| Working tree | Expected clean except **untracked** `src/strategies/testing_parameters_results/**` (Layer 1 v2 sweeps), `src/combiner/results/layer2_qqq_global_2023_2024_v2/diagnostics/` (Q1 smoke), `run_console.log` under `layer1_global_qqq_2023_2024_v2/` (do not stage) |

## B. Task scope

| | |
|--|--|
| Requested | Post–feature-hardening Global L1 v2, audit v2, diversity v2, l2_core root, leaderboard, Layer 2 design/configs, feature warning verify, docs/indexes; **no** mini/full WFO/live; **no** `git add .` |
| Completed | Audit v2; full `run_global_layer1.py` v2 (30 sweeps, 81 strict YAMLs); diversity full + l2_core; `create_layer2_candidate_core.py` (66); `emit_global_layer2_v2_configs.py`; combiner base+sweep YAML; `build_global_branch_leaderboard_v2.py`; Q1 combiner diagnostics smoke (local heavy artifacts); `feature_build_performance_v2/verify_after` + `feature_warning_verify.md`; runner/audit/fast-context CLI improvements; summaries `global_research_summary_v2.md`, `global_layer2_qqq_2023_2024_v2_design.md`, `global_layer2_gate_decision_v2.md`, `layer2_global_diagnostics_smoke_q1_2023.md` |
| Intentionally not done | **Full** Global Layer 2 **2023–2024** sweep + postprocess in repo (time + artifact policy); mini-WFO; full WFO; live/paper; SPY |

## C. Files changed

| Area | Paths |
|------|-------|
| Research scripts | `src/research/run_global_layer1.py`, `global_strategy_audit.py`, `check_selected_candidates_fast_context.py`, `create_layer2_candidate_core.py`, `emit_global_layer2_v2_configs.py`, `build_global_branch_leaderboard_v2.py` |
| Combiner configs | `src/combiner/configs/layer2_qqq_global_2023_2024_v2.yaml`, `layer2_sweep_qqq_global_2023_2024_v2.yaml` |
| Research results | `src/research/results/global_strategy_audit_v2/**`, `layer1_global_qqq_2023_2024_v2/**` (exclude staging `run_console.log`), `global_candidate_signal_diversity_qqq_2023_2024_v2/**`, `global_candidate_signal_diversity_l2_core_qqq_2023_2024_v2/**`, `global_branch_leaderboard_v2.{csv,md}`, `global_research_summary_v2.md`, `global_layer2_qqq_2023_2024_v2_design.md`, `global_layer2_gate_decision_v2.md`, `layer2_global_diagnostics_smoke_q1_2023.md`, `feature_build_performance_v2/**` |
| Docs / indexes | `README.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `NEXT_HANDOFF.md`, `src/research/results/RESULTS_INDEX.md`, `src/combiner/configs/CONFIG_INDEX.md`, `src/combiner/results/RESULTS_INDEX.md` |
| Local-only heavy | `src/strategies/testing_parameters_results/**` (v2 tag sweeps); `src/combiner/results/layer2_qqq_global_2023_2024_v2/diagnostics/*` (precompute profile, feature_store_stats) |

## D. Validation

| Check | Result |
|--------|--------|
| `pytest -q` | **374 passed** |
| `compileall` | **OK** |
| `loader.py --list` | **35** strategies |
| Parity | **failed_orb**, **afternoon_continuation**, **pa_buy_sell_close_trend** tuned v3, **pa_climax_reversal** tuned v3 — `TOTAL_MISMATCH_FIELDS approx=0` |
| Feature warning | Benchmark `fragmentation_warnings_count=0` (see `feature_build_performance_v2/verify_after/`); sweep smoke `feature_perf_verify_phase` — **no** `PerformanceWarning` / fragmentation lines in filtered log |
| Boundary greps | LOOKAHEAD / `_feat_key` — same policy as prior (markdown hits under `src/research/results` allowed) |
| Tracked `*.py` under `src/research/results` | **None** |

## E. Research results

| Metric | Value |
|--------|--------|
| Audit strategies | **35** |
| Runnable sweeps (L1 v2) | **30** completed |
| Skipped (audit / grid) | **5** (see `skipped_strategies.csv`) |
| Strict YAMLs (full root) | **81** |
| l2_core YAMLs | **66** (≤ 80) |
| Distinct families (strict) | **15** |
| Short-side fingerprint strict (`n_short_signals>0`) | **0** |
| Diversity (full) | `global_candidate_signal_diversity_qqq_2023_2024_v2/` — exit **0** |
| Fast-context (full + l2_core) | exit **0** |
| Automated L2 prerun gate (full 81-YAML root) | **NO** (81 > 80) |
| Manual L2 input gate (l2_core) | **YES** |
| Layer 2 full sweep | **Not run** (configs + Q1 diagnostics smoke only) |
| **Decision** | **`PROCEED_TO_GLOBAL_LAYER2_SWEEP`** on **l2_core** when ready (672-combo grid in `layer2_sweep_qqq_global_2023_2024_v2.yaml`) |

## F. Explicit non-runs

- mini-WFO, full WFO, live/paper, SPY  
- Committing `testing_parameters_results/**`, combiner diagnostics heavy files, `run_console.log`

## G. Risks / caveats

- In-sample QQQ 2023–2024 only; not live-ready.  
- Full strict export still **81** YAMLs — use **l2_core** for Layer 2 to satisfy historical ≤80 prerun convention.  
- `opening_trap_core` bucket omits `prior_day_level_trap` / `orb_retest_continuation` when absent from l2_core (expected).  
- Several branches flagged **DEFER_COST_FRAGILE** / **DEFER_DUPLICATE_ONLY** on leaderboard heuristics — review before productionizing.

## H. Recommended next step

**Exactly one:** run **`python -m src.combiner.sweep`** with `src/combiner/configs/layer2_sweep_qqq_global_2023_2024_v2.yaml`, `--candidate-root` = `src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates`, window **2023-01-01 → 2024-12-31**, optional signal cache; then cost-stress + behavior dedupe postprocess — keep heavy artifacts local per `ARTIFACT_POLICY.md`.
