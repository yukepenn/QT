# PROJECT_STATUS (handoff)

## 1. Purpose

QT is a **local, in-sample intraday strategy research framework** centered on **QQQ** 1‑minute RTH bars.

- **Layer 1:** per-strategy parameter sweeps → candidate library (`selected_candidates/*.yaml`).
- **Layer 2:** combiner/router that evaluates candidate sets under simple system constraints (currently **max_open_positions=1**).
- **Layer 3:** planned walk-forward / OOS harness (not implemented in this phase).

**Non-goals:** live trading, broker execution, portfolio optimizer, ML pipelines, SPY robustness, or profitability claims.

## 2. Current architecture (high level)

- **Raw data:** local only under `data/raw/` (gitignored).
- **Features:** built from raw bars via `src/features/build_features.py`; **FeatureStore v1** provides in-memory reuse.
- **Strategies:** plugins under `src/strategies/strategy/` implementing fast context path:
  `prepare_signal_context` → `generate_signal_arrays_from_context`.
- **Layer 1 sweep:** `src/backtest/sweep.py` (fast Numba path).
- **Candidate selection:** `src/research/select_candidates.py` exports `selected_candidates/*.yaml`.
- **Layer 2:** `src/combiner/run.py`, `src/combiner/sweep.py`, `src/combiner/postprocess.py`.
- **Engineering accelerators:**
  - **Signal cache (disk):** `.cache/qt/candidate_signals` (gitignored), from `src/combiner/signal_cache.py`.
  - **FeatureStore (memory):** `src/features/feature_store.py`.

## 3. Active research baselines (current)

### Layer 1 (candidate libraries)

- **Active (post-hardening):**
  - `src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1/`
  - `src/research/results/layer1_all10_qqq_2025_20260430_posthardening_v1/`
- **Reference:** `src/research/results/layer1_all10_qqq_2023_20260430_posthardening_v1/`

### Layer 2 (combiner roots)

- **Active (post-hardening 2020):**
  - `src/combiner/results/layer2_qqq_2020_20260430_posthardening_strict_v1/`
  - `src/combiner/results/layer2_qqq_2020_20260430_posthardening_relaxed_v1/`
- **Active (recent-window check):**
  - `src/combiner/results/layer2_qqq_2025_20260430_recent_check_v1/`
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
- Layer 3 smoke plan (doc only): `src/research/results/layer3_smoke_plan_v1.md`

## 7. Next intended phases

1. Keep this repo hygiene / indexing work mergeable.
2. Draft and review **Layer 3 smoke** plan (already documented), then implement only with explicit approval.

