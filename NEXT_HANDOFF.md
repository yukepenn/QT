# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Parent before this cycle | **`fefb268`** — `Research(router): refine offline quality diagnostics` |
| **Main research commit (this cycle)** | **`26e95cf4b37f7aec1976db4f320e2b0e2c9ed4a0`** (`26e95cf`) — `Research(exit): run overlay diagnostics` |
| Repo tip (after push) | **`7737c7c9d01fd4cac18ec33a5cd95542d24e6ba0`** (`7737c7c`) — `Docs(handoff): fix NEXT commit SHA` — should match **`git ls-remote origin refs/heads/main`** |
| Push status | Run `git push origin main` after explicit staging; verify remote `main` equals local `HEAD` |
| Working tree | Expect **untracked** heavy/local artifacts under `src/combiner/results/**`, enriched/scored CSVs, logs — **do not** `git add .` |
| Expected untracked local-only | `local_detailed_trade_context_replay_v1/local_rows/**`, `exit_overlay_diagnostics_v1/local_rows/**`, `.cache/qt/candidate_signals/**`, `sweep_*`, `top_runs/` |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **487 passed** |
| `python -m src.strategies.loader --list` | **35** strategies |
| Artifact validation — `exit_overlay_diagnostics_v1` | `exit_overlay_diagnostics_artifact_validation.csv` — **0** parse failures, **0** abs-path hits (with `local_rows/` excluded from scans) |
| Artifact validation — `router_quality_refinement_v2` | `router_quality_refinement_v2_artifact_validation.csv` (refreshed) |
| Artifact validation — `local_detailed_trade_context_replay_v1` | `local_trade_context_replay_artifact_validation.csv` (refreshed) |
| Tracked-heavy check | `git ls-files \| Select-String -Pattern "top_runs\|trades.csv\|compact_trades\|enriched.csv\|scored_trades\|trade_context_panel.csv\|overlay_trades.csv\|\\.parquet\|\\.npy\|\\.npz\|\\.memmap"` → **no matches** |
| ChatGPT bundle (exit cycle) | `src/research/results/exit_overlay_diagnostics_v1/CHATGPT_REVIEW_BUNDLE.md` |
| Source map (exit cycle) | `src/research/results/exit_overlay_diagnostics_v1/SOURCE_MAP.csv` |

## C. Task scope

| | |
|--|--|
| **Requested** | Offline exit-overlay diagnostic harness for Champion v0 (`trend_swing`, `runner`, no-followthrough, max-hold); inventories; dry-run + execute; aggregates only; tests; docs/indexes; `NEXT_HANDOFF` A–L; explicit `git add` (no row-level commits); commit + push |
| **Completed** | `exit_overlay_sim.py` + `run_exit_overlay_diagnostics.py`; full `exit_overlay_diagnostics_v1/` curated outputs; `validate_research_artifacts.py` excludes `local_rows/` by default; tests; refreshed artifact validations; `README` unchanged; `PROJECT_STATUS` / `PROGRESS` / `CHANGES` / `RESULTS_INDEX` / this handoff |
| **Intentionally not done** | WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global Layer1; production exit-management or router in combiner; strategy / feature / selected YAML edits; short/scalp implementations; committing `trade_context_panel.csv` or `overlay_trade_results.csv` |

## D. Input data / local panel

| Topic | Answer |
|--------|--------|
| Local panel | `src/research/results/local_detailed_trade_context_replay_v1/local_rows/trade_context_panel.csv` — **local-only** (gitignored) |
| Row / column count | **10,628** rows × **170** columns (filtered to Champion v0 profiles × windows in runner) |
| QQQ bars | `data/raw/ibkr` — **617,160** rows over panel span; **0** sessions missing bars (`overlay_input_coverage.csv`) |
| Overlay row output | `exit_overlay_diagnostics_v1/local_rows/overlay_trade_results.csv` — **local-only** (~106k rows × overlays); **not** committed |

## E. Overlay harness

| Topic | Answer |
|--------|--------|
| Overlays tested | `baseline_original`, `fixed_target_replay`, `trend_swing_1p5R`, `trend_swing_2R`, `runner_after_1R_trail_vwap`, `runner_after_1R_trail_atr`, `no_followthrough_exit_3bars`, `no_followthrough_exit_5bars`, `max_hold_tighten_30`, `max_hold_tighten_60` |
| Ambiguity policy | `stop_first` (default CLI) |
| No-lookahead | Post-entry bar walk only; trend-swing eligibility uses decision-time row fields |
| Baseline sanity | `overlay_sanity_vs_original.csv` — **`fixed_target_replay` vs panel `r_multiple` mean abs diff ~0.28–0.38 R** by profile×window → headline overlay deltas are **diagnostic until replay aligns** with combiner fills |

## F. Overlay results (headlines)

| Topic | Answer |
|--------|--------|
| Best trend_swing (illustrative) | `trend_swing_2R` on **`primary_mtp2_meta` / `full_available`** shows large **positive** `delta_total_r` vs baseline in detail grid — still subject to replay drift caveat |
| Best runner | `runner_after_1R_trail_vwap` on **`primary_mtp2_meta` / `full_available`** shows the largest **positive** `delta_total_r` in the profile×window grid — often labeled **`EXIT_OVERLAY_CONTEXT_SPECIFIC`** (late_oow PF can disagree) |
| No-followthrough | Generally **cuts total R** materially on pooled profiles — useful for loss-shape experiments, not a free PnL lift |
| Max-hold tighten | `max_hold_tighten_60` shows **PF / drawdown proxy improvements** on some profiles with moderate **total R** tradeoffs vs baseline — see `overlay_results_by_profile.csv` |
| Profile / window / context | See `overlay_results_detail_by_profile_window.csv`, `overlay_results_by_*`, `trend_swing_context_results.csv`, `runner_context_results.csv` |
| Weak periods | `overlay_weak_period_results.csv` — mixed by overlay; review before any integration |

## G. Exit vs router/quality comparison

| Topic | Answer |
|--------|--------|
| Comparison tables | `exit_vs_router_quality_comparison.{csv,md}` — programmatic picks vs best overlay PF delta (non-`full_available` slice) |
| Path preference | **Exit remains diagnostic** until replay matches panel; **router/quality v2** still documents narrower but complementary **trade-selection** effects |
| Integration | **No** production exit-management or router wiring from this cycle |

## H. Scalp / short roadmap

| Topic | Answer |
|--------|--------|
| After exit diagnostics | `scalp_short_after_exit_overlay.{md,csv}` — **defer** long-side scalp and short branch; evidence strength **STRONG** for deferral, **MODERATE** that max-hold / no-followthrough partially substitute time-stop discipline |

## I. Decision

**Label (exactly one):** **`RUN_EXIT_OVERLAY_DIAGNOSTICS_V2`**

- **`fixed_target_replay` ≠ panel `r_multiple`** at material scale — must **reconcile entry bar / intrabar / fill model** before trusting overlay-level deltas.
- Several overlays show **interesting PF / drawdown-proxy moves** on subsets (e.g. `max_hold_tighten_60`, VWAP runner on `full_available`) but **labels split** across windows (`EXIT_OVERLAY_CONTEXT_SPECIFIC` counts are non-zero).
- **No** production exit-management integration — design-only follow-on after simulator v2.
- Champion v0 **entries** remain frozen; this cycle only adds **offline** simulation + aggregates.
- Router/quality v2 remains the parallel track for **masking / retention** experiments (different control than exits).

## J. Explicit non-runs and risks

- **No** WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global Layer1 reruns.
- **No** production router / **no** production exit-management in combiner.
- **No** strategy / feature / selected-candidate YAML / signal edits.
- **No** short or scalp strategy code.
- Row-level **`trade_context_panel.csv`** and **`local_rows/**`** remain **local-only**.
- **Risk:** optimistic overlay rankings while replay drift persists → **treat PF / maxDD deltas as directional only**.

## K. Files changed

- `src/research/exit_overlay_sim.py`, `src/research/run_exit_overlay_diagnostics.py`
- `src/research/validate_research_artifacts.py` (default exclude `local_rows/`)
- `tests/test_exit_overlay_sim.py`, `tests/test_run_exit_overlay_diagnostics.py`
- `src/research/results/exit_overlay_diagnostics_v1/**` (curated only; no `local_rows/**`)
- Refreshed `router_quality_refinement_v2_artifact_validation.csv`, `local_trade_context_replay_artifact_validation.csv`
- `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `src/research/results/RESULTS_INDEX.md`, `NEXT_HANDOFF.md`

## L. Recommended next step (exactly one)

**Refine the exit-overlay bar simulator (replay alignment vs combiner `r_multiple`, intrabar policy, entry index) and rerun `exit_overlay_diagnostics_v1` — then decide between exit-management integration design vs returning to router integration design.**


