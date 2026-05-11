# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| **Main research commit (this cycle)** | `Research(exit): run full-panel overlay alignment` — identify SHA with `git log -1 --oneline` on `main` after pull |
| Repo tip (after push) | Must equal local `HEAD` after successful `git push origin main` (verify with `git ls-remote origin refs/heads/main`) |
| Push status | **Verify** with `git status -sb` and `git ls-remote origin refs/heads/main` after push |
| Working tree | Untracked heavy artifacts under `src/combiner/results/**`, logs, sweep folders — **do not** `git add .` |
| Expected untracked local-only | `local_detailed_trade_context_replay_v1/local_rows/**`, `exit_overlay_diagnostics_v1/local_rows/**`, `exit_overlay_diagnostics_v2/local_rows/**` (incl. `alignment_trade_detail.csv`), `.cache/**`, `sweep_*`, `top_runs/` |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK (re-run before next handoff) |
| `python -m pytest -q` | **491 passed** last full run in this cycle |
| `python -m src.strategies.loader --list` | **35** strategies |
| Artifact validation — `exit_overlay_diagnostics_v2` | `exit_overlay_diagnostics_v2_artifact_validation.csv` — **0** abs-path hits (re-run after edits) |
| Tracked-heavy check | `git ls-files \| Select-String -Pattern "top_runs\|trades.csv\|...\|overlay_trade_results_v2.csv\|..."` → **no matches** |
| ChatGPT bundle (V2) | `src/research/results/exit_overlay_diagnostics_v2/CHATGPT_REVIEW_BUNDLE.md` |
| Source map (V2) | `src/research/results/exit_overlay_diagnostics_v2/SOURCE_MAP.csv` |

## C. Exit overlay v2 — full-panel alignment (this cycle)

| | |
|--|--|
| **Real full-panel alignment ran** | **Yes** — 10,628 rows (Champion v0 profiles × windows) |
| **QQQ bar rows loaded** | **617,160** (`data/raw/ibkr`, `bar_load_meta.csv`; missing sessions **0**) |
| **Alignment result** | **`ALIGNMENT_FAIL`** — best grid `cfg_0015`: low mean/median \|ΔR\|, but **`total_r_diff` ≈ +52.4R** exceeds PASS/PWW aggregate budgets |
| **Overlay ran** | **No** — gates require PASS or PASS_WITH_WARNINGS first |
| **Decision** | **`REFINE_REPLAY_ALIGNMENT`** |
| **Exact next step** | Reconcile **panel `max_hold`** vs replay **stop/target** path (476 / 5188 `max_hold` rows); refine `combiner_clone_long_walk` / labeling; rerun `--mode alignment`, then `--mode overlay` if eligible |

## D. Synthetic vs real artifacts

- **Prior committed v2 `alignment/*`:** synthetic smoke — **archived** to `alignment/archive_synthetic_pre_full_panel/`.
- **Current curated `alignment/*`:** **real** full-panel outputs + `full_panel_alignment_manifest.csv` (`synthetic_or_real=real`).
- **`overlay_v2/*`:** **not** refreshed this cycle; treat prior CSVs as **schema smoke only** until overlay reruns (`overlay_v2/overlay_v2_summary.md`).

## E. Key files

- Inventories: `full_panel_run_inventory.{md,csv}`, `local_full_panel_input_check.{md,csv}`, `full_panel_commands.{md,ps1}`
- Alignment: `alignment/alignment_grid_results.csv`, `alignment_best_config.yaml`, `alignment_decision.md`, `full_panel_alignment_manifest.csv`, `full_panel_alignment_failure_*`
- Decision / bundle: `exit_overlay_diagnostics_v2_decision.md`, `CHATGPT_REVIEW_BUNDLE.md`, `exit_overlay_diagnostics_v2_summary.md`, `chatgpt_key_tables.csv`
- Overlay not run: `comparison_not_run_reason.md`, `overlay_v2/full_panel_overlay_manifest.csv`

## F. Explicit non-runs

- No WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global Layer1.
- No production router / exit-management integration.
- No strategy / feature / selected-candidate YAML edits.
- No commit of `local_rows/**`, row-level panel, parquet, logs.

## G. Recommended next step (exactly one)

**Refine replay alignment for `max_hold` vs intrabar stop/target, rerun full-panel `--mode alignment`, then overlay if PASS/PWW.**


