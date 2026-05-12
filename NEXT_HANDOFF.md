# NEXT_HANDOFF

## A. Git

| Field | Value |
|--------|--------|
| Branch | `main` |
| Tip | After push, verify `git log -1 --oneline` matches `git ls-remote origin refs/heads/main`. |
| Working tree | Stage curated paths only — **never** `git add .` |

## B. Validation

| Check | Result (post combiner_adapter_parity) |
|--------|----------------------------------------|
| `python -m compileall -q src` | OK |
| `python -m pytest -q` | **133** passed |
| `python -m src.strategies.loader --list` | OK |
| `python -m src.backtest.sweep --smoke` | OK |
| `python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend` | OK |
| `python -m src.combiner.run --help` | OK — `--engine` documents `legacy` / `legacy_reference` / `canonical` / `execution_backed` |
| `python -m src.research.run_combiner_adapter_parity` | OK — refreshes `parity/` + default `smoke/` |
| `python -m src.research.validate_research_artifacts --root src/research/results/combiner_adapter_parity --csv-only` | OK |

## C. Task scope

Narrow **`combiner_adapter_parity`** pass: verify true combiner state, align docs/handoff, add **`normalize_combiner_engine_label`**, stamp **`engine`** + semantics columns, synthetic parity bundle under **`src/research/results/combiner_adapter_parity/`**, tests in **`tests/test_combiner_adapter_parity.py`**, research runner **`run_combiner_adapter_parity.py`**. No new versioned result roots beyond that folder.

## D. Starting architecture state

- Prior docs still implied Layer3 blocked by a simulator **stub**; code was already **mixed** (lazy `legacy_reference` + `execution_backed` adapter).
- CLI used `legacy|canonical` only; **`execution_backed`** / **`legacy_reference`** names were not first-class.

## E. Adapter / engine implementation

- **`normalize_combiner_engine_label`** in `src/combiner/simulator.py` — maps synonyms; **`ValueError`** on unknown engines.
- **`simulate_combiner_execution_backed`** — public alias of **`simulate_combiner_canonical`** (same object in `simulator` module).
- **`trade_result_to_combiner_row`** — adds **`engine`**, **`adapter_semantics_version`** (defaults to adapter version).
- **`adapter.simulate_combiner_canonical`** return dict includes **`combiner_engine`** = `execution_backed`.
- **`run.py` / `sweep.py`** — validate `--engine` with shared parser; **`run_combiner_fixed_config`** stamps **`engine=legacy_reference`** on legacy `trades_df` when missing.

## F. Tests / smoke / parity

- **`tests/test_combiner_adapter_parity.py`** — normalization, schema, same-bar policy, dual-engine synthetic matrices, priority selection.
- **Synthetic parity (committed):** `parity/parity_summary.csv` → **`PARITY_PASS_WITH_EXPLAINED_DIFFS`** (toy matrix: legacy **0** trades vs execution-backed **1** — documented).
- **Real QQQ smoke:** default **NOT_RUN** (`smoke/`); optional **`--try-real-smoke`** uses temp dir for combiner outputs, metrics only to `smoke_summary*`.

## G. Layer2 / Layer3 reachability

- Layer2: **no** `NotImplementedError` on simulator import path (archive present).
- Layer2 **execution_backed**: available via CLI / `engine=` kwarg.
- Layer3: **imports OK**; default combiner engine in walkforward-style callers remains **`legacy_reference`** until parity sign-off. Full Layer3 dry-run **not** run here.

## H. Decision

**`COMPLETE_COMBINER_ADAPTER_PARITY`**

## I. Explicit non-runs / risks

No WFO, mini-WFO, live/paper, SPY, broad Layer2 sweeps, new strategies, Champion YAML edits, raw trade commits, production router/exit-management, scalp/short.

**Risk:** Treating synthetic parity as sufficient — real-slice parity still required before switching Layer3 default engine or resuming exit-overlay alignment on execution rows.

## J. Files changed (high level)

`src/combiner/{simulator,trade_intent_adapter,adapter,run,sweep,selection}.py`, `src/research/run_combiner_adapter_parity.py`, `tests/test_combiner_adapter_parity.py`, `tests/test_combiner_adapter.py`, simulator tests, `docs/{LAYER_FLOW,MAINLINE_STRUCTURE_SUMMARY,PROJECT_STRUCTURE,FILE_OWNERSHIP}.md`, `src/research/results/combiner_adapter_parity/**`, `src/research/results/RESULTS_INDEX.md`, `src/research/run_combiner_adapter_smoke.py`, status docs.

## K. Local-only artifacts

None committed beyond small curated CSV/MD under `combiner_adapter_parity/` (detailed combiner runs use temp dirs when `--try-real-smoke`).

## L. Recommended next step (exactly one)

**`COMPLETE_COMBINER_ADAPTER_PARITY`**
