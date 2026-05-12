# combiner_adapter_parity — summary

## Outcomes

- **Engine vocabulary:** `normalize_combiner_engine_label` maps `legacy` / `legacy_reference` / `numba` → `legacy_reference`; `canonical` / `execution_backed` → `execution_backed`. CLI `--engine` validates via the same helper (loud `ValueError` on typos).
- **Row stamps:** execution-backed trade rows include `engine`, `adapter_semantics_version`, `execution_semantics_version`, `result_lineage`, `combiner_adapter_version`. Legacy outputs gain `engine=legacy_reference` when returned through `run_combiner_fixed_config` / CLI (column stamped post-sim).
- **Synthetic parity:** `run_combiner_adapter_parity` + `parity/*` show **PARITY_PASS_WITH_EXPLAINED_DIFFS** on the built-in toy matrix (legacy trade count may be **0** while execution-backed emits **1** — documented).
- **Tests:** `tests/test_combiner_adapter_parity.py` added (133 total `pytest` after this change).
- **Research bundle:** this folder + `CHATGPT_REVIEW_BUNDLE.md`, `SOURCE_MAP.csv`, `chatgpt_key_tables.csv`, `combiner_adapter_parity_key_findings.csv`.

## Non-goals (unchanged)

Production router, production exit management, scalp/short, WFO, SPY, broad Layer2 research.
