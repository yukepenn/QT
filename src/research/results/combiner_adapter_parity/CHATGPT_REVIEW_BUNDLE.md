# CHATGPT_REVIEW_BUNDLE — combiner_adapter_parity

Readable raw bundle for external review. Repo: `https://github.com/yukepenn/QT`.

## 1. Git / validation

- Branch: `main` (at commit time of this bundle).
- `python -m compileall -q src`: OK.
- `python -m pytest -q`: **135** tests passed (includes `tests/test_combiner_adapter_parity.py` + `resolve_ibkr_data_dir` checks).
- Layer1: `python -m src.backtest.sweep --smoke` and `--validate-pipeline --strategy pa_buy_sell_close_trend`: OK.
- Combiner CLI: `python -m src.combiner.run --help` / `sweep --help`: OK; documents `--engine` tokens.
- Parity runner: `python -m src.research.run_combiner_adapter_parity --help` — **`--bar-root`**, **`--data-dir`**, **`--real-smoke-suite`**, **`--aggregate-only`**, **`--dry-run`**.
- Artifact scan: `python -m src.research.validate_research_artifacts --root src/research/results/combiner_adapter_parity --csv-only` → `combiner_adapter_parity_artifact_validation.csv`.

## 2. Why repo-local `data/` is committed

Reproducible **small-window** QQQ (and co-located SPY) IBKR 1m bar shards under **`data/raw/ibkr/`** (~34 MB total, no file near GitHub limits) remove reliance on **`D:\TradingData`** or other external roots for the combiner parity smoke in CI and fresh clones. Global **`*.parquet`** remains ignored except this subtree via explicit **`!data/raw/ibkr/**/*.parquet`** (see `data_git_tracking_plan.*`).

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

## 7. Data folder audit

- Summary: `data_folder_audit.md`, `data_folder_audit_summary.csv`, per-file `data_folder_audit.csv` (**104** parquet files, ~**34.3** MB, largest **~0.41** MB).
- **Safe to commit:** yes (under 95 MB/file policy).

## 8. Candidate inventory (smoke)

- **Root used:** `src/research/results/Archive/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates` (auto-discovered).
- **Config:** `src/combiner/configs/Archive/layer2_qqq_global_2023_2024_v2.yaml`.
- **IDs:** `PA_BUY_SELL_CLOSE_TREND_003` and two-candidate with `GAP_ACCEPTANCE_FAILURE_001`.

## 9. Execution-backed real smoke

- Bar root: **`data`** → resolved `data/raw/ibkr`.
- Window: **2024-01-01 … 2024-01-31**, symbol **QQQ**.
- Metrics: `smoke/real_execution_backed_smoke_summary.csv` + `.md`, manifests + schema validation CSVs.

## 10. Legacy-reference real smoke

- Same inputs as §9. Metrics: `smoke/real_legacy_reference_smoke_summary.csv` + `.md`.

## 11. Real-data parity / reconciliation

- **`REAL_PARITY_PASS_WITH_EXPLAINED_DIFFS`** — `parity/real_data_parity_summary.csv` / `.md`.
- By candidate / exit / bars held / drift classification: `parity/real_data_parity_by_*.csv`, `parity/real_data_parity_known_differences.md`, `parity/real_data_parity_drift_classification.csv`.
- Synthetic toy matrix parity unchanged: `parity/parity_summary.csv` (**legacy 0** vs **execution 1** trades) per `parity_known_differences.md`.

## 12. Execution-backed readiness

- Label: **`EXECUTION_BACKED_READY_FOR_RESEARCH`** (`execution_backed_readiness.md` / `.csv`).

## 13. Layer reachability

- Updated `layer_reachability.md` / `.csv` — real dual-engine smoke **OK**; exit overlay dependency **OK** (research resume); router **BLOCKED**.

## 14. Decision

**`RESUME_EXIT_OVERLAY_ON_EXECUTION_PATH`** — see `combiner_adapter_parity_decision.md`.

## 15. Explicit non-runs

No WFO, mini-WFO, live/paper, SPY *research sweeps*, broad Layer2 sweeps, new strategies, Champion YAML edits, raw trade row commits, `top_runs` / `local_runs`, caches, logs, `git add .`. **Exception:** parquet **only** under repo `data/raw/ibkr/` is committed intentionally.

## 16. Recommended next step

**`RESUME_EXIT_OVERLAY_ON_EXECUTION_PATH`** — continue exit-overlay diagnostics using **execution-backed** combiner trade rows (research-only); migrate Layer1/2/3 defaults toward execution-backed accounting incrementally as separate work.

## 17. Appendix: key tables

- `chatgpt_key_tables.csv` — section / item / metric / value / interpretation.
- `SOURCE_MAP.csv` — file_path / purpose / review flags.
