# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Main research anchor (Layer3 complete smoke chain) | **`8f910a2693612fa433aab863de5af5fd03abf9ae`** — `Research(layer3): run optional smoke ablations` (merged CORE+optional; decision **`PROCEED_TO_LAYER3_EXPANDED_STABILITY_DESIGN`**) |
| Layer3 CORE-only smoke (historical) | **`1735f42493bd40101e8961b9f74f04083ce3edca`** — `Research(layer3): run fixed profile core smoke` |
| Repo tip (this handoff) | **`Research(layer3): run expanded stability review`** — after committing/pushing this handoff, canonical execution SHA is **`git rev-parse HEAD`** on a clean `main` (parent design tip was **`f4741a9557d65e54d6a47e62819ea822289bfb0a`** — `Research(layer3): design expanded stability`). |
| Push status | Run **`git push origin main`** after staging this commit; verify **`git ls-remote origin refs/heads/main`** matches local **`HEAD`**. |
| Working tree | Curated **`layer3_expanded_stability_v1/**`** tracked; expect **untracked** `layer3_*/*/local_runs/**`, `local_configs/**`, combiner scratch. **Do not** `git add .`. |
| Expected untracked local-only | `local_runs/**`, `.cache/qt/candidate_signals/**`, `sweep_*`, `top_runs/`, heavy `src/combiner/results/**` diagnostics |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **455 passed** |
| `python -m src.strategies.loader --list` | **35** strategies |
| Tracked-heavy check | No matches (`git ls-files` vs `top_runs`, raw `trades.csv`, `.parquet`, …) |
| Artifact validation | **`layer3_expanded_stability_v1/layer3_expanded_stability_artifact_validation.*`** — **26** CSVs, **0** parse failures, **0** absolute-path hits; refreshed **`layer3_fixed_profile_smoke_complete_v1/layer3_complete_artifact_validation.*`**; **`layer3_expanded_stability_design_v1/layer3_expanded_stability_design_artifact_validation.*`** |
| ChatGPT bundle (expanded stability) | `src/research/results/layer3_expanded_stability_v1/CHATGPT_REVIEW_BUNDLE.md` |
| Source map (expanded stability) | `src/research/results/layer3_expanded_stability_v1/SOURCE_MAP.csv` |
| Complete smoke bundle (evidence) | `src/research/results/layer3_fixed_profile_smoke_complete_v1/CHATGPT_REVIEW_BUNDLE.md` |

## C. Task scope

| | |
|--|--|
| **Requested** | **Execute** Layer3 **expanded stability review v1** under `layer3_expanded_stability_v1/`: monthly/quarterly/rolling stability, QQQ-derived market context (no calendar hard-labeling), weak-period diagnostics, cost/exit/contribution summaries from curated smoke, gate rollup, ChatGPT bundle — **no** trading rerun by default. |
| **Completed** | `src/research/run_layer3_expanded_stability.py`; `src/research/results/layer3_expanded_stability_v1/**` (incl. manifests, validation, decision); `tests/test_run_layer3_expanded_stability.py`; refreshed validation CSVs; `RESULTS_INDEX.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, **`NEXT_HANDOFF.md`**. |
| **Intentionally not done** | No combiner / Layer3 smoke **re-execution**; no WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global L1; no strategy/feature/selected-candidate YAML/router/short-support changes; no raw trades or `local_runs/**` commits; quarter-sliced exit/candidate tables remain **`REQUIRES_LOCAL_DETAILED_REPLAY`** unless a future local replay is run. |

## D. Input evidence (complete Layer3 smoke recap)

| profile_id | role | early | insample | late | full | maxDD (full) | notes |
|------------|------|------:|---------:|-----:|-----:|-------------:|--------|
| `pa_only_mtp1_meta` | CLEAN_BASELINE | 45.14 | 37.97 | **21.49** | 104.59 | −17.71 | Default clean baseline |
| `pa_gap_mtp2_meta` | DEFAULT_COMBINED | 60.95 | 52.27 | 18.77 | **131.99** | −21.27 | Default combined |
| `primary_mtp2_meta` | BREADTH_BASELINE | 61.33 | 62.70 | **11.86** | **135.89** | −25.09 | Highest full R; weaker late; deeper DD — **reference only** |
| `pa_gap_mtp1_meta` | ABLATION | 54.00 | 45.28 | 18.12 | 117.40 | −22.34 | mtp2 > mtp1 on full |
| `pa_only_mtp2_meta` | ABLATION | 45.14 | 37.97 | 21.49 | 104.59 | −17.71 | ≡ mtp1 in smoke |

**Prior merged-smoke decision:** **`PROCEED_TO_LAYER3_EXPANDED_STABILITY_DESIGN`**. **Design decision:** **`RUN_LAYER3_EXPANDED_STABILITY`**.

## E. Monthly / quarterly / rolling stability (`full_available`)

| profile_id | pos month ratio | worst month R | rolling 3m min | monthly label | pos Q ratio | worst Q | worst Q R | weak Q (<−5) count | quarterly label |
|------------|----------------:|--------------:|---------------:|---------------|------------|---------|----------:|-------------------:|------------------|
| `pa_only_mtp1_meta` | **0.645** | −8.44 | **−11.68** | `POSITIVE_WITH_DRAWDOWN_WARNING` | **0.808** | 2025Q1 | **−11.68** | 3 | `STABLE_POSITIVE` |
| `pa_gap_mtp2_meta` | **0.671** | −9.13 | **−9.76** | `POSITIVE_WITH_DRAWDOWN_WARNING` | **0.769** | 2022Q4 | **−8.80** | 2 | `STABLE_POSITIVE` |
| `primary_mtp2_meta` | — | — | — | *(monthly gates N/A in design for primary)* | **0.692** | 2023Q3 | **−8.58** | **6** | `WEAK_PERIOD_WARNING` |

**Weak-quarter profile PnL (`full_available` quarterly totals, ranks 1 = best in slice):**

| weak_period | best profile (rank 1) | `pa_gap_mtp2_meta` R | `pa_only_mtp1_meta` R | `primary_mtp2_meta` R |
|-------------|----------------------|----------------------:|----------------------:|----------------------:|
| **2025Q1** | `pa_gap_mtp1_meta` | −8.11 (rank 3) | −11.68 (rank 4) | −7.08 (rank 2) |
| **2022Q4** | `pa_only_mtp1_meta` | −8.80 (rank 5) | −5.07 (rank 1) | −6.28 (rank 3) |
| **2023Q3** | `pa_only_mtp1_meta` | −2.64 (rank 4) | +1.61 (rank 1) | −8.58 (rank 5) |

## F. Market context and weak-period diagnosis (QQQ-derived)

| weak_period | QQQ return | assigned `context_label` | confidence |
|-------------|-----------:|---------------------------|--------------|
| **2025Q1** | **−5.32%** | `downtrend_high_vol` | medium |
| **2022Q4** | −1.73% | `unknown_mixed` | low |
| **2023Q3** | −2.92% | `downtrend_low_vol` | medium |

**Weak-period interpretation (heuristic: QQQ quarter return &lt; 0 and key profile PnL &lt; 0 → `MARKET_CONTEXT_ALIGNED`):** **2025Q1**, **2022Q4**, **2023Q3** all classified **`MARKET_CONTEXT_ALIGNED`** in `weak_period_interpretation.md` (see `layer3_expanded_stability_key_findings.csv`). **Gap:** period-sliced **exit-reason** and **candidate contribution** are **not** in curated smoke CSVs → `weak_period_exit_reason.csv` / `weak_period_candidate_contribution.csv` mark **`REQUIRES_LOCAL_DETAILED_REPLAY`** / window-level fallback.

## G. Cost / exits / contribution

| profile_id | `full_available` **target_limit_stress** total R | `published_baseline` total R (full) |
|------------|-----------------------------------------------:|------------------------------------:|
| `pa_only_mtp1_meta` | **+84.22** | +104.59 |
| `pa_gap_mtp2_meta` | **+105.60** | +131.99 |

**Exit mechanics:** window-level shares in `exit_mechanics_summary.csv` (from `complete_exit_reason_summary.csv`) — `max_hold` share **~0.47–0.59** across profiles/windows (**below** the **0.60** warning threshold in evaluated rows). **Contribution:** `candidate_contribution_stability.csv` — GAP adds most in early/insample/full; late_oow GAP slice remains small vs PA (see bundle).

## H. Gate results and risk flags

| Metric | Value |
|--------|------:|
| Gate row evaluations (`expanded_stability_gate_results.csv`) | **78** rows |
| **PASS** | **62** |
| **WARNING** | **5** |
| **NOT_EVALUATED** | **11** |
| **FAIL** | **0** |

**`expanded_stability_profile_labels.csv`:** `pa_only_mtp1_meta`, `pa_gap_mtp2_meta`, `primary_mtp2_meta` → **`EXPANDED_STABILITY_PASS_WITH_WARNINGS`**; `pa_gap_mtp1_meta`, `pa_only_mtp2_meta` → **`EXPANDED_STABILITY_PASS`**.

**Top risks (see `expanded_stability_risk_flags.csv`):** 2025Q1 / 2022Q4 pockets; max_hold dependency; no SPY / no WFO / no live; `full_available` overlap caveat; optional local replay for period exit mix.

## I. Decision (expanded stability execution)

**Exactly one:** **`PROCEED_TO_PRE_WFO_STABILITY_DESIGN`**

- All **hard** window + **target_limit_stress** gates **PASS** for default profiles; **no FAIL** rows in the gate grid.
- Monthly/quarterly tables show **manageable** dispersion with explicit weak quarters; **QQQ context labels** are data-derived (2022Q4 **`unknown_mixed`** — not narrative “chop”).
- **`pa_gap_mtp2_meta`** remains the default combined path on **full-span** economics; **`pa_only_mtp1_meta`** stays the cleaner baseline (e.g. **2022Q4** less negative than PA+GAP).
- **`primary_mtp2_meta`** stays **breadth-only** (quarterly stability **`WEAK_PERIOD_WARNING`**, weaker **late_oow**, deeper DD).
- Period-sliced exit/candidate attribution is **explicitly deferred** (CSV markers) rather than fabricated from window aggregates.

## J. Explicit non-runs and risks

- No combiner replay; no Layer3 smoke re-run; no WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global L1.
- No strategy / feature / selected-candidate YAML / router / production short-support changes.
- **SPY / WFO / live** evidence still absent for production claims.

## K. Files changed

- `src/research/run_layer3_expanded_stability.py`
- `src/research/results/layer3_expanded_stability_v1/**` (curated CSV/MD, bundle, source map, manifests, artifact validation)
- `tests/test_run_layer3_expanded_stability.py`
- `src/research/results/layer3_fixed_profile_smoke_complete_v1/layer3_complete_artifact_validation.*` (refresh)
- `src/research/results/layer3_expanded_stability_design_v1/layer3_expanded_stability_design_artifact_validation.*` (refresh)
- `src/research/results/RESULTS_INDEX.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, **`NEXT_HANDOFF.md`**

## L. Recommended next step

**Exactly one:** **Draft pre-WFO stability design** (checklist + gates + evidence map) using `layer3_expanded_stability_v1/CHATGPT_REVIEW_BUNDLE.md` and companion CSVs; treat optional **local-only** weak-quarter trade replay as a follow-on if period exit/candidate attribution becomes blocking.
