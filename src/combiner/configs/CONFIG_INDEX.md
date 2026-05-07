# Layer 2 config index

This index classifies `src/combiner/configs/*.yaml` without changing YAML contents.

## A. Active / current (safe defaults for new work)

### Post-hardening 2020–2026 (primary baseline)

- **`layer2_qqq_2020_20260430_posthardening_strict.yaml`**
  - **window**: 2020‑01‑01 → 2026‑04‑30
  - **candidate_root**: `src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1/selected_candidates`
  - **purpose**: strict combiner constraints baseline
  - **use**: yes (current baseline)
- **`layer2_sweep_qqq_2020_20260430_posthardening_strict.yaml`**
  - **base_config**: the strict config above
  - **purpose**: strict grid sweep

- **`layer2_qqq_2020_20260430_posthardening_relaxed.yaml`**
  - **window**: 2020‑01‑01 → 2026‑04‑30
  - **candidate_root**: `src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1/selected_candidates`
  - **purpose**: relaxed combiner constraints baseline
  - **use**: yes (current baseline)
- **`layer2_sweep_qqq_2020_20260430_posthardening_relaxed.yaml`**
  - **base_config**: the relaxed config above
  - **purpose**: relaxed grid sweep

### Recent-window check (sanity baseline)

- **`layer2_qqq_2025_20260430_recent_check_v1.yaml`**
  - **window**: 2025‑01‑01 → 2026‑04‑30
  - **candidate_root**: `src/research/results/layer1_all10_qqq_2025_20260430_posthardening_v1/selected_candidates`
  - **purpose**: recent-window stability check + quick equivalence runs
  - **use**: yes
- **`layer2_sweep_qqq_2025_20260430_recent_check_v1.yaml`**
  - **base_config**: recent-check config above
  - **purpose**: smaller/targeted recent grid sweep (still 2688 combos; run sparingly)

## B. Reference / historical (keep for comparison; not the default)

- **`layer2_qqq_2023_20260430_posthardening_strict.yaml`** (+ sweep)
  - **window**: 2023‑01‑01 → 2026‑04‑30
  - **candidate_root**: `src/research/results/layer1_all10_qqq_2023_20260430_posthardening_v1/selected_candidates`
  - **purpose**: historical reference run
- **`layer2_qqq_2023_20260430_posthardening_relaxed.yaml`** (+ sweep)
  - same window/candidate root, relaxed reference

## C. Frozen configs (Layer 3 smoke / fixed-system evaluation only)

Directory: **`src/combiner/configs/frozen/`**

- Research snapshots that pin **candidate IDs**, combiner knobs, and provenance (`source.layer1_root`, `source.layer2_root`).
- Consumed by **`src/walkforward/runner.py`** for temporal-stability smoke — **not** live deployment configs.
- Example files: `qqq_trap_family_recent_top1.yaml`, `qqq_opening_family_recent_top1.yaml`, `qqq_full_history_opening_pair.yaml`.

## D. Legacy / deprecated (do not use for new decisions)

- **`layer2_qqq_2020_20260430_v2_relaxed.yaml`** (+ sweep)
  - **candidate_root**: `src/research/results/layer1_all10_qqq_2020_20260430_v1/selected_candidates`
  - **status**: **pre-hardening** candidate root (see `PRE_HARDENING_STALE.md`)
  - **replacement**: post-hardening 2020 strict/relaxed configs above

- **`layer2_qqq_v1.yaml`** (+ sweep)
  - **candidate_root**: `src/research/results/layer1_all10_qqq_v1/selected_candidates`
  - **status**: legacy baseline / recovery template
  - **replacement**: post-hardening 2020/2025 configs

- **`orb_vwap_simple.yaml`**
  - **status**: early prototype / reference only
  - **replacement**: use post-hardening configs and candidate families

