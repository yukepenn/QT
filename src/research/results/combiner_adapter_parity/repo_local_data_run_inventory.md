# Repo-local data parity run — inventory

| Field | Value |
|--------|--------|
| Git tip before this work | `c2e94bf0ac08ebd216185a0759ac039e63490943` |
| Prior NEXT_HANDOFF decision | `COMPLETE_COMBINER_ADAPTER_PARITY` |
| Interrupted run artifacts | **No** — no partial `local_runs` / `top_runs` / sweep dirs staged |
| Action on artifacts | N/A |
| Result root | `src/research/results/combiner_adapter_parity/` |
| Repo-local data path | `data/` → bars at `data/raw/ibkr/` (QQQ + SPY IBKR 1m shards) |
| Explicit non-goals | No WFO / mini-WFO / live / paper / SPY research runs / broad Layer2 / Global L1 / new strategies / router or production exit-management / scalp-short / `git add .` / row-level trade panels / caches / logs |

## Commands used (real smoke)

```text
python -m src.research.run_combiner_adapter_parity --try-real-smoke --bar-root data --aggregate-only --real-smoke-suite --skip-synthetic-parity
```

Dry bar load uses `read_bars` via `run_bar_load_check` inside the same entrypoint when `--try-real-smoke` is set (non-`--dry-run` runs load then combiner).
