# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Tip | After push, verify `git log -1 --oneline` matches `git ls-remote origin refs/heads/main`. |
| Working tree | Stage curated paths only — **never** `git add .` |

## B. Validation

| Check | Result (post exit-overlay diagnostic) |
|--------|----------------------------------------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **142** passed |
| `python -m src.strategies.loader --list` | OK |
| `python -m src.backtest.sweep --smoke` | OK |
| `python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend` | OK |
| `python -m src.combiner.run --help` | OK |
| `python -m src.combiner.sweep --help` | OK |
| `python -m src.research.run_combiner_adapter_parity --help` | OK |
| `python -m src.research.run_exit_overlay_execution_path --help` | OK |
| `python -m src.research.validate_research_artifacts --root src/research/results/exit_overlay_execution_path --csv-only` | OK → `exit_overlay_execution_path_artifact_validation.csv` |

## C. Task scope

**Exit overlay on execution path (research-only):** thin runner `src/research/run_exit_overlay_execution_path.py` + tests `tests/test_exit_overlay_execution_path.py`. **No third PnL engine** — baseline **`simulate_combiner_canonical`**; overlays **`simulate_trade_path`** with modified **`TradeIntent` / `ExitPlan`**. **No** WFO, broad Layer2, Global Layer1, live/paper, SPY, router production, scalp/short, Champion YAML edits, legacy deletion.

## D. Data / candidate inputs

- **Bars:** repo-local **`data/raw/ibkr`** (via `--bar-root data` → `resolve_ibkr_data_dir`).
- **Candidates:** `src/research/results/Archive/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates`.
- **Profiles / IDs:** `pa_only_mtp1_meta` → `PA_BUY_SELL_CLOSE_TREND_003`; `pa_gap_mtp2_meta` → PA + `GAP_ACCEPTANCE_FAILURE_001`. CLI supports comma-separated **`--profile`** for a single aggregate CSV batch.

## E. Layer file map / cleanup inventory

- **`layer_file_map.csv` / `.md`:** Layer1/2/3 + execution/support roles; confirms only **`src/execution/`** should own accounting math.
- **`file_cleanup_candidates.csv` / `.md`:** classify only — **no deletes**.

## F. Overlay support status

| Overlay | Status |
|---------|--------|
| `baseline_execution_backed` | supported |
| `max_hold_tighten_60` | supported |
| `no_followthrough_exit_5bars` | supported |
| `trend_swing_2r` | supported |
| `trail_after_1r_simple` | **unsupported** (no arm-after-R trailing threshold in contract) |
| `runner_after_1r_reference` | **unsupported** (no runner ladder) |

Deduped reasons: `overlay_unsupported.csv`.

## G. Overlay results

- **Smoke:** QQQ **2024-01** — see `overlay_smoke_summary.csv` (both profiles). **max_hold** and **NFT** reduce **`total_r`** vs baseline; **NFT** turns **PA+GAP** smoke **negative**; **trend_swing_2r** slightly helps PA-only smoke.
- **Repo coverage:** full QQQ span in committed shards (**~2020–2026** on this checkout) — `overlay_repo_coverage_*`. Same qualitative pattern: **max_hold** / **NFT** haircut baseline **`total_r`**; **trend_swing_2r** near baseline.
- **Local-only:** `_local_only/` (precompute profiles, feature stats, optional replay row CSVs) — **gitignored**.

## H. Decision

**`USE_EXECUTION_BACKED_FOR_RESEARCH_AND_REBUILD_LAYER1_2_3`**

## I. Explicit non-runs / risks

No mini/full WFO, production exit-management, inverse/side-flip research, new strategies, combiner production behavior changes, raw row-level trade commits, `top_runs` / `local_runs` (new), parquet outside `data/raw/ibkr`.

## J. Files changed

`.gitignore` (`src/research/results/**/_local_only/`), `src/research/run_exit_overlay_execution_path.py`, `tests/test_exit_overlay_execution_path.py`, `src/research/results/exit_overlay_execution_path/**` (curated CSV/MD), `docs/LAYER_FLOW.md`, `src/research/results/RESULTS_INDEX.md`, `NEXT_HANDOFF.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`.

## K. Local-only artifacts

`src/research/results/exit_overlay_execution_path/_local_only/` — precompute CSV/MD/JSON + optional **`--local-row-output`** replay tables; **not** committed.

## L. Recommended next step (exactly one)

**`USE_EXECUTION_BACKED_FOR_RESEARCH_AND_REBUILD_LAYER1_2_3`**
