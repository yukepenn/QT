# Layer file map (summary)

Machine-readable rows: `layer_file_map.csv`.

**Accounting ownership:** only **`src/execution/`** (especially **`path.py`**, **`pnl.py`**, **`fill.py`**, **`exits.py`**, **`materialize.py`**, **`policy.py`**) should own intrabar fill, exit sequencing, and R/PnL math. Layer1/2/3 may **aggregate** execution outputs but must not introduce parallel definitions.

**Layer2 engines:** `legacy_reference` remains for compatibility; **`execution_backed`** is the research-forward path (`combiner/adapter.py` → `simulate_trade_path`).

**Layer3:** walkforward harnesses orchestrate windows; this task **did not** run WFO.
