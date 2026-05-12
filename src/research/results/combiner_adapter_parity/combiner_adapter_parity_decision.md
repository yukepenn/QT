# Decision — combiner_adapter_parity

## Label (exactly one)

**`COMPLETE_COMBINER_ADAPTER_PARITY`**

## Rationale

- Synthetic parity run shows **legacy_reference vs execution_backed drift** on the shared toy matrix (`parity_summary.csv`: trade counts differ); this must be reconciled before treating parity as production-grade.
- Real QQQ **execution_backed** smoke was **not** run in-repo (no `data/raw/ibkr` bars committed); only default `smoke/NOT_RUN` plus optional local `--try-real-smoke`.
- **Exit overlay on execution path** should wait until parity is understood on real slices or a dedicated harness exists — not `RESUME_EXIT_OVERLAY_ON_EXECUTION_PATH` yet.
- Layer3 imports succeed; default combiner engine remains **legacy_reference** by design until parity sign-off.
- Naming discipline: no new `*_v2` / `*_v3` roots; only `combiner_adapter_parity/` added as specified.

## Recommended next step

Build a **small real-data parity harness** (same bars, same candidates, both engines) and reconcile the top drift drivers (cursor semantics, rejection mapping, target materialization) — still **no WFO**, **no router production**, **no exit-management production**.

## Explicit non-runs (this task)

No WFO, mini-WFO, live/paper, SPY research, broad Layer2 sweeps, new strategies, Champion YAML edits, raw trade commits, production router/exit-management, scalp/short work.
