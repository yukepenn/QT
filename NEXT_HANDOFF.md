# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Main research anchor (Layer3 complete smoke chain) | **`8f910a2693612fa433aab863de5af5fd03abf9ae`** — `Research(layer3): run optional smoke ablations` (merged CORE+optional; decision **`PROCEED_TO_LAYER3_EXPANDED_STABILITY_DESIGN`**) |
| Layer3 CORE-only smoke (historical) | **`1735f42493bd40101e8961b9f74f04083ce3edca`** — `Research(layer3): run fixed profile core smoke` |
| Repo tip (this handoff) | **`Research(layer3): design expanded stability`** — canonical SHA is **`git rev-parse HEAD`** on a clean `main` after pull (this push moved `main` forward from `8f910a2`). |
| Push status | **Pushed** to `origin/main` — confirm `git ls-remote origin refs/heads/main` matches local `HEAD` after any further pulls. |
| Working tree | Curated design root **tracked**; expect **untracked** `layer3_*/*/local_runs/**`, `local_configs/**`, combiner scratch. **Do not** `git add .`. |
| Expected untracked local-only | `local_runs/**`, `.cache/qt/candidate_signals/**`, `sweep_*`, `top_runs/`, heavy `src/combiner/results/**` diagnostics |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **446 passed** |
| `python -m src.strategies.loader --list` | **35** strategies |
| Tracked-heavy check | No matches (`git ls-files` vs `top_runs`, raw `trades.csv`, `.parquet`, …) |
| Artifact validation | `layer3_fixed_profile_smoke_complete_v1/layer3_complete_artifact_validation.*` (refresh); **`layer3_expanded_stability_design_v1/layer3_expanded_stability_design_artifact_validation.*`** — **0** parse failures, **0** absolute-path hits in scanned CSVs |
| ChatGPT bundle (design) | `src/research/results/layer3_expanded_stability_design_v1/CHATGPT_REVIEW_BUNDLE.md` |
| Source map (design) | `src/research/results/layer3_expanded_stability_design_v1/SOURCE_MAP.csv` |
| Complete smoke bundle (evidence) | `src/research/results/layer3_fixed_profile_smoke_complete_v1/CHATGPT_REVIEW_BUNDLE.md` |

## C. Task scope

| | |
|--|--|
| **Requested** | **Design-only** Layer3 **expanded stability review v1** from complete smoke evidence: profile scope, weak-period diagnostics (no hard-coded regime names), market-context labels, gates, future run plan + output schema, risks, ChatGPT bundle. |
| **Completed** | `layer3_expanded_stability_design_v1/**`; `tests/test_layer3_expanded_stability_design.py`; indexes + handoff; decision **`RUN_LAYER3_EXPANDED_STABILITY`**. |
| **Intentionally not done** | No **`layer3_expanded_stability_v1/`** execution; no WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global L1; no strategy/feature/selected-candidate YAML/router/short-support changes; no raw trades committed. |

## D. Input evidence (complete Layer3 smoke recap)

| profile_id | role | early | insample | late | full | maxDD (full) | notes |
|------------|------|------:|---------:|-----:|-----:|-------------:|--------|
| `pa_only_mtp1_meta` | CLEAN_BASELINE | 45.14 | 37.97 | **21.49** | 104.59 | −17.71 | Default clean baseline |
| `pa_gap_mtp2_meta` | DEFAULT_COMBINED | 60.95 | 52.27 | 18.77 | **131.99** | −21.27 | Default combined |
| `primary_mtp2_meta` | BREADTH_BASELINE | 61.33 | 62.70 | **11.86** | **135.89** | −25.09 | Highest full R; weaker late; deeper DD — **reference only** |
| `pa_gap_mtp1_meta` | ABLATION | 54.00 | 45.28 | 18.12 | 117.40 | −22.34 | mtp2 > mtp1 on full |
| `pa_only_mtp2_meta` | ABLATION | 45.14 | 37.97 | 21.49 | 104.59 | −17.71 | ≡ mtp1 in smoke |

**Interpretation:** keep **`pa_gap_mtp2_meta`** as default combined; **`pa_only_mtp1_meta`** clean baseline; **`primary_mtp2_meta`** breadth/interpretability only.

## E. Weak-period diagnostic design

| Anchor | Role in design |
|--------|----------------|
| **2025Q1** | Listed in `complete_risk_flags.csv` (`R_2025Q1`) — **starting slice** for diagnostics, **not** a pre-labeled “down market” |
| **2022Q4** | `R_2022Q4` — same rule |
| **Worst months / quarters** | From `worst_month_r` / `worst_quarter_r` and `complete_monthly_summary.csv` / `complete_quarterly_summary.csv` |
| **2023Q3 (`primary_mtp2_meta`)** | Example **data-mined** weak quarter for CCI profile (negative in quarterly table) — candidate slice only |

**Approach:** compute QQQ return / vol / trend-efficiency / range proxies **per slice**, then join profile PnL, exit mix, candidate contribution — see **`weak_period_diagnostic_design.md`** + **`.csv`**.

## F. Market context label design

| Label bucket (examples) | Notes |
|-------------------------|--------|
| `uptrend_low_vol`, `uptrend_high_vol`, `downtrend_low_vol`, `downtrend_high_vol` | From **signed** return + vol percentile vs trailing window |
| `range_chop` | Trend efficiency low + range / VWAP-churn proxies |
| `high_gap_environment` | Gap rate vs ATR (if computable without new primitives) |
| `late_trend_climax_like` | Heuristic quarter shape — optional |
| `unknown_mixed` | Fallback |

**Rule:** label names are **never** calendar IDs (no `2025Q1` as a `label_name`). See **`market_context_label_design.md`** + **`.csv`**.

## G. Expanded stability gates (taxonomy)

| Category | Intent |
|----------|--------|
| Window | early/insample/late/full positivity (hard for default profiles) |
| Monthly / quarterly | Positive-month ratio, worst month/quarter, rolling 3-month, streaks (**mostly warning**) |
| Drawdown | Full + late_oow tiers (**warning**) |
| Cost | **target-limit stress** positive on `full_available` for defaults (**hard**); symmetric/extreme as warnings |
| Exit mechanics | max_hold / stop share warnings |
| Contribution | PA positive where combined; GAP late_oow non‑material negativity; CCI justify DD for primary reference |
| Market context | No unexplained catastrophic single-label failure |
| Artifact | `SOURCE_MAP` + `CHATGPT_REVIEW_BUNDLE` + validator clean |

Full table: **`expanded_stability_gate_design.csv`**.

## H. Future run plan / outputs

| Item | Value |
|------|--------|
| Future output root | `src/research/results/layer3_expanded_stability_v1/` (**not created in this task**) |
| Profiles | **Required:** `pa_only_mtp1_meta`, `pa_gap_mtp2_meta` — **Reference:** `primary_mtp2_meta` — **Optional ref:** `pa_gap_mtp1_meta`, `pa_only_mtp2_meta` |
| New trading runs? | **Prefer reuse** of `complete_monthly_summary.csv` / `complete_quarterly_summary.csv`; detailed trade tape **local-only** if exit/contribution-by-slice requires it |
| Phases | **`expanded_stability_run_plan.csv`** (A–J) |

## I. Decision (design v1)

**Exactly one:** **`RUN_LAYER3_EXPANDED_STABILITY`**

- Profile roles and inclusion flags are explicit in **`expanded_stability_profile_selection.csv`**.
- Weak-period path is **data-derived** and avoids narrative hard-coding of 2025Q1 / 2022Q4.
- Market-context vocabulary + fallbacks are defined.
- Gate + risk + expected-output contracts are complete enough to implement a runner.
- Execution is explicitly **out of scope** for this commit — design de-risk only.

## J. Explicit non-runs and risks

- No **`layer3_expanded_stability_v1/`** execution; no mini/full WFO; no live/paper; no **SPY**; no broad Layer2; no Global Layer1 re-run.
- No strategy plugins, feature primitives, selected-candidate YAML edits, router, production short support.
- **SPY / WFO / live** evidence still absent even if expanded stability later passes — remain blocked for production claims.

## K. Files changed

- `src/research/results/layer3_expanded_stability_design_v1/**` (design CSV/MD, bundle, source map, validation)
- `tests/test_layer3_expanded_stability_design.py`
- `src/research/results/layer3_fixed_profile_smoke_complete_v1/layer3_complete_artifact_validation.*` (refresh)
- `src/research/results/RESULTS_INDEX.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, **`NEXT_HANDOFF.md`**

## L. Recommended next step

**Exactly one:** **Implement and execute `RUN_LAYER3_EXPANDED_STABILITY`** — materialize `layer3_expanded_stability_v1/` per **`expanded_stability_run_plan.md`**, reusing monthly/quarterly where possible, adding QQQ context + weak-period tables + gate rollup + new **`CHATGPT_REVIEW_BUNDLE.md`** for that root.
