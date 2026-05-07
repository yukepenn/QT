# Pre‑Layer‑3 gate readiness summary

## 1. Current status

- Hardening A/B/C/D/E: **complete**
- Layer 1 baseline runs: **complete**
- Layer 2 precompute cleanup + observability: **complete**
- Layer 2 persistent signal cache: **complete**
- FeatureStore v1: **complete**
- Project status / config index / results index / artifact policy: **complete**
- Artifact cleanup + cache benchmark: **complete**
- Layer 3: **not implemented** (intentionally deferred)

## 2. Active baselines (roots)

- Layer 1 2020: `src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1/`
- Layer 1 2025: `src/research/results/layer1_all10_qqq_2025_20260430_posthardening_v1/`
- Layer 2 2020 strict: `src/combiner/results/layer2_qqq_2020_20260430_posthardening_strict_v1/`
- Layer 2 2020 relaxed: `src/combiner/results/layer2_qqq_2020_20260430_posthardening_relaxed_v1/`
- Layer 2 2025 recent: `src/combiner/results/layer2_qqq_2025_20260430_recent_check_v1/`

## 3. Artifact gate

- **Heavy generated artifacts untracked / removed locally**: `equity.csv`, `trades.csv`, `top_runs/`, `run_*`, `sweep_*`, logs.
- `.gitignore` blocks future heavy outputs under both:
  - `src/combiner/results/**`
  - `src/research/results/**`
- Curated sanity check: `src/research/results/curated_artifact_sanity_check.md` (**PASS**).
- Regenerated active Layer 2 diagnostics summaries:
  - `diagnostics/diagnostics_summary.md` now present in all active Layer 2 roots.

## 4. Cache benchmark gate (Layer 2 recent)

Benchmark window: QQQ 2025‑01‑01 → 2026‑04‑30

- sweep wall time:
  - cache_off: **~483.25s**
  - cache_on_cold: **~331.81s**
  - cache_on_warm: **~232.82s**
- signal cache hits/misses (40 candidates):
  - off: **0 / 40**
  - cold: **0 / 40**
  - warm: **40 / 0**
- equality gate: **PASS** (top_unique first row equal within tol=1e‑6; behavior first row equal).
- full top‑20 / cost‑stress comparison: **SKIPPED** (benchmark curated CSVs not retained locally); see `pre_layer3_cache_benchmark_full_summary.md`.

## 5. Research gate (no overclaim)

Recent window leader (in-sample; not live-ready claim):

- `trap_family` top‑1
- trades: **323**
- total_r: **69.057**
- PF: **1.516**
- maxDD_r: **‑12.082**

Full-history baselines remain more authoritative than the recent-window check.

## 6. Remaining caveats

- SPY is incomplete and not used here.
- Recent window is still in-sample.
- Layer 3 is intentionally deferred; no walk-forward tooling added here.

## 7. Recommendation

Pre‑Layer‑3 gate is **ready**. Next step should be a **small Layer 3 smoke** only after explicit approval:

- A. `trap_family` top‑1
- B. `opening_family` top‑1

Smoke should be **fixed-system**, minimal folds, and focused on process/consistency—not profitability claims.

