# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Tip | After push, verify `git log -1 --oneline` matches `origin/main`. |
| Working tree | Stage curated paths only — **never** `git add .` |

## B. Validation

| Check | Result (post combiner adapter v1) |
|--------|-------------------------------------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **125** passed |
| `python -m src.strategies.loader --list` | **35** strategies |
| `python -m src.backtest.sweep --smoke` | OK |
| `python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend` | exit 0 |
| `python -m src.combiner.run --help` | shows `--engine`, `--dry-run` |

## C. Task scope

Execution-backed **Layer 2 combiner adapter** (`TradeIntent` → `simulate_trade_path`) with **lazy legacy** Numba compatibility; CLI `--engine`; synthetic tests; curated research bundle under `src/research/results/combiner_adapter_v1/`.

## D. Starting architecture state

- Prior: `simulate_combiner_numba` stubbed → `NotImplementedError` blocked `run.py` / `sweep.py`.
- Legacy reference only on disk under `archive/legacy_combiner/reference_simulator.py`.

## E. Adapter implementation

- `src/combiner/trade_intent_adapter.py` — build intent, policy bridge, `trade_result_to_combiner_row`.
- `src/combiner/adapter.py` — `simulate_combiner_canonical` (sequential loop + selection/state).
- `src/combiner/simulator.py` — lazy legacy load (`sys.modules` registration for dataclasses); `simulate_combiner_numba` → legacy alias; `simulate_combiner_canonical` export.
- `src/combiner/run.py`, `src/combiner/sweep.py` — `--engine legacy|canonical`; `run_combiner_fixed_config(..., engine="legacy")` default.
- `src/research/validate_research_artifacts.py` — lightweight CSV scan helper.
- `src/research/run_combiner_adapter_smoke.py` — thin canonical+dry-run forwarder.

## F. Tests / smoke / parity

- `tests/test_combiner_adapter.py` — synthetic target/stop/max-hold, schema stamps, minimal canonical combiner smoke.
- Simulator tests updated for lazy legacy + canonical export.
- Real QQQ smoke: **not run** (`smoke_not_run_reason.md`).
- Parity legacy vs canonical: **PARITY_NOT_RUN** (`parity/`).

## G. Layer2 / Layer3 reachability

- Layer2 legacy path **restored** (no `NotImplementedError` on import/call when archive present).
- Layer2 canonical path **available** via `--engine canonical` or `engine=` kwarg.
- Layer3 / mini-WFO: **not run**; walkforward still defaults to **legacy** engine until parity.

## H. Decision

**`COMPLETE_COMBINER_ADAPTER_V2`**

## I. Explicit non-runs / risks

No WFO, mini-WFO, live/paper, SPY, broad Layer2 sweeps, new strategies, Champion YAML edits, raw trade commits, production router/exit-management.

Risks: canonical sequential adapter **does not** replicate full legacy matrix semantics; switching Layer3 to canonical without parity is unsafe.

## J. Files changed (high level)

`src/combiner/{adapter,trade_intent_adapter,simulator,run,sweep}.py`, `tests/test_combiner_adapter.py`, simulator tests, `docs/{LAYER_FLOW,FILE_OWNERSHIP,MAINLINE_STRUCTURE_SUMMARY,PROJECT_STRUCTURE}.md`, `src/research/*`, `src/research/results/combiner_adapter_v1/**`, status docs.

## K. Local-only artifacts

None committed beyond small curated CSV/MD under `combiner_adapter_v1/`.

## L. Recommended next step (exactly one)

**`COMPLETE_COMBINER_ADAPTER_V2`**
