# CLI capability check — Layer1 controlled (design task)

**Date:** 2026-05-11

## Questions → answers

| Question | Answer |
|----------|--------|
| Can current CLI run execution-backed Layer1 controlled sweep? | **Yes** — real-symbol sweep always uses **`simulate_trade_path`** via **`run_strategy_backtest`**. |
| Repo-local data root? | **Yes** — `--data-root data/raw/ibkr` (required together with strategy/symbol/start/end for real runs). |
| Single strategy? | **Yes** — `--strategy <name>`. |
| Output root? | **Yes** — `--output-root <path>`. |
| Dry-run? | **Yes** — `--dry-run` skips **`run_strategy_backtest`** accounting while still building signals. **Verified:** PA + QQQ + 4-day window + `--dry-run --max-combos 1` exits 0. |
| `--engine execution_backed`? | **No** — not a sweep flag; see **`runner_gap_analysis.md`**. |

## Gaps before “productionized” Layer1

- Candidate YAML / selection pipeline is **manual or script** (not in `sweep.py`).
- **`min_risk_per_share`** policy threading from YAML into **`default_intraday_policy`** in **`engine.py`** — recommended small code change in **run** task.
- Sweep **`engine`** column label **`reference`** vs research vocabulary **`execution_backed`** — document at YAML stamp time.

See **`cli_capability_check.csv`**.
