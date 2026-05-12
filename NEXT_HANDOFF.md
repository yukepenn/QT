# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Tip | After push, verify `git log -1 --oneline` matches `git ls-remote origin refs/heads/main`. |
| Working tree | Stage curated paths only — **never** `git add .` |

## B. Validation

| Check | Result (post repo-local parity) |
|--------|----------------------------------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **135** passed |
| `python -m src.strategies.loader --list` | OK |
| `python -m src.backtest.sweep --smoke` | OK |
| `python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend` | OK |
| `python -m src.combiner.run --help` | OK — `--engine` documents `legacy` / `legacy_reference` / `canonical` / `execution_backed` |
| `python -m src.research.run_combiner_adapter_parity --help` | OK — `--bar-root`, `--data-dir`, `--real-smoke-suite`, `--aggregate-only`, `--dry-run` |
| `python -m src.research.validate_research_artifacts --root src/research/results/combiner_adapter_parity --csv-only` | OK |

## C. Task scope

**Repo-local `data/`** (IBKR 1m shards under `data/raw/ibkr/`, ~34 MB, 104 parquet files) is **intentionally committed** for reproducible small-window QQQ research. **`.gitignore`** negates `*.parquet` only under that subtree. **`run_combiner_adapter_parity`** gained **`resolve_ibkr_data_dir`**, **`--bar-root`**, **`--real-smoke-suite`**, real dual-engine smoke + **`parity/real_data_parity_*`**. **`run_combiner_fixed_config`** supports **`return_trades_df`** for metrics-only smoke. No new versioned result roots beyond **`combiner_adapter_parity/`**.

## D. Data / bars

- **Path:** `data/raw/ibkr` (from `--bar-root data` or default).
- **QQQ Jan 2024 window:** **8190** bars, **21** NY sessions (see `repo_local_data_load_check.csv`).
- **Parquet outside `data/`:** still ignored by global `*.parquet` (do not commit research parquet elsewhere).

## E. Real smoke / parity

- **execution_backed** and **legacy_reference** both **OK** for 1- and 2-candidate Champion smoke (`smoke/real_*_smoke_summary.csv`).
- **Real parity label:** **`REAL_PARITY_PASS_WITH_EXPLAINED_DIFFS`** — identical trade counts; small `total_r` drift (`parity/real_data_parity_*`).
- **Synthetic toy matrix:** unchanged documented drift (`parity/parity_summary.csv`).

## F. Execution-backed readiness

**`EXECUTION_BACKED_READY_FOR_RESEARCH`** — see `src/research/results/combiner_adapter_parity/execution_backed_readiness.md`.

## G. Layer reachability

See `combiner_adapter_parity/layer_reachability.md` — real dual-engine Layer2 smoke **OK**; exit overlay on execution path **OK** to resume (research-only); router **BLOCKED**.

## H. Decision

**`RESUME_EXIT_OVERLAY_ON_EXECUTION_PATH`**

## I. Explicit non-runs / risks

No WFO, mini-WFO, live/paper, SPY research sweeps, broad Layer2 sweeps, Global Layer1, new strategies, Champion YAML edits, raw row-level trade panels, `top_runs` / `local_runs`, caches, logs, `git add .`, production router/exit-management, scalp/short.

## J. Files changed (high level)

`.gitignore`, `data/raw/ibkr/**`, `src/combiner/run.py`, `src/research/run_combiner_adapter_parity.py`, `tests/test_combiner_adapter_parity.py`, `src/research/results/combiner_adapter_parity/**`, `docs/LAYER_FLOW.md`, handoff/status/index docs.

## K. Local-only artifacts

Combiner full outputs still use **temp** dirs when running smoke; only **curated** CSV/MD under `combiner_adapter_parity/` plus committed **`data/`** bars.

## L. Recommended next step (exactly one)

**`RESUME_EXIT_OVERLAY_ON_EXECUTION_PATH`**
