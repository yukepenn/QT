# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Tip | After push, verify `git log -1 --oneline` matches `git ls-remote origin refs/heads/main`. |
| Working tree | Stage curated paths only — **never** `git add .` |

## B. Validation

| Check | Result (post execution-backed hardening) |
|--------|------------------------------------------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **149** passed |
| `python -m src.strategies.loader --list` | OK |
| `python -m src.backtest.sweep --smoke` | OK |
| `python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend` | OK |
| `python -m src.combiner.run --help` | OK |
| `python -m src.combiner.sweep --help` | OK |
| `python -m src.research.run_combiner_adapter_parity --help` | OK |
| `python -m src.research.run_exit_overlay_execution_path --help` | OK |
| `python -m src.research.validate_research_artifacts --root src/research/results/execution_backed_hardening --csv-only` | OK → `execution_backed_hardening_artifact_validation.csv` (**17** CSVs scanned) |

## C. Task scope

**Execution-backed hardening (research / correctness):** `adapter` same-session next-bar entry; `state.reset_day` clears cooldown + open positions; **`ExecutionPolicy.min_risk_per_share`** + **`materialize`** `risk_too_small`; **`path`** scale-out uses **remaining** qty; **`tests/test_execution_backed_hardening.py`**. **No** new Numba engine, **no** WFO/broad sweeps/router/production exit-management.

## D. Data / candidate inputs

- Repo-local bars: **`data/raw/ibkr`** (optional smoke via `run_combiner_adapter_parity --try-real-smoke`).
- Smoke reference: `src/research/results/execution_backed_hardening/smoke/` (aggregate CSV/MD only; paths repo-relative in committed CSVs).

## E. Layer file map / cleanup

- Hardening touches **`src/combiner/adapter.py`**, **`state.py`**, **`trade_intent_adapter.py`**, **`src/execution/{types,policy,materialize,path,validators}.py`** only (plus tests/docs/results).
- Full inventories remain under **`combiner_adapter_parity/`** and **`exit_overlay_execution_path/`** from prior tasks.

## F. Hardening status

| Item | Status |
|------|--------|
| Same-session next-bar entry | **done** (`adapter`) |
| Cooldown reset on new session | **done** (`state.reset_day`) |
| `min_risk_per_share` on policy + materialize | **done** |
| Scale-out fraction semantics | **done** (remaining qty) |
| Fast-path acceleration | **planned only** (`fast_path_acceleration_plan.md`) |

## G. Overlay / parity context

- **Exit overlay on execution path:** complete — did not justify immediate **`src/management/`** promotion (`exit_overlay_execution_path/`).
- **Combiner adapter parity:** `EXECUTION_BACKED_READY_FOR_RESEARCH` unchanged as label; semantics **stricter** post-hardening (documented).

## H. Decision

**`DESIGN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`**

## I. Explicit non-runs / risks

No WFO/mini-WFO, live/paper, SPY sweeps, broad Layer1/Layer2, Global Layer1 rerun, router, production exit-management, short/scalp, Champion YAML edits, legacy delete/archive, second PnL engine, raw trade commits, `git add .`.

## J. Files changed (high level)

`src/combiner/adapter.py`, `state.py`, `trade_intent_adapter.py`, `src/execution/types.py`, `policy.py`, `materialize.py`, `path.py`, `validators.py`, `tests/test_execution_backed_hardening.py`, `src/research/results/execution_backed_hardening/**`, docs (`LAYER_FLOW`, `CANONICAL_COMBINER_DESIGN`, `MODULE_OWNERSHIP`, `MAINLINE_STRUCTURE_SUMMARY`, `PROJECT_STRUCTURE`, `EXECUTION_SEMANTICS`, `EXECUTION_TEST_MATRIX_SUMMARY`, `README`), `RESULTS_INDEX.md`, `NEXT_HANDOFF.md`, `PROJECT_STATUS.md`, `PROGRESS.md`, `CHANGES.md`.

## K. Local-only artifacts

None required beyond standard temp dirs for combiner runs; smoke outputs under `execution_backed_hardening/smoke/` are **aggregates only** (no row-level trade dumps in this commit).

## L. Recommended next step (exactly one)

**`DESIGN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`**
