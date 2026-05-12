# Execution-backed readiness — post repo-local real smoke

## Label

**`EXECUTION_BACKED_READY_FOR_RESEARCH`**

## Rationale

- Repo-local **`data/raw/ibkr`** loads **8190** QQQ bars for **2024-01-01 … 2024-01-31** (21 NY sessions via `ts_ny`).
- **`execution_backed`** real smoke **OK** for 1- and 2-candidate Champion slices (`smoke/real_execution_backed_smoke_summary.csv`).
- Trade rows carry **`engine`**, **`execution_semantics_version`**, **`combiner_adapter_version`** when applicable (`smoke/real_execution_backed_schema_validation.csv`).
- Dual-engine comparison: **same trade counts**, small **`total_r`** drift vs **`legacy_reference`**, classified as **`execution_backed_design_choice`** / touch-fill semantics (`parity/real_data_parity_drift_classification.csv`).
- Heavy combiner outputs remain **temp-only**; **`--aggregate-only`** avoids compact trade CSV commits.

## Caveats

- **`legacy_reference`** remains the **default** combiner token in some CLIs for backward compatibility; research may opt into **`execution_backed`** explicitly.
- Synthetic toy matrix still shows structural legacy vs execution divergence — documented separately under `parity/parity_known_differences.md`.
- Layer3 fixed-profile dry-run **not** re-run here.

## Exit overlay / router

- Exit overlay can **resume on the execution-backed trade row shape** now that real smoke validates schema and non-empty metrics.
- Production router / exit-management: **still out of scope**.
