# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| **Main research commit (this cycle)** | `Research(exit): refine max-hold replay alignment` — verify SHA with `git log -1 --oneline` after push |
| Repo tip (after push) | Must equal local `HEAD` after successful `git push origin main` (verify with `git ls-remote origin refs/heads/main`) |
| Push status | **Verify** with `git status -sb` and `git ls-remote origin refs/heads/main` after push |
| Working tree | Untracked heavy artifacts under `src/combiner/results/**`, logs, sweep folders — **do not** `git add .` |
| Expected untracked local-only | `local_detailed_trade_context_replay_v1/local_rows/**`, `exit_overlay_diagnostics_v1/local_rows/**`, `exit_overlay_diagnostics_v2/local_rows/**` (incl. `alignment_trade_detail.csv`), `.cache/**`, `sweep_*`, `top_runs/` |

## B. Validation

| Check | Result |
|--------|--------|
| `python -m compileall -q src` | OK (re-run before next handoff) |
| `python -m pytest -q` | **497 passed** last full run in this cycle |
| `python -m src.strategies.loader --list` | **35** strategies |
| Artifact validation — `exit_overlay_diagnostics_v2` | `exit_overlay_diagnostics_v2_artifact_validation.csv` — **0** abs-path hits (re-run after edits) |
| Tracked-heavy check | `git ls-files \| Select-String -Pattern "top_runs\|trades.csv\|...\|overlay_trade_results_v2.csv\|..."` → **no matches** |
| ChatGPT bundle (V2) | `src/research/results/exit_overlay_diagnostics_v2/CHATGPT_REVIEW_BUNDLE.md` |
| Source map (V2) | `src/research/results/exit_overlay_diagnostics_v2/SOURCE_MAP.csv` |

## C. Exit overlay v2 — max_hold alignment refinement (this cycle)

| | |
|--|--|
| **Real full-panel alignment reran** | **Yes** — **10,628** rows; **617,160** QQQ bars; **18** grid configs (incl. `max_hold_priority` variants) |
| **Headline best config** | **`cfg_0015`** (`intrabar_first`) — still **`ALIGNMENT_FAIL`** (`total_r_diff` ≈ **+52.4R**) |
| **forced_first_on_terminal_bar** | **`cfg_0016_mh_forced`** — `total_r_diff` ≈ **+51.2R** (still FAIL) |
| **panel_exit_reason_authoritative** | **`cfg_0017_mh_panelauth`** — **identical** aggregate metrics to `cfg_0015` on this panel |
| **skip_terminal_bar_conflicts** | **`cfg_0018_mh_skipconf`** — **`ALIGNMENT_PASS`** only by **excluding** mismatched rows (**diagnostic**, not overlay baseline) |
| **Max_hold drift shape** | **476 / 5188** panel `max_hold` rows replay **`stop`/`target`** first — **all 476** have **`replay_exit_bar_index` < `panel_exit_idx`** (**pre-terminal**), **0** on-terminal, **0** after |
| **Overlay ran** | **No** — `OVERLAY_BLOCKED_ALIGNMENT_FAIL` (`max_hold_alignment_v1/overlay_gate_after_max_hold_alignment.md`) |
| **Decision** | **`REFINE_REPLAY_ALIGNMENT`** |
| **Exact next step** | Audit **pre-terminal** materialization for the **476** rows (entry bar alignment, `stop_price`/`target_price` vs session OHLC, `panel_exit_idx` cap, session join), then adjust **research-only** replay if justified; rerun `--mode alignment`; overlay only after PASS/PWW on headline clone |

## D. Synthetic vs real artifacts

- **Prior committed v2 `alignment/*`:** synthetic smoke — **archived** to `alignment/archive_synthetic_pre_full_panel/`.
- **Current curated `alignment/*`:** **real** full-panel outputs + `full_panel_alignment_manifest.csv` (`synthetic_or_real=real`, **18** configs).
- **`overlay_v2/*`:** **not** refreshed for economics; see `overlay_v2/overlay_v2_summary.md`.

## E. Key files

- **max_hold v1:** `max_hold_alignment_v1/*` (baseline inventory, combiner semantics audit, drift aggregates, overlay gate, bug assessment, mode comparison)
- **Builder:** `src/research/build_max_hold_alignment_v1_aggregates.py` (reads **local-only** `local_rows/alignment_trade_detail.csv`)
- Alignment: `alignment/alignment_grid_results.csv`, `alignment_best_config.yaml`, `alignment_decision.md`, `full_panel_alignment_manifest.csv`, `full_panel_alignment_failure_*`
- Decision / bundle: `exit_overlay_diagnostics_v2_decision.md`, `CHATGPT_REVIEW_BUNDLE.md`, `exit_overlay_diagnostics_v2_summary.md`, `chatgpt_key_tables.csv`, `exit_overlay_diagnostics_v2_key_findings.csv`
- Overlay not run: `comparison_not_run_reason.md`, `overlay_v2/full_panel_overlay_manifest.csv`

## F. Explicit non-runs

- No WFO / mini-WFO / live / paper / SPY / broad Layer2 / Global Layer1.
- No production router / exit-management integration.
- No production combiner semantics change in this task.
- No strategy / feature / selected-candidate YAML edits.
- No commit of `local_rows/**`, row-level panel, parquet, logs.

## G. Recommended next step (exactly one)

**Audit pre-terminal replay vs panel materialization for the 476 max_hold mismatch rows, refine research-only clone inputs/caps as needed, rerun full-panel `--mode alignment`.**

