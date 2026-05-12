# CHATGPT_REVIEW_BUNDLE — combiner adapter v1

## 1. Git / validation

- Baseline tip documented: `4da3ed1` (structure consolidation).
- Post-change: `compileall` OK; `pytest` **125** passed in local session.
- `python -m src.combiner.run --help` shows `--engine` and `--dry-run`.

## 2. Why this task was needed

Layer2 `simulate_combiner_numba` had been stubbed with `NotImplementedError`, blocking `run.py` / `sweep.py` / walkforward-style callers. The agreed direction is **execution-backed** Layer2 (`TradeIntent` → `simulate_trade_path`) while **preserving** the archived Numba reference for compatibility and future parity.

## 3. Actual starting state

- `simulator.py` was **stub-only** (NotImplementedError).
- Docs (`NEXT_HANDOFF`) already pointed to `COMPLETE_COMBINER_ADAPTER`.
- Legacy reference existed only under `archive/legacy_combiner/`.

## 4. Contradictions resolved

- Code vs docs: simulator is no longer “stub only”; it is **mixed** (lazy legacy + canonical export).
- `LAYER_FLOW` updated to describe dual engines.

## 5. Canonical execution contract

- `TradeIntent` carries raw signal fields; `simulate_trade_path` performs materialization, ambiguity policy, exits, PnL.
- `execution_semantics_version` stamped via policy on trade rows.

## 6. Adapter design

- `trade_intent_adapter.py`: build intent, map `TradeResult` → combiner dict, policy helper.
- `adapter.py`: sequential bar walk, selection + state hooks, no standalone R math.

## 7. Implementation summary

- Legacy: `importlib` load archive module; register in `sys.modules` for dataclass compatibility.
- Canonical: `simulate_combiner_canonical` returns same top-level keys as legacy (`trades_df`, `equity_df`, empty logs, `rejection_counts` zeros).
- CLI: `--engine canonical|legacy`, `--dry-run`.

## 8. Synthetic tests

- `tests/test_combiner_adapter.py` covers target/stop/max-hold, schema stamps, minimal `simulate_combiner_canonical` smoke.

## 9. Real-data smoke

- Not run (`smoke_not_run_reason.md`).

## 10. Legacy vs canonical parity

- `PARITY_NOT_RUN` (see `parity/`).

## 11. Layer2 / Layer3 reachability

- Layer2 legacy path restored; canonical path available.
- Layer3 not executed; walkforward import remains valid with default legacy engine.

## 12. What remains blocked

- Full parity vs legacy Numba on real matrices.
- Exit overlay V3 until canonical outputs are trusted vs panels.
- Production router / exit-management.

## 13. Decision

**`COMPLETE_COMBINER_ADAPTER_V2`**

## 14. Explicit non-runs

No WFO, mini-WFO, live/paper, SPY, broad Layer2, new strategies, Champion edits, heavy artifacts.

## 15. Recommended next step

**`COMPLETE_COMBINER_ADAPTER_V2`** — build parity harness on tiny shared slices; tighten rejection mapping; optional `ExitPlan` from YAML.
