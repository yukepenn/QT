# Decision — combiner adapter v1

## Label (exactly one)

**`COMPLETE_COMBINER_ADAPTER_V2`**

## Rationale

- Canonical sequential adapter exists and is tested synthetically, but does not yet replicate full legacy matrix semantics or rejection taxonomy.
- Parity harness vs legacy on shared slices is **not** run (`PARITY_NOT_RUN`).
- Layer3 remains on default **legacy** engine until parity and operational review justify switching `run_combiner_fixed_config(engine="canonical")`.
- Exit overlay alignment is **not** automatically unblocked: needs dedicated harness on canonical trade rows.

## Recommended next step

Implement **adapter v2**: parity harness + closer rejection mapping + optional `ExitPlan` wiring from management YAML — still without WFO/live/SPY.

## Explicit non-runs (this task)

No WFO, mini-WFO, live/paper, SPY, broad Layer2 sweeps, new strategies, Champion edits, raw trade commits, router production, exit-management production.
