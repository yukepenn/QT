# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Parent before this cycle | **`92ba1fab0002929a9e6805ba896ef7c1a79a6567`** — `Research(router): design playbook router cycle` |
| **Main research commit (this cycle)** | Message **`Research(router): run local trade context replay`** — resolve full SHA with **`git log -1 --format=%H`** on synced `main` (do not embed commit hash into itself). |
| Repo tip (after push) | Same as **Main research commit** when `main` is clean and matches **`git ls-remote origin refs/heads/main`** |
| Push status | After staging, run **`git push origin main`**; verify **`git ls-remote origin refs/heads/main`** equals local **`git rev-parse HEAD`**. |
| Working tree | Curated **`src/research/results/local_detailed_trade_context_replay_v1/**`** tracked (aggregates only). Row-level artifacts remain local-only and gitignored. **Do not** `git add .`. |
| Expected untracked local-only | `src/research/results/local_detailed_trade_context_replay_v1/local_runs/**`, `src/research/results/local_detailed_trade_context_replay_v1/local_rows/**`, `.cache/qt/candidate_signals/**`, `sweep_*`, `top_runs/` |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **464 passed** |
| `python -m src.strategies.loader --list` | **35** strategies (list printed by loader) |
| Artifact validation — `layer3_expanded_stability_v1` | **`layer3_expanded_stability_artifact_validation.*`** refreshed (**0** parse failures, **0** abs-path hits in validator output for this root) |
| Artifact validation — `layer3_fixed_profile_smoke_complete_v1` | **`layer3_complete_artifact_validation.*`** refreshed |
| Artifact validation — `playbook_router_research_cycle_v1` | **`playbook_router_cycle_v1_artifact_validation.*`** — **32** CSVs, **0** parse failures, **0** absolute-path hits, **0** missing required columns |
| Tracked-heavy check | `git ls-files \| Select-String -Pattern "top_runs\|trades.csv\|compact_trades\|enriched.csv\|scored_trades\|\.parquet\|\.npy\|\.npz\|\.memmap"` → **no matches** |
| ChatGPT bundle (this cycle) | `src/research/results/playbook_router_research_cycle_v1/CHATGPT_REVIEW_BUNDLE.md` |
| ChatGPT bundle (this cycle) | `src/research/results/local_detailed_trade_context_replay_v1/CHATGPT_REVIEW_BUNDLE.md` |
| Source map (this cycle) | `src/research/results/local_detailed_trade_context_replay_v1/SOURCE_MAP.csv` |

## C. Task scope

| | |
|--|--|
| **Requested** | **Local-only** detailed trade-context replay for Champion v0; backward-asof decision-time context join; commit only aggregates; run offline router + quality v2 diagnostics; attribution/freshness/exit readiness/roadmap evidence; bundle + source map + decision; **no** WFO/live/SPY/broad L2/strategy or YAML edits/production router wiring. |
| **Completed** | Local-only detailed replays for **3** Champion v0 profiles × **4** windows; local-only row panel (not committed); committed aggregates under `local_detailed_trade_context_replay_v1/` including router diagnostics, quality v2 diagnostics, attribution, freshness, exit readiness, roadmap update, bundle/source map/decision. |
| **Intentionally not done** | No WFO / mini-WFO / live / paper; no SPY / broad Layer2 / Global Layer1 rerun; no strategy/feature/YAML semantics changes; no production router wiring; no row-level artifacts committed. |

## D. Champion v0 freeze

| profile_id | role | candidates | Why frozen |
|------------|------|------------|------------|
| `pa_only_mtp1_meta` | CLEAN_BASELINE | `PA_BUY_SELL_CLOSE_TREND_003` | Simplest profile; positive across key windows; **robustness anchor**. **Do not modify** YAML parameters for this champion profile. |
| `pa_gap_mtp2_meta` | DEFAULT_COMBINED | PA + `GAP_ACCEPTANCE_FAILURE_001` | Default combined; PA is main driver; GAP adds **early / insample / full** incremental R in complete smoke. **Do not modify** champion YAML parameters. |
| `primary_mtp2_meta` | BREADTH_REFERENCE_ONLY | PA + GAP + `CCI_EXTREME_SNAPBACK_003` | Highest **full_available** total R in complete smoke but **deeper max drawdown** and **weaker late_oow** vs PA-only / PA+GAP pattern — **reference only**; **do not promote** to default without new evidence. |

**Champion v0 constraints (explicit):** long-only intraday sleeve; **not** a full day-trader system; **not production-ready**; frozen as **benchmark/incumbent** for future router, scalp, short, and exit-overlay research.

## E. Trade-context panel

| Topic | Location / answer |
|--------|-------------------|
| Schema (row-level contract) | `trade_context_panel_schema.csv` + `.md` |
| Available from curated smoke | `trade_context_available_fields.csv` — window **total_r**, candidate shares, exit-reason shares, trade#, monthly/quarterly rows (see `trade_context_panel_v1/`) |
| Local row-level panel | `src/research/results/local_detailed_trade_context_replay_v1/local_rows/trade_context_panel.csv` (**local-only; not committed**) |
| Local row count | **10,628** trades |
| Decision timestamp logic | Prefer `signal_ts_utc`; fallback `entry_ts_utc - 1min` (if needed). Join is backward `merge_asof` only. |
| Coverage | `aggregates/trade_context_coverage.csv` (100% join coverage on regime window 20 in this run) |

## F. Router / quality / exit design

| Area | Artifact |
|------|-----------|
| Router context buckets | `trend_long`, `trend_short_diagnostic`, `trading_range`, `gap_failure`, `late_climax`, `high_chop`, `unknown_mixed` — `router_design_v1/offline_router_rule_design.csv` + `.md`, draft YAML **`enabled: false`**, **`mode: offline_diagnostic`** |
| Candidate metadata | `router_metadata_v1/candidate_playbook_metadata.csv` (+ future rows **`DESIGN_ONLY_NOT_IMPLEMENTED`**) |
| Trade-quality score v2 | Weights **30% / 20% / 20% / 15% / 15%** = **100%** — `trade_quality_score_v2/trade_quality_score_design.*`, `quality_score_v2_test_plan.csv` |
| Exit management modes | **`scalp`**, **`trend_swing`**, **`runner`**, **`reversal`** — `exit_overlay_design_v1/exit_overlay_design.csv`, `exit_overlay_test_plan.csv` |

## G. Scalp / short roadmap

| Branch | Artifact | Status |
|--------|----------|--------|
| Long-side scalp families (4) | `scalp_strategy_roadmap_v1/scalp_strategy_roadmap.csv` | **`DESIGN_ONLY_NOT_IMPLEMENTED`** |
| Short-side families (6) | `short_strategy_roadmap_v1/short_strategy_roadmap.csv` | **`DESIGN_ONLY_NOT_IMPLEMENTED`** |
| Validation sequence | Short-only Layer1 + OOW **before** any mix with Champion v0; scalp long **Layer1 strict** only after router diagnostics — see roadmaps + `next_3layer_sweep_roadmap.csv` |

## H. Next 3-layer sweep roadmap (ordered)

| cycle_id | One-line purpose |
|----------|------------------|
| **Cycle_1** | Router diagnostics against Champion v0 (offline; existing + local trades). |
| **Cycle_2** | Router-integrated **controlled** Layer2 (Champion candidates only; router/quality axes). |
| **Cycle_3** | Scalp long-side additions (2–4 families; Layer1 only). |
| **Cycle_4** | Short-side branch (standalone Layer1 + OOW). |
| **Cycle_5** | Integrated Layer2 (v0 + approved scalp + validated short if any). |
| **Cycle_6** | Layer3 fixed profiles (smoke / OOW / stability). |
| **Cycle_7** | Reduced WFO (QQQ; frozen candidates; small grid; train/test discipline). |

**Pass conditions / non-goals:** see CSV columns `pass_condition`, `explicit_non_goals`, `expected_decision`.

## I. Decision

**Label (exactly one):** **`REFINE_ROUTER_QUALITY_SCORE`**

- Champion v0 **freeze + roles** are documented and asserted in tests; strategic work shifts to **context** rather than new strategies.
- **Curated `complete_*` summaries** support window-level PA vs PA+GAP vs primary and weak-period **proxies** only.
- **Row-level** regime labels, per-trade market context, prior-trade linkage, and true **GAP-vs-PA** attribution **cannot** be recovered from committed aggregates alone.
- Offline router / quality / exit designs are **ready** to consume a row-level panel once built **locally**.
- The lowest-risk next increment is a **local-only** trade tape + backward `merge_asof` feature join (outputs not committed except new aggregates if a future script emits them).

## J. Explicit non-runs and risks

- **No** full / mini / reduced **WFO** execution in this cycle.
- **No** live / paper / **SPY** / broad **Layer2** / Global **Layer1** rerun.
- **No** new production strategies; **no** short/scalp **code**; **no** strategy **signal** semantics or **selected-candidate YAML** edits; **no** combiner **production regime_router** wiring.
- **Research-only** scripts + curated CSV/MD; **no** raw `trades.csv` / row-level enriched or scored panels in git.
- **Risk:** window-level proxies can **over-interpret** late_oow GAP weakness without trade-level context — treat **`gap_increment_by_context.csv`** as **proxy**, not ground truth for regime routing.

## K. Files changed (this commit)

- **Result root:** `src/research/results/playbook_router_research_cycle_v1/**`
- **Scripts:** `src/research/build_trade_context_panel.py`, `src/research/analyze_playbook_context.py`
- **Tests:** `tests/test_playbook_router_cycle_v1.py`
- **Refreshed validations:** `src/research/results/layer3_expanded_stability_v1/layer3_expanded_stability_artifact_validation.csv`, `src/research/results/layer3_fixed_profile_smoke_complete_v1/layer3_complete_artifact_validation.csv`
- **Indexes / docs:** `src/research/results/RESULTS_INDEX.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, **`NEXT_HANDOFF.md`**

## L. Recommended next step (exactly one)

**Refine the offline router filters and quality score v2 component definitions using the now-available decision-time panel fields, then rerun aggregate-only diagnostics (still no production wiring).**

---

## Evidence table — complete smoke window **total_r** (Champion v0 trio)

| profile_id | early_oow | insample_ref | late_oow | full_available | max_drawdown_r (full) |
|------------|----------:|-------------:|---------:|-----------------:|---------------------:|
| `pa_only_mtp1_meta` | 45.14 | 37.97 | **21.49** | 104.59 | −17.71 |
| `pa_gap_mtp2_meta` | **60.95** | **52.27** | 18.77 | **131.99** | −21.27 |
| `primary_mtp2_meta` | **61.33** | **62.70** | **11.86** | **135.89** | −25.09 |

**Read:** PA-only **wins late_oow** total_r vs PA+GAP and primary; PA+GAP **wins** early/insample/full vs PA-only; primary **wins full** at cost of **weaker late_oow** and **deepest DD**.
