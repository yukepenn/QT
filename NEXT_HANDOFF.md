# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Parent before this cycle | **`d81a1791bcf7d254b4754988816ea8969dce4c2c`** — `Research(router): run local trade context replay` |
| **Main research commit (this cycle)** | Message **`Research(router): refine offline quality diagnostics`** — resolve SHA with **`git log -1 --format=%H`** on synced `main` (do not treat docs as authoritative if they disagree with git). |
| Repo tip (after push) | Should equal **`git rev-parse HEAD`** and match **`git ls-remote origin refs/heads/main`** when clean |
| Push status | Run `git push origin main` after explicit staging; verify `git ls-remote origin refs/heads/main` equals `git rev-parse HEAD` |
| Working tree | Expect **untracked** heavy/local artifacts under `src/combiner/results/**`, `src/research/results/**/local_runs/**`, enriched/scored CSVs, logs — **do not** stage. |
| Expected untracked local-only | `local_detailed_trade_context_replay_v1/local_rows/**`, `.cache/qt/candidate_signals/**`, `sweep_*`, `top_runs/` |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **474 passed** |
| `python -m src.strategies.loader --list` | **35** strategies |
| Artifact validation — `router_quality_refinement_v2` | `router_quality_refinement_v2_artifact_validation.csv` — **0** parse failures, **0** abs-path hits |
| Artifact validation — `local_detailed_trade_context_replay_v1` | `local_trade_context_replay_artifact_validation.csv` refreshed |
| Artifact validation — `playbook_router_research_cycle_v1` | `playbook_router_cycle_v1_artifact_validation.csv` (unchanged unless regenerated) |
| Tracked-heavy check | `git ls-files \| Select-String -Pattern "top_runs\|trades.csv\|compact_trades\|enriched.csv\|scored_trades\|trade_context_panel.csv\|\\.parquet\|\\.npy\|\\.npz\|\\.memmap"` → **no matches** |
| ChatGPT bundle (v2 cycle) | `src/research/results/router_quality_refinement_v2/CHATGPT_REVIEW_BUNDLE.md` |
| Source map (v2 cycle) | `src/research/results/router_quality_refinement_v2/SOURCE_MAP.csv` |

## C. Task scope

| | |
|--|--|
| **Requested** | README/docs consistency + offline router/quality refinement v2 on local panel; bundles; tests; explicit non-heavy staging |
| **Completed** | Concise `README.md`; v2 runner + lib + tests; `router_quality_refinement_v2/**` aggregates + designs + decision; combined guards; `import json` fix; expanded local replay bundle; indexes + handoff |
| **Intentionally not done** | WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global Layer1; production router wiring; strategy/YAML/signal edits; short/scalp implementations; committing `local_rows/**` |

## D. Champion v0 / local panel

| Topic | Answer |
|--------|--------|
| Frozen profiles | `pa_only_mtp1_meta` (baseline), `pa_gap_mtp2_meta` (default combined), `primary_mtp2_meta` (breadth reference) |
| Local panel | `src/research/results/local_detailed_trade_context_replay_v1/local_rows/trade_context_panel.csv` — **local-only** |
| Row count | **10,628** (see `aggregates/trade_context_coverage.csv`) |

## E. README / code consistency refresh

- `README.md` rewritten as a short seven-section front page aligned to Layer1/Layer2/Layer3 + playbook + local replay.
- Scripts: mostly already readable; **bugfix** only in `run_trade_quality_score_v2.py` (`json` import).
- Local replay `CHATGPT_REVIEW_BUNDLE.md` expanded into a real review entry.

## F. Router v2 diagnostics

| Topic | Answer |
|--------|--------|
| Variants tested | `baseline_all`, `soft_avoid_removed`, `soft_downweight_proxy`, `gap_context_guard`, `late_climax_guard`, `high_chop_guard`, `repeat_after_loss_guard`, `combined_light_guard` |
| Best “promising” examples | `late_climax_guard` (PF uplift, **~0.82–0.90** retention on profiles); `gap_context_guard` / `combined_light_guard` smaller improvements |
| Retention | See `router_v2/router_v2_trade_retention.csv` |
| PF / maxDD / weak-period | See `router_v2/router_v2_results.csv` + `router_v2_weak_period_effect.csv` |
| Layer2 integration? | **Not yet** — tradeoffs + lack of held-out threshold discipline → **no combiner wiring** |

## G. Quality refinement v2

| Topic | Answer |
|--------|--------|
| Score variants | `original_v2_score`, `no_signal_strength_fallback`, `regime_level_cost_only`, `freshness_penalty_light`, `repeat_after_loss_penalty_only`, `context_fit_plus_cost`, `profile_percentile_score` |
| Threshold schemes | `fixed_AB`, `relaxed_AB`, percentile-by-profile/window, `bottom_cut_{10,20,30}` |
| Best-behaved “promising” patterns | `percentile_profile_top80`, `bottom_cut_20` on `original_v2_score` often land near **~80% retention** with PF / maxDD proxy improvements — flagged **`in_sample_diagnostic=True`** |
| Fixed A/B | Still **over-filters** vs 60–85% goal |
| Useful? | **Yes as ranking evidence**, **no** as immediate production filter without OOS discipline |

## H. Combined guards / exit implications

| Topic | Answer |
|--------|--------|
| Combined light guards | Ran (`combined_light_guards/*`) because both router and quality passes had `PROMISING` rows |
| Exit overlay implications | **`RUN_EXIT_OVERLAY_DIAGNOSTICS`** — see `exit_overlay_implications.*` |
| Scalp / short | Roadmap-only; scalp de-prioritized vs `trend_swing` / `runner` preview |

## I. Decision

**Label (exactly one):** **`RUN_EXIT_OVERLAY_DIAGNOSTICS`**

- Offline router v2 finds **real PF / maxDD proxy improvements** under **soft** masks, but **total R** tradeoffs on **`primary_mtp2_meta`** remain sensitive.
- Quality v2 shows **percentile/bottom-cut** can hit retention targets, but thresholds are **in-sample** on the same panel.
- Exit readiness preview already points to **`trend_swing` / `runner`** as higher next ROI than more score tinkering.
- Champion v0 stays frozen; next increment should be **simulation harnessing**, not combiner integration.

## J. Explicit non-runs and risks

- **No** WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global Layer1 reruns.
- **No** production router / hard regime filters / short implementation / strategy signal changes / selected YAML edits.
- Row-level artifacts **local-only**; research-only aggregate commits.
- **Risk:** in-sample percentile thresholds can look good without out-of-sample guardrails.

## K. Files changed

- `README.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `NEXT_HANDOFF.md`, `src/research/results/RESULTS_INDEX.md`
- `src/research/run_trade_quality_score_v2.py` (json import)
- `src/research/run_router_quality_refinement_v2.py`, `src/research/router_quality_refinement_v2_lib.py`
- `tests/test_router_quality_refinement_v2.py`
- `src/research/results/router_quality_refinement_v2/**`
- `src/research/results/local_detailed_trade_context_replay_v1/CHATGPT_REVIEW_BUNDLE.md`, `SOURCE_MAP.csv`, `local_trade_context_replay_artifact_validation.csv`

## L. Recommended next step (exactly one)

**Run offline exit-overlay diagnostics** (start with **`trend_swing`**, then **`runner`**) using a bar-path-capable harness while keeping outputs **aggregate-only** and leaving Champion v0 frozen.

