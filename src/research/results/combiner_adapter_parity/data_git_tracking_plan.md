# Git tracking plan — repo-local `data/`

| Field | Value |
|--------|--------|
| Ignored before | Global `*.parquet`; former blanket `data/raw/` (removed) |
| `.gitignore` change | **yes** — remove `data/raw/` blanket ignore; append `!data/raw/ibkr/**/*.parquet` with comment (May 2026 intentional small dataset) |
| Files to stage | `data/**` (104 parquet shards under `data/raw/ibkr/`) |
| Files excluded | `data/cache/`, `local_runs/**`, `top_runs/**`, sweep outputs, logs, npy/npz/memmap, trade CSVs outside `data/` |
| Rationale | Reproducible QQQ (and co-located SPY) 1m RTH research without external `D:\` data roots |

## Verification

`git check-ignore -q` on a sample QQQ shard exits **1** (path is **not** ignored after negation).
