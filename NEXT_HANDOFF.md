# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Tip | After push, verify `git log -1 --oneline` matches `git ls-remote origin refs/heads/main`. |
| Working tree | Stage curated paths only — **never** `git add .` |

## B. Validation

| Check | Result (post Layer1 controlled design) |
|--------|----------------------------------------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **149** passed |
| `python -m src.strategies.loader --list` | OK (**35** strategies) |
| `python -m src.backtest.sweep --help` | OK (`sweep.py` now runs **`main()`** under `python -m`) |
| `python -m src.backtest.sweep --smoke` | OK |
| `python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend` | OK |
| `python -m src.backtest.sweep --dry-run` (PA, QQQ, short window, `--max-combos 1`) | OK |
| `python -m src.combiner.run --help` | OK |
| `python -m src.combiner.sweep --help` | OK |
| `python -m src.research.validate_research_artifacts --root src/research/results/layer1_execution_backed_controlled --csv-only` | OK → `layer1_execution_backed_controlled_artifact_validation.csv` (**14** paths) |

## C. Task scope

**Design-only package:** **`src/research/results/layer1_execution_backed_controlled/`** — controlled execution-backed Layer1 rebuild **design** (pipeline map, data window, three strategies, grids + caps, candidate schema, execution policy, runbooks, CLI capability, validation gates, ChatGPT bundle). **No** broad Layer1/Layer2/Layer3 runs, **no** WFO, **no** new strategy families, **no** Numba fast path, **no** raw trade commits.

**Small code fix in same work:** `src/backtest/sweep.py` **`if __name__ == "__main__"`** so documented **`python -m src.backtest.sweep`** invocations actually run **`main()`** (tests already called **`sweep.main`** directly).

## D. Layer1 pipeline state

Mainline: **`read_bars`** → **`strategy_runner`** → **`run_strategy_backtest`** → **`simulate_trade_path`** → **`summarize_trades`**. Only **`src/execution/`** owns accounting. Sweep result column **`engine=reference`** is legacy naming for the mainline path (not combiner **`legacy_reference`**). See **`layer1_pipeline_state.md`**.

## E. Data / strategy / grid design

- **Data:** repo-local **`data/raw/ibkr`**, **QQQ** 1m, committed years **2020–2026**; preferred first run window **2023-01-01 .. 2024-12-31** (fallback **2024 H1**).
- **Strategies (first pass):** **`pa_buy_sell_close_trend`**, **`gap_acceptance_failure`**, **`cci_extreme_snapback`** with focused YAMLs; cap with **`--max-combos`** (**64** / **64** / **32**).
- **Optional later:** VWAP reclaim/reject, VWAP trend pullback, failed ORB, ORB continuation — documented only, **not** first run.

## F. Candidate schema

Future outputs under **`.../selected_candidates/`** (reserved **`README.md`** only in git now). Required stamps: **`execution_engine`** (use **`execution_backed`** in YAML), semantics version, policy/config hashes, **`data_root=data/raw/ibkr`**, window, **`layer=1`**, selection gate, metric summary. See **`candidate_artifact_schema.md`**.

## G. CLI capability / runner gaps

- **Can run controlled sweeps:** yes — **`--strategy`**, **`--symbol`**, **`--start`**, **`--end`**, **`--data-root`**, **`--grid`**, **`--output-root`**, **`--max-combos`**, **`--dry-run`**.
- **No `--engine` on Layer1 sweep:** accounting is always **`simulate_trade_path`** for real runs; stamp YAML separately.
- **Selection / YAML promotion:** not in `sweep.py` — follow-up script or thin **`run_layer1_execution_backed_controlled.py`** if needed.
- **`min_risk_per_share` on policy:** `run_strategy_backtest` should thread **`risk.min_risk_per_share`** into **`default_intraday_policy`** in the **run** task (documented in **`execution_policy_design.csv`**).

## H. Decision

**`RUN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`**

## I. Explicit non-runs / risks

No broad Layer1/Layer2/Layer3, WFO, live/paper, SPY sweeps, router, production exit-management, new strategy families, signal semantic edits, champion YAML edits, legacy delete/archive, second PnL engine, Numba accounting in `fast_path`, forbidden heavy artifacts, **`git add .`**. Avoid committing **`runs/`** sweep outputs until curated post-selection.

## J. Files changed (high level)

`src/backtest/sweep.py` (**`__main__`** guard), `src/research/results/layer1_execution_backed_controlled/**`, `NEXT_HANDOFF.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`, `RESULTS_INDEX.md`, `docs/LAYER_FLOW.md`, `docs/MAINLINE_STRUCTURE_SUMMARY.md` (if touched).

## K. Local-only artifacts

Standard optional **`runs/`** under the result root for future sweeps — **gitignore or omit** until curated aggregates exist.

## L. Recommended next step (exactly one)

**`RUN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`**
