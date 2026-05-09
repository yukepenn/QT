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

### Strategy Library v2 Batch 1 — reduced Layer 2 (QQQ 2023–2024)

- **`layer2_qqq_v2_batch1_2023_2024.yaml`**
  - **window**: 2023‑01‑01 → 2024‑12‑31
  - **candidate_root**: `src/research/results/layer1_v2_batch1_qqq_2023_2024/selected_candidates`
  - **purpose**: Batch 1 only (RSI + squeeze strict; fade + exhaustion relaxed/diagnostic); MA/Donchian excluded (no Layer 1 YAMLs)
- **`layer2_sweep_qqq_v2_batch1_2023_2024.yaml`**
  - **base_config**: YAML above
  - **grid**: 1296 combos
  - **results**: `src/combiner/results/layer2_qqq_v2_batch1_2023_2024/layer2_v2_batch1_summary.md`

### Strategy Library v2 Batch 1 — tuned reduced Layer 2 (QQQ 2023–2024)

- **`layer2_qqq_v2_batch1_tuned_2023_2024_v1.yaml`**
  - **window**: 2023‑01‑01 → 2024‑12‑31
  - **candidate_root**: `src/research/results/layer1_v2_batch1_tuned_qqq_2023_2024_v1/selected_candidates`
  - **purpose**: cost-aware **tuned** strict Batch 1 (squeeze + RSI only)
- **`layer2_sweep_qqq_v2_batch1_tuned_2023_2024_v1.yaml`**
  - **base_config**: YAML above
  - **grid**: 192 combos
  - **results**: `src/combiner/results/layer2_qqq_v2_batch1_tuned_2023_2024_v1/layer2_v2_batch1_tuned_summary.md`

**Tuned v2:** `bollinger_squeeze_breakout_tuned_v2.yaml` exists for a stricter squeeze grid; **no** Layer 2 YAMLs were added in this phase because Layer 1 candidate export was **empty** (see `strategy_library_v2_batch1_tuning_v2_summary.md`).

## C. Frozen configs (Layer 3 smoke / fixed-system evaluation only)

Directory: **`src/combiner/configs/frozen/`**

- Research snapshots that pin **candidate IDs**, combiner knobs, and provenance (`source.layer1_root`, `source.layer2_root`).
- Consumed by **`src/walkforward/runner.py`** for temporal-stability smoke — **not** live deployment configs.
- Example files: `qqq_trap_family_recent_top1.yaml`, `qqq_opening_family_recent_top1.yaml`, `qqq_full_history_opening_pair.yaml`.

## D. Frozen diagnosis (`frozen/diagnosis/` — component smoke only)

Directory: **`src/combiner/configs/frozen/diagnosis/`**

- **Status:** diagnostic-only YAMLs for Layer 3 **component** runs (`walkforward` diagnosis config).
- **Not** active trading configs; **not** live configs.
- Decompose trap/opening families into single candidates, pairs, MTD variants, and full-history contrasts.

## E. Layer 3 mini-WFO (`src/walkforward/configs/` — causal split harness)

- **Status:** `mini_wfo.py` driver only — generates train-local Layer 2 base/sweep YAMLs under the run’s `train_layer2/` tree; not a default Layer 2 research baseline (use sections A–B for that).
- **Example:** `qqq_mini_wfo_2023_2024_train_2025_202604_test_v1.yaml` — QQQ train 2023–2024 / test 2025–2026, narrowed strategy family, fixed 288-combo grid.

## F. Legacy / deprecated (do not use for new decisions)

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

