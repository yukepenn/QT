# Real-data combiner smoke — not run

Per task constraints (no broad Layer2 research, no guaranteed local QQQ parquet in CI), a one-month QQQ canonical combiner smoke was **not** executed.

To run locally when data and YAML exist:

```bash
python -m src.combiner.run \
  --candidate-root <path/to/selected_candidates> \
  --config <combiner.yaml> \
  --symbol QQQ --start 2024-01-01 --end 2024-01-31 \
  --engine canonical --dry-run
```

Do not commit `trades.csv` or row-level outputs from exploratory runs.
