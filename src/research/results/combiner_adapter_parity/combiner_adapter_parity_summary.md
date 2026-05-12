# combiner_adapter_parity — summary

## Outcomes

- **Engine vocabulary:** `normalize_combiner_engine_label` maps `legacy` / `legacy_reference` / `numba` → `legacy_reference`; `canonical` / `execution_backed` → `execution_backed`. CLI `--engine` validates via the same helper (loud `ValueError` on typos).
- **Row stamps:** execution-backed trade rows include `engine`, `adapter_semantics_version`, `execution_semantics_version`, `result_lineage`, `combiner_adapter_version`. Legacy outputs gain `engine=legacy_reference` when returned through `run_combiner_fixed_config` / CLI (column stamped post-sim).
- **Synthetic parity:** `parity/*` retains **PARITY_PASS_WITH_EXPLAINED_DIFFS** on the built-in toy matrix (legacy trade count may be **0** while execution-backed emits **1** — documented in `parity_known_differences.md`).
- **Repo-local data:** **`data/raw/ibkr`** committed intentionally (small IBKR 1m shards for **QQQ** and **SPY**; all files < 1 MB each; ~34 MB total). Global `*.parquet` ignore is negated only under this subtree (`.gitignore`).
- **Real QQQ smoke (Jan 2024):** `--try-real-smoke --bar-root data --aggregate-only --real-smoke-suite` runs **execution_backed** and **legacy_reference** for 1- and 2-candidate Champion IDs; curated metrics under `smoke/real_*` and reconciliation under `parity/real_data_parity_*`.
- **Real parity label:** **`REAL_PARITY_PASS_WITH_EXPLAINED_DIFFS`** — same trade counts; small `total_r` drift classified **`execution_backed_design_choice`** in `parity/real_data_parity_drift_classification.csv`.
- **Tests:** `tests/test_combiner_adapter_parity.py` includes `resolve_ibkr_data_dir` checks; **135** `pytest` total at this tip.
- **Decision:** **`RESUME_EXIT_OVERLAY_ON_EXECUTION_PATH`** (`combiner_adapter_parity_decision.md`).
- **Readiness:** **`EXECUTION_BACKED_READY_FOR_RESEARCH`** (`execution_backed_readiness.md`).

## Non-goals (unchanged)

Production router, production exit management, scalp/short, WFO, live trading, SPY *research sweeps*, broad Layer2 research, `git add .`, row-level trade CSV commits.
