# Global research summary v2 (QQQ 2023–2024, post feature hardening)

## 1. Purpose

Re-validate global research artifacts after **`51bfe17`** (feature construction performance) without changing strategy logic: audit → Layer 1 sweep → diversity → Layer-2-ready core → Layer 2 design.

## 2. Feature-performance verification

- Benchmark: `src/research/results/feature_build_performance_v2/verify_after/feature_build_benchmark.csv` — **fragmentation_warnings_count = 0** for failed_orb, afternoon_continuation, PA configs.
- Note: `src/research/results/feature_build_performance_v2/feature_warning_verify.md`.

## 3. Global strategy audit

- **Root:** `src/research/results/global_strategy_audit_v2/`
- **Strategies audited:** 35 (same universe as v1).
- **Runnable (READY_* and grid ≤1500):** 30 sweeps executed; **5** skipped (audit status or grid >1500).

## 4. Global Layer 1 v2 results

- **Root:** `src/research/results/layer1_global_qqq_2023_2024_v2/`
- **Tag:** `layer1_global_qqq_2023_2024_v2`
- **Manifest rows (runnable sweeps):** 30 completed; see `sweep_manifest.csv` / `skipped_strategies.csv`.
- **Strict selected YAMLs:** **81** (`selected_candidates/`, `selected_candidates.csv`).
- **Distinct strategies (strict):** 17.
- **Distinct families (strict):** 15.
- **Fast-context:** exit code **0** (`fast_context_check.*`).
- **Console log (local, not committed):** `run_console.log` in the same folder.

## 5. Full selected root vs Layer2-ready core

| Root | YAML count | Role |
|------|------------|------|
| `selected_candidates/` | 81 | Research-complete strict export |
| `selected_candidates_l2_core/selected_candidates/` | 66 | Prerun cap + hash-aware subset for Layer 2 |

## 6. Candidate diversity

- **Full:** `src/research/results/global_candidate_signal_diversity_qqq_2023_2024_v2/`
- **l2_core:** `src/research/results/global_candidate_signal_diversity_l2_core_qqq_2023_2024_v2/`

## 7. Side support / short candidates

- **Strict l2_core:** **0** rows with `n_short_signals > 0` in merged diversity (QQQ 2023–2024 fingerprint window).
- **`long_short_mixed`** bucket omitted from sweep grid (no synthetic shorts).

## 8. Global branch leaderboard

- `src/research/results/global_branch_leaderboard_v2.csv` (+ `.md`) — built with `src/research/build_global_branch_leaderboard_v2.py` (manifest + full vs l2_core counts + duplicate ratio).

## 9. Global Layer 2 design

- `src/research/results/global_layer2_qqq_2023_2024_v2_design.md`
- Configs: `src/combiner/configs/layer2_qqq_global_2023_2024_v2.yaml`, `layer2_sweep_qqq_global_2023_2024_v2.yaml`

## 10. Global Layer 2 run result

- **Full 2023–2024 sweep:** not run in this change set.
- **Diagnostics-only smoke (Q1 2023):** see `layer2_global_diagnostics_smoke_q1_2023.md`; heavy CSV/JSON under `src/combiner/results/layer2_qqq_global_2023_2024_v2/diagnostics/` is **local-only** per artifact policy.

## 11. Decision

- **`PROCEED_TO_GLOBAL_LAYER2_SWEEP`** on l2_core when time budget allows (configs + gates OK).
- Automated **full-root** prerun gate remains **NO** (81 > 80) — informational only once l2_core exists.

## 12. Explicit non-runs

- mini-WFO, full WFO, live/paper, SPY.

## 13. Next step

Run **`python -m src.combiner.sweep`** with `layer2_sweep_qqq_global_2023_2024_v2.yaml` and `--candidate-root` = l2_core `selected_candidates`, **2023–2024** window, signal cache if desired; postprocess for cost stress / behavior dedupe. Do **not** use the 81-YAML full root for Layer 2 prerun without raising the cap or trimming.
