# Validation results

| Check | Result |
|-------|--------|
| compileall | OK |
| pytest | **163** passed |
| `run_layer1_execution_backed_controlled --help` | OK |
| `validate-candidates --allow-empty` on README-only candidate root | OK |
| `validate_research_artifacts` (alignment root, `--csv-only`) | OK → **8** rows in **`artifact_validation.csv`** |
| `validate_research_artifacts` (controlled design root) | OK → **14** rows in **`layer1_execution_backed_controlled_artifact_validation.csv`** |

Tracked-heavy / parquet: legacy **Archive** paths still match grep patterns (historical); active parquet under **`data/raw/ibkr/**`** includes committed **QQQ** and **SPY** months (repo baseline — do not expand SPY research in controlled Layer1).

See **`validation_results.csv`**.
