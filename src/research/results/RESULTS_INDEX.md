# Research results index (`src/research/results/`)

This index classifies **result roots** without moving or deleting them.

## A. Active / current

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

## B. Reference / engineering docs

- **Hardening docs**: `hardening_*`, `rerun_plan_after_hardening.md`, `PRE_HARDENING_STALE.md` markers
- **Engineering summaries (Layer 2):**
  - `layer2_precompute_cleanup_plan.md`, `layer2_precompute_cleanup_summary.md`
  - `layer2_signal_cache_summary.md`
  - `feature_store_v1_plan.md`, `feature_store_v1_summary.md`
- **Data coverage docs:** `data_backfill_spy_qqq_2020_20260430/` (SPY incomplete; QQQ is the research symbol)

## C. Stale / superseded (keep for history; do not use for new decisions)

- **`layer1_all10_qqq_2020_20260430_v1/`**
  - **status**: stale (pre-hardening)
  - **marker**: includes `PRE_HARDENING_STALE.md`
  - **replacement**: `layer1_all10_qqq_2020_20260430_posthardening_v1/`

- **`layer1_all10_qqq_v1/`**
  - **status**: legacy seed baseline (pre post-hardening reruns)
  - **replacement**: post-hardening 2020/2025 roots

## Notes

- **Do not delete** `selected_candidates/*.yaml` or curated summaries.
- Heavy sweep folders are intentionally gitignored elsewhere; this folder contains curated artifacts and docs.

