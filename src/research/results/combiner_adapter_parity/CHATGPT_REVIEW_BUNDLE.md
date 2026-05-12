# CHATGPT_REVIEW_BUNDLE — combiner_adapter_parity

Readable raw bundle for external review. Repo: `https://github.com/yukepenn/QT`.

## 1. Git / validation

- Branch: `main` (at commit time of this bundle).
- `python -m compileall -q src`: OK.
- `python -m pytest -q`: **133** tests passed (includes new `tests/test_combiner_adapter_parity.py`).
- Layer1: `python -m src.backtest.sweep --smoke` and `--validate-pipeline --strategy pa_buy_sell_close_trend`: OK.
- Combiner CLI: `python -m src.combiner.run --help` / `sweep --help`: OK; documents `--engine` tokens.
- Artifact scan: `python -m src.research.validate_research_artifacts --root src/research/results/combiner_adapter_parity --csv-only` → `combiner_adapter_parity_artifact_validation.csv`.

## 2. Why this task was needed

Docs still mixed **stub / blocked Layer3** language with a **live mixed simulator**. Naming used `canonical` without spelling out **execution-backed** semantics. A narrow parity pass was required to: verify true state, align vocabulary (`legacy_reference` vs `execution_backed`), stamp trade rows with `engine` + semantics versions, and record **synthetic** parity without broad research.

## 3. Starting true state

- `simulator.py`: **mixed** — lazy `legacy_reference` Numba + execution-backed adapter export (`simulate_combiner_canonical` = `simulate_combiner_execution_backed`).
- `run.py` / `sweep.py`: default **`legacy`** token → **`legacy_reference`** branch; **`canonical`** retained as alias for **`execution_backed`**.
- `NotImplementedError` blocker from an earlier stub state: **removed** in prior commit; this task did not reintroduce it.

## 4. File naming / scope discipline

- Single new research root: **`src/research/results/combiner_adapter_parity/`** only.
- No new `*_v2`, `canonical_v2`, `exit_overlay_v3`, or `combiner_adapter_v2` roots.
- New source files allowed by spec: **`src/research/run_combiner_adapter_parity.py`**, **`tests/test_combiner_adapter_parity.py`** only.

## 5. Adapter boundary

- **`trade_intent_adapter.py`:** builds `TradeIntent`, validates inputs, runs `simulate_trade_path` via `simulate_selected_trade`, maps `TradeResult` → row dict with `engine`, `execution_semantics_version`, `combiner_adapter_version`, `adapter_semantics_version`, `result_lineage`.
- **`adapter.py`:** sequential combiner loop, selection/state, returns `combiner_engine` + stamped `trades_df` rows (`engine=execution_backed`).
- **`simulator.py`:** `normalize_combiner_engine_label` for loud failure on typos; lazy legacy load; no silent cross-routing between engines.

## 6. Synthetic tests

- `tests/test_combiner_adapter_parity.py`: engine normalization, schema stamps, same-bar stop/target behavior, two-candidate priority, synthetic dual-engine smoke, `simulate_combiner_numba` callable.
- `tests/test_combiner_adapter.py` updated for `engine` / `adapter_semantics_version` expectations.

## 7. Real-data smoke

- Default: **NOT_RUN** — no committed QQQ parquet under `data/raw/ibkr` in this workspace.
- Optional: `python -m src.research.run_combiner_adapter_parity --try-real-smoke --candidate-root ... --config ... --candidate-ids ...` writes metrics-only summaries to `smoke/` using a **temp** output directory for full combiner artifacts.

## 8. Legacy vs execution-backed parity

- Curated synthetic comparison: **`parity/parity_summary.csv`** → label **`PARITY_PASS_WITH_EXPLAINED_DIFFS`** on the bundled toy matrix (legacy trade count **0**, execution-backed **1**).
- Exit-reason and candidate breakdowns: `parity_by_exit_reason.csv`, `parity_by_candidate.csv`.
- Known differences: `parity_known_differences.md` (includes toy-matrix observation).

## 9. Layer reachability

- See `layer_reachability.md` / `.csv`. Layer2 import paths **OK**. Layer3 imports **OK**; full fixed-profile dry-run **NOT_RUN** in this task.

## 10. Docs / handoff sync

- Updated: `docs/LAYER_FLOW.md`, `docs/MAINLINE_STRUCTURE_SUMMARY.md`, `docs/PROJECT_STRUCTURE.md`, `docs/FILE_OWNERSHIP.md`, `NEXT_HANDOFF.md`, `CHANGES.md`, `PROGRESS.md`, `PROJECT_STATUS.md`, `src/research/results/RESULTS_INDEX.md`.
- Removed stale claims that Layer3 is blocked by a simulator stub.

## 11. What remains blocked

- **Production router** and **production exit-management**: out of scope.
- **Exit overlay alignment on execution path**: **partial** — wait for real-slice parity or harness.
- **Exact legacy_reference ≡ execution_backed**: **not** claimed.

## 12. Decision

**`COMPLETE_COMBINER_ADAPTER_PARITY`** — see `combiner_adapter_parity_decision.md`.

## 13. Explicit non-runs

No WFO, mini-WFO, live/paper, SPY research, broad Layer2 sweeps, new strategies, Champion YAML edits, raw trade commits, parquet/npy commits, `git add .`.

## 14. Recommended next step

**`COMPLETE_COMBINER_ADAPTER_PARITY`** — build a tiny **real-data** dual-engine parity harness (same bars, same candidates, both engines) and reconcile top drift drivers.

## 15. Appendix: key tables

- `chatgpt_key_tables.csv` — section / item / metric / value / interpretation.
- `SOURCE_MAP.csv` — file_path / purpose / review flags.
