# Run commands — controlled Layer1 (next task; **do not execute** full sweeps here)

All commands assume **repository root** as current directory. Use **`data/raw/ibkr`** only.

**Environment template**

- `DATA_ROOT=data/raw/ibkr`
- `SYMBOL=QQQ`
- `ASSET=equity`
- `START=2023-01-01`
- `END=2024-12-31`
- `OUT_BASE=src/research/results/layer1_execution_backed_controlled/runs`

## 1) Preflight

```bash
python -m compileall -q src
python -m pytest -q
python -m src.strategies.loader --list
python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend --symbol QQQ --start 2024-01-02 --end 2024-01-05 --data-root data/raw/ibkr
```

## 2) Dry-run smoke (no accounting; fast)

```bash
python -m src.backtest.sweep --strategy pa_buy_sell_close_trend --symbol QQQ --start 2024-01-02 --end 2024-01-05 --data-root data/raw/ibkr --dry-run --max-combos 1
```

## 3) PA — controlled sweep (real accounting; capped)

```bash
python -m src.backtest.sweep --strategy pa_buy_sell_close_trend --symbol QQQ --asset equity --start %START% --end %END% --data-root %DATA_ROOT% --grid src/strategies/testing_parameters/pa_buy_sell_close_trend_focused.yaml --max-combos 64 --output-root %OUT_BASE%/pa_buy_sell_close_trend_2023_2024_m64
```

## 4) GAP — controlled sweep

```bash
python -m src.backtest.sweep --strategy gap_acceptance_failure --symbol QQQ --asset equity --start %START% --end %END% --data-root %DATA_ROOT% --grid src/strategies/testing_parameters/gap_acceptance_failure_focused.yaml --max-combos 64 --output-root %OUT_BASE%/gap_acceptance_failure_2023_2024_m64
```

## 5) CCI — controlled sweep (full grid fits cap)

```bash
python -m src.backtest.sweep --strategy cci_extreme_snapback --symbol QQQ --asset equity --start %START% --end %END% --data-root %DATA_ROOT% --grid src/strategies/testing_parameters/cci_extreme_snapback_focused.yaml --max-combos 32 --output-root %OUT_BASE%/cci_extreme_snapback_2023_2024_m32
```

## 6) Postprocess / selection (next task)

Not implemented in `sweep.py` — implement as small script or **`src/research/run_layer1_execution_backed_controlled.py`** in a follow-up: read `sweep_results.csv`, apply gates, emit `selected_candidates/` + summaries. **Design only** here.

## 7) Artifact validation (curated roots)

```bash
python -m src.research.validate_research_artifacts --root src/research/results/layer1_execution_backed_controlled --csv-only --output src/research/results/layer1_execution_backed_controlled/layer1_execution_backed_controlled_artifact_validation.csv
```

## 8) Tracked-heavy check (PowerShell)

```powershell
git ls-files | Select-String -Pattern "top_runs|trades.csv|compact_trades|enriched.csv|scored_trades|trade_context_panel.csv|overlay_trade_results|local_rows|local_runs|\.npy|\.npz|\.memmap"
```

## 9) Parquet tracking (bash style)

```bash
git ls-files | grep -E "\.parquet$|data\.parquet$" || true
```

## 10) Commit / push checklist (after run task)

- `git status --short`
- Explicit `git add` on curated CSV/MD/YAML only
- Forbidden pattern scan on `git diff --cached --name-only`
- `git commit -m "..."` / `git push origin main`

**Note:** There is **no** `--engine execution_backed` flag on `backtest.sweep`; accounting is always **`simulate_trade_path`** for real runs. See **`runner_gap_analysis.md`**.
