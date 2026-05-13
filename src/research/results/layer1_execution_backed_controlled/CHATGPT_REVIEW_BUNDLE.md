# CHATGPT_REVIEW_BUNDLE — Layer1 execution-backed controlled (minimal proof)

External review pack for **`RUN_MINIMAL_LAYER1_EXECUTION_BACKED_PROOF_AND_PREP_FASTPATH`**. Accounting truth remains **`src/execution/path.py`** (`simulate_trade_path`); **`fast_path.py`** is not canonical until parity tests exist.

## 1. Git / validation

- **Branch:** `main`.
- **`python -m compileall -q src`:** OK.
- **`python -m pytest -q`:** **165** passed (includes **`tests/test_sweep_checkpoint.py`**).
- **`python -m src.strategies.loader --list`:** OK.
- **`python -m src.backtest.sweep --help`:** OK (**`--checkpoint-every`**, **`--resume`**).
- **`python -m src.backtest.sweep --smoke`:** OK.
- **`python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend --symbol QQQ --start 2024-01-02 --end 2024-01-05 --data-root data/raw/ibkr`:** OK.
- **`python -m src.research.run_layer1_execution_backed_controlled --help`:** OK (**`--include-run-name-contains`**).
- **`validate-candidates`** on active root: OK (see **`minimal_candidate_root_validation.*`**).
- **`python -m src.research.validate_research_artifacts --root .../layer1_execution_backed_controlled --csv-only`:** OK (**29** path rows in **`layer1_execution_backed_controlled_artifact_validation.csv`**).

## 2. Why full focused run was interrupted / abandoned for now

- Full focused Cartesian product (**~656** combos) on the **Python reference** execution path is too slow for a single uninterrupted session; prior run had **no** resumable **`sweep_results.csv`**, so progress was not recoverable.
- **New policy:** use **explicit small balanced YAML grids** (full Cartesian product **without** prefix-biased **`--max-combos`**) plus **checkpoint/resume** so long runs can continue after interrupt.

## 3. Checkpoint / resume implementation

- **`src/backtest/sweep.py`:** per-combo append path uses **atomic** write (temp file → replace) for **`sweep_results_partial.csv`** and **`sweep_progress.json`** when **`output_root`** is set and not **`--dry-run`**.
- **`sweep_progress.json`:** strategy, symbol, dates, grid path, output root, total combos, completed **`combo_id`** set, **`last_completed_at_utc`**, **`status`**, git SHA when available.
- **`--resume`:** skips combos whose **`combo_id`** already appears in the partial CSV.
- **Successful completion:** final **`sweep_results.csv`** + **`sweep_meta.json`** + **`sweep_summary.md`**; partial CSV **removed** on **`completed`** so stale partials do not confuse reviewers.
- **Timing columns on each row:** **`combo_elapsed_sec`**, **`combo_started_at_utc`**, **`combo_finished_at_utc`**, **`combo_index`**, **`combo_count_total`**, **`combo_id`** (see **`checkpoint_resume_design.*`**).

## 4. Minimal balanced grid design

- **`pa_buy_sell_close_trend_minimal_proof.yaml`:** **16** combos — fixed execution/backtest fields aligned with production YAMLs; small PA signal + risk grid.
- **`gap_acceptance_failure_minimal_proof.yaml`:** **16** combos — keys aligned with **`gap_acceptance_failure`** validator (see focused YAML for naming).
- **`cci_extreme_snapback_minimal_proof.yaml`:** **8** combos.
- **Total:** **40** combos — **`minimal_grid_design.*`**.

## 5. Minimal sweep results

- **Outputs:** `src/research/results/layer1_execution_backed_controlled/runs/{pa_buy_sell_close_trend,gap_acceptance_failure,cci_extreme_snapback}_2023_2024_minimal_proof/`.
- Each run: **`sweep_results.csv`**, **`sweep_meta.json`**, **`sweep_progress.json`** (**`status: completed`**), **`sweep_summary.md`**; **`data_source`** stamped **`ibkr_parquet:data/raw/ibkr`** when run from repo root.
- **No** raw trade files committed.
- Summary metrics: **`minimal_sweep_summary.*`**.

## 6. Runtime profile (from timing columns)

- **Aggregate wall clock** (three sweeps sequential): ~**1121 s** for **40** combos (~**28 s** / combo average).
- **Per-strategy max combo elapsed (approx.):** PA ~**18 s**; GAP ~**26 s**; CCI ~**29 s** — reference path is the bottleneck for larger grids; see **`fast_path_numba_readiness.*`**.

## 7. Promotion / candidate root

- **Promotion filter:** **`--include-run-name-contains minimal_proof`** so interrupted **`*_full_focused`** folders (if any reappear) are not mixed into selection.
- **Gate label:** **`L1_EXECUTION_BACKED_MINIMAL_PROOF`**.
- **Candidate IDs:** **`*_L1M_*`** plus **`selection.candidate_kind: minimal_proof`** in YAML metadata where supported.
- **Write result:** **4** YAMLs (**GAP**×2, **CCI**×2); **PA** had no row meeting **PF_R ≥ 1.02** on this minimal slice (max ~**1.014**).
- **Indices:** **`CANDIDATE_INDEX.csv`**, **`selected_candidates_summary.csv`**, **`candidate_rejects_summary.csv`**.
- Details: **`minimal_promotion_dry_run.*`**, candidate root **`README.md`**.

## 8. Candidate validation

- **`validate-candidates`** on **`src/strategies/testing_parameters_results/l1_execution_backed_controlled`:** OK — schema, repo-relative paths, execution stamp, metrics block. See **`minimal_candidate_root_validation.*`**.

## 9. Fast-path Numba readiness

- **No Numba implementation** in this task.
- **`fast_path_numba_readiness.*`** defines phase-1 scope (long-only, fixed-R, min risk, next-open, stop/target ambiguity, max-hold, EOD), proposed API **`simulate_trade_path_fast(...)`**, and parity cases (simple win/stop, same-bar ambiguity, min-risk reject, max-hold, EOD, no-trade session, gap edge if needed).
- **Rule:** broad / full focused sweeps should switch to fast path **only after** parity vs **`simulate_trade_path`** passes.

## 10. Decision

**`RUN_CONTROLLED_LAYER2_ON_MINIMAL_CANDIDATES`**

Minimal sweeps and artifact validation succeeded; **4** minimal-proof YAMLs are combiner-loadable for a **tiny** Layer2 smoke; PA remains under PF gate on this narrow grid — do **not** treat **`L1M`** files as full-focused champions.

## 11. Explicit non-runs

- No full focused **~656** sweep, no broad Layer1, no Layer3, no WFO, no live/paper, no SPY research, no router, no new strategy families, no Numba as canonical PnL, no raw trades / panels / caches / logs / npy in git.

## 12. Recommended next step

**`RUN_CONTROLLED_LAYER2_ON_MINIMAL_CANDIDATES`** — point combiner Layer2 smoke at **`l1_execution_backed_controlled`** with **`execution_backed`** and validate combiner metrics on **minimal_proof** candidates only; in parallel, schedule **`DESIGN_FAST_PATH_NUMBA_PARITY`** implementation when ready to unblock larger Layer1.

## Navigation

- **`SOURCE_MAP.csv`** — file index.
- **`chatgpt_key_tables.csv`** — key numeric fields.
- **`layer1_execution_backed_controlled_key_findings.csv`** — short findings list.
