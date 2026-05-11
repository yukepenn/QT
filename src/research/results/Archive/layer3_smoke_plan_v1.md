# Layer 3 smoke plan v1 — implemented (fixed-system smoke only)

**Implementation (smoke):** `src/walkforward/` (runner, folds YAML, frozen configs under `src/combiner/configs/frozen/`). Curated results example: `src/walkforward/results/layer3_smoke_v1_qqq_fixed_systems/`.

**Implementation (component diagnosis v1):** frozen YAMLs under `src/combiner/configs/frozen/diagnosis/`, config `src/walkforward/configs/qqq_fixed_system_diagnosis_v1.yaml`, curated aggregates under `src/walkforward/results/layer3_smoke_v1_diagnosis_qqq_components/` (`layer3_smoke_diagnosis_summary.md`, comparison CSVs).

This document retains the **original design intent** for smoke vs full Layer 3 WFO.

## Mini-WFO v1 (implemented)

**Single causal split** (train-only selection, one held-out test): `src/walkforward/mini_wfo.py` with `src/walkforward/configs/qqq_mini_wfo_2023_2024_train_2025_202604_test_v1.yaml`. Produces its own Layer 1 manifest + `MINIWFO_*` candidate YAMLs, train-only Layer 2 sweep (heavy `sweep_*` local, gitignored), `frozen_system/selected_frozen_system.yaml`, and test CSV/MD under `src/walkforward/results/layer3_mini_wfo_qqq_2023_2024_train_2025_202604_test_v1/`. This is **not** multi-fold WFO and **not** the same as smoke v1 (no pre-pinned frozen systems from prior research roots for selection).

---

# Layer 3 smoke plan v1 (historical header — design intent)

## 1. Purpose

Run a **minimal out-of-sample smoke** to validate that a *fixed* Layer 2 system has reasonable behavior when evaluated on unseen periods. This is **not** a walk-forward optimization and **not** a profitability claim.

## 2. Candidate fixed systems to smoke

### A. `trap_family` top-1 (recent + full-history strong)

Candidates (typical top‑1 trio):

- `FAILED_ORB_001`
- `GAP_ACCEPTANCE_FAILURE_001`
- `PRIOR_DAY_LEVEL_TRAP_001`

Rationale: simple, consistently present in baselines, strong recent-window performance, and positive full-history in-sample.

### B. `opening_family` top-1 (tests ORB momentum/retest contribution)

Typical candidates:

- `FAILED_ORB_001`
- `GAP_ACCEPTANCE_FAILURE_001`
- `ORB_CONTINUATION_001`
- `ORB_RETEST_CONTINUATION_001`

Rationale: checks whether adding ORB continuation/retest improves robustness relative to the trap trio.

## 3. Suggested folds (example)

Use a small number of 1-year-ish test segments:

1. Train: 2020‑01‑01 → 2022‑12‑31, Test: 2023‑01‑01 → 2023‑12‑31  
2. Train: 2021‑01‑01 → 2023‑12‑31, Test: 2024‑01‑01 → 2024‑12‑31  
3. Train: 2022‑01‑01 → 2024‑12‑31, Test: 2025‑01‑01 → 2026‑04‑30  

## 4. What to freeze in the smoke

- **No** Layer 1 re-sweep per fold initially.
- **No** Layer 2 grid sweep per fold initially.
- Start with **fixed candidate systems** and **fixed combiner constraints**.
- Later (full Layer 3): rerun Layer 1 + candidate selection + Layer 2 inside each train fold (explicitly out of scope for smoke v1).

## 5. Metrics to track

- trades, total_r
- profit_factor / profit_factor_r (if present in summaries)
- max_drawdown_r
- cost stress at slippage 0.02
- monthly/quarterly breakdown consistency
- daily trade number profile (if exported)

## 6. Explicit non-goals

- No live trading, no broker integration
- No broad parameter search in the smoke
- No “best fold” selection beyond reporting

## 7. Gate for proceeding beyond smoke

Proceed only if the fixed system:

- is positive (or at least not clearly negative) on OOS tests,
- remains reasonable under 0.02 slippage/share,
- does not rely on a single test segment,
- has drawdown and trade behavior consistent with research constraints.

