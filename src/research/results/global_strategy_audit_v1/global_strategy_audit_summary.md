# Global strategy audit summary (v1)

- Strategies audited: **35**
- `READY_GLOBAL_L1`: **28**
- `READY_LONG_ONLY`: **0**
- `READY_SHORT_OR_BOTH`: **2**
- `REVIEW_GRID_TOO_LARGE` (raw grid > 1500): **5**
- `DEFER_IMPLEMENTATION_RISK`: **0**

Artifacts:

- `strategy_eligibility_matrix.csv` / `.md`
- `strategy_side_support_matrix.csv` / `.md`

Policy: no short axes are invented; unknown side grids default to **READY_LONG_ONLY**.

Next: run `python src/research/run_global_layer1.py` with `--audit` pointing at the CSV.
