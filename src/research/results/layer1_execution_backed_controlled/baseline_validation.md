# Baseline validation — Layer1 controlled design

Machine-readable rows: **`baseline_validation.csv`**.

Design-time checks: **`compileall`**, **`pytest` (149)**; **`python -m src.backtest.sweep`** help, smoke, validate-pipeline, and PA/QQQ **`--dry-run`** (see csv).

`validate_research_artifacts` on this design root: **14** path rows → **`layer1_execution_backed_controlled_artifact_validation.csv`** (includes self-row).

Tracked-heavy / parquet expectations match prior handoffs (historical Archive noise allowed; parquet only under `data/raw/ibkr`).
