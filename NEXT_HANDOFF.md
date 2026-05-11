# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| **Main research commit (this cycle)** | **`85b8306`** — `Research(exit): align overlay replay diagnostics` |
| Repo tip (after push) | **`85b8306`** on `origin/main` (unless you add follow-up commits) |
| Push status | **Pushed** — `origin/main` at **`85b8306`** |
| Working tree | Expect untracked heavy artifacts under `src/combiner/results/**`, logs, sweep folders — **do not** `git add .` |
| Expected untracked local-only | `local_detailed_trade_context_replay_v1/local_rows/**`, `exit_overlay_diagnostics_v1/local_rows/**`, `exit_overlay_diagnostics_v2/local_rows/**`, `.cache/**`, `sweep_*`, `top_runs/` |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **491 passed** (includes `tests/test_exit_overlay_alignment.py`, `tests/test_run_exit_overlay_diagnostics_v2.py`) |
| `python src/strategies/loader.py --list` | **35** strategies |
| Artifact validation — `exit_overlay_diagnostics_v2` | `exit_overlay_diagnostics_v2_artifact_validation.csv` — **0** abs-path hits |
| Tracked-heavy check | `git ls-files \| Select-String -Pattern "top_runs\|trades.csv\|...\|overlay_trade_results_v2.csv\|..."` → **no matches** |
| ChatGPT bundle (V2) | `src/research/results/exit_overlay_diagnostics_v2/CHATGPT_REVIEW_BUNDLE.md` |
| Source map (V2) | `src/research/results/exit_overlay_diagnostics_v2/SOURCE_MAP.csv` |

## C. Task scope

| | |
|--|--|
| **Requested** | Exit overlay diagnostics **V2**: combiner-aligned `combiner_clone_replay`, alignment grid, contextual overlays, ambiguity sensitivity, aggregates vs clone, docs, tests, `NEXT_HANDOFF` A–L, explicit `git add`, no row-level commits |
| **Completed** | `exit_overlay_alignment.py`, `run_exit_overlay_diagnostics_v2.py`; `exit_overlay_sim.py` extensions; tests; `exit_overlay_diagnostics_v2/**` curated tree (incl. synthetic smoke rows for schema); `validate_research_artifacts` clean on v2 root |
| **Intentionally not done** | Full **10k+** panel alignment/overlay **numerics** in-repo (requires local QQQ parquet); production combiner wiring; WFO/live/SPY/broad L2 |

## D. Why V2 was needed

- V1 **`fixed_target_replay`** drifted from panel **`r_multiple`** (~0.28–0.38R mean abs) — mainly **missing combiner exit slip** and fill conventions (`combiner_semantics_inventory.md`).
- V2 adds **`combiner_clone_long_walk`** + **alignment grid** to search switch combinations before trusting overlay deltas.

## E. Alignment results

| Topic | Answer |
|--------|--------|
| Best clone config (committed YAML) | `src/research/results/exit_overlay_diagnostics_v2/alignment/alignment_best_config.yaml` — currently **`cfg_0005`** from **one-row synthetic** grid (slip `none` won on that toy path) |
| Full-panel metrics | **Run locally** — see `alignment/alignment_grid_results.csv` after `--mode alignment` |
| Pass/fail label (synthetic) | **`ALIGNMENT_FAIL`** — see `alignment/alignment_decision.md` |
| Remaining drift | Until full run: **unknown**; expect `cfg_0001` (`apply_like_combiner`) to be competitive on real data |

## F. V2 overlay results

| Topic | Answer |
|--------|--------|
| Overlays wired | `baseline_original`, `combiner_clone_replay`, `max_hold_tighten_60`, `trend_swing_2R_contextual`, `runner_after_1R_trail_vwap_contextual`, `runner_after_1R_trail_atr_contextual`, `no_followthrough_exit_5bars_contextual` |
| Ambiguity policies | `stop_first`, `target_first`, `skip_ambiguous` (runner repeats sim per policy) |
| Aggregates | `overlay_v2/overlay_v2_results_*.csv` — **include synthetic smoke**; re-run on full panel for evidence |
| Context splits | `trend_swing_v2_context_results.csv`, `runner_v2_context_results.csv`, `no_followthrough_v2_context_results.csv`, `max_hold_v2_context_results.csv` |
| Weak periods | `overlay_v2_weak_period_results.csv` (headers only if no weak-flag rows in smoke) |

## G. Exit vs router/quality comparison

| Topic | Answer |
|--------|--------|
| Tables | `exit_vs_router_quality_v2_comparison.{csv,md}` — router/quality remain primary **selection** path until clone alignment passes |
| Preferred path | **Router/quality** for integration priority **until** alignment **PASS** / **PASS_WITH_WARNINGS** on full panel |

## H. Scalp / short roadmap

| Topic | Answer |
|--------|--------|
| After V2 scaffolding | `scalp_short_after_exit_overlay_v2.{md,csv}` — defer scalp/short; alignment evidence **insufficient** on repo-only smoke |

## I. Decision

**Label (exactly one):** **`REFINE_REPLAY_ALIGNMENT`**

- Synthetic-only alignment row **fails** gates; **full panel + parquet** required.
- V1 drift root cause is **documented** (exit slip + combiner conventions).
- **No** production exit-management integration in this commit.
- Contextual overlays + ambiguity wiring are **research-only**.
- Router/quality v2 **not superseded** by exit evidence yet.

## J. Explicit non-runs and risks

- **No** WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global Layer1.
- **No** production router / **no** production exit-management in combiner.
- **No** strategy / feature / selected-candidate YAML / signal edits.
- **No** short or scalp strategy implementations.
- Row-level **`trade_context_panel.csv`**, **`overlay_trade_results_v2.csv`**, **`local_rows/**`** remain **local-only**.
- **Risk:** curated v2 CSVs contain **synthetic** rows — **do not** cite as QQQ economics without local re-run.

## K. Files changed

- `src/research/exit_overlay_alignment.py`, `src/research/run_exit_overlay_diagnostics_v2.py`, `src/research/exit_overlay_sim.py`
- `tests/test_exit_overlay_alignment.py`, `tests/test_run_exit_overlay_diagnostics_v2.py`; updates to `tests/test_exit_overlay_sim.py` if any
- `src/research/results/exit_overlay_diagnostics_v2/**` (curated; no `local_rows/**`)
- `src/research/exit_overlay_alignment.py` label fix (`total_r_diff` zero handling)
- `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `RESULTS_INDEX.md`, `NEXT_HANDOFF.md`

## L. Recommended next step (exactly one)

**Run `python -m src.research.run_exit_overlay_diagnostics_v2 --mode alignment` on the full local `trade_context_panel.csv` with QQQ parquet present; if alignment passes, run `--mode overlay`.**

