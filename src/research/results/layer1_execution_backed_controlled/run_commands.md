# Run commands — Layer1 execution-backed controlled

All commands assume **repository root** as current directory. Use **`data/raw/ibkr`** only.

**Preferred minimal proof (balanced grids, no `--max-combos` truncation)**

- Grids: `src/strategies/testing_parameters/*_minimal_proof.yaml`
- Sweeps: add **`--checkpoint-every 1`**; use **`--resume`** to continue after interrupt.
- Promotion: filter with **`--include-run-name-contains minimal_proof`** and gate **`L1_EXECUTION_BACKED_MINIMAL_PROOF`** (candidate IDs **`*_L1M_*`**).

**Environment template**

- `DATA_ROOT=data/raw/ibkr`
- `SYMBOL=QQQ`
- `ASSET=equity`
- `START=2023-01-01`
- `END=2024-12-31`
- `OUT_BASE=src/research/results/layer1_execution_backed_controlled/runs`
- `CANDIDATE_ROOT=src/strategies/testing_parameters_results/l1_execution_backed_controlled`

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

## 3) PA — minimal proof sweep (40 combos total across PA/GAP/CCI)

```bash
python -m src.backtest.sweep --strategy pa_buy_sell_close_trend --symbol QQQ --asset equity --start %START% --end %END% --data-root %DATA_ROOT% --grid src/strategies/testing_parameters/pa_buy_sell_close_trend_minimal_proof.yaml --output-root %OUT_BASE%/pa_buy_sell_close_trend_2023_2024_minimal_proof --checkpoint-every 1
python -m src.backtest.sweep --strategy gap_acceptance_failure --symbol QQQ --asset equity --start %START% --end %END% --data-root %DATA_ROOT% --grid src/strategies/testing_parameters/gap_acceptance_failure_minimal_proof.yaml --output-root %OUT_BASE%/gap_acceptance_failure_2023_2024_minimal_proof --checkpoint-every 1
python -m src.backtest.sweep --strategy cci_extreme_snapback --symbol QQQ --asset equity --start %START% --end %END% --data-root %DATA_ROOT% --grid src/strategies/testing_parameters/cci_extreme_snapback_minimal_proof.yaml --output-root %OUT_BASE%/cci_extreme_snapback_2023_2024_minimal_proof --checkpoint-every 1
```

## 4) GAP — minimal proof (see §3)

## 5) CCI — minimal proof (see §3)

## 6) Validate empty candidate root (README-only)

```bash
python -m src.research.run_layer1_execution_backed_controlled validate-candidates --candidate-root %CANDIDATE_ROOT% --allow-empty
```

## 7) Promote — dry-run (minimal proof runs only)

```bash
python -m src.research.run_layer1_execution_backed_controlled promote --runs-root %OUT_BASE% --include-run-name-contains minimal_proof --candidate-root %CANDIDATE_ROOT% --max-per-strategy 2 --min-trades 10 --min-profit-factor-r 1.02 --min-total-r 0.0 --gate-label L1_EXECUTION_BACKED_MINIMAL_PROOF
```

## 8) Promote — write YAML + CSV indices

```bash
python -m src.research.run_layer1_execution_backed_controlled promote --runs-root %OUT_BASE% --include-run-name-contains minimal_proof --candidate-root %CANDIDATE_ROOT% --max-per-strategy 2 --min-trades 10 --min-profit-factor-r 1.02 --min-total-r 0.0 --gate-label L1_EXECUTION_BACKED_MINIMAL_PROOF --write
```

## 9) Re-validate candidates (loads every `*.yaml`)

```bash
python -m src.research.run_layer1_execution_backed_controlled validate-candidates --candidate-root %CANDIDATE_ROOT%
```

## 10) Artifact validation (curated roots)

```bash
python -m src.research.validate_research_artifacts --root src/research/results/layer1_execution_backed_controlled --csv-only --output src/research/results/layer1_execution_backed_controlled/layer1_execution_backed_controlled_artifact_validation.csv
```

## 11) Tracked-heavy check (PowerShell)

```powershell
git ls-files | Select-String -Pattern "top_runs|trades.csv|compact_trades|enriched.csv|scored_trades|trade_context_panel.csv|overlay_trade_results|local_rows|local_runs|\.npy|\.npz|\.memmap"
```

## 12) Parquet tracking (bash style)

```bash
git ls-files | grep -E "\.parquet$|data\.parquet$" || true
```

## 13) Commit / push checklist (after run task)

- `git status --short`
- Explicit `git add` on curated CSV/MD/YAML only
- Forbidden pattern scan on `git diff --cached --name-only`
- `git commit -m "..."` / `git push origin main`

**Note:** There is **no** `--engine execution_backed` flag on `backtest.sweep`; accounting is always **`simulate_trade_path`** for real runs. See **`runner_gap_analysis.md`**.
