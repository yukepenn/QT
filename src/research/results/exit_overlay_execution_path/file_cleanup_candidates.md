# File cleanup candidates (inventory only)

This CSV classifies paths for **future** hygiene. **No deletes, moves, or archives** were performed in this task.

High level:

- **Legacy / Archive trees** remain **`compatibility_reference`** until Layer1/2/3 are rebuilt under **`execution_backed`** accounting.
- **`_local_only/`** under the exit-overlay result root holds precompute CSV/JSON and per-trade replay tables — **gitignored**; safe to delete locally anytime.

See `file_cleanup_candidates.csv`.
