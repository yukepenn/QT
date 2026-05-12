# Baseline inventory — combiner_adapter_parity

**Captured at:** start of this task (git tip before new commit documented in `baseline_inventory.csv`).

## Summary

- **Tip (pre-change):** `65f4ecf29fe051c4aa04e59f70cf70b387330195` — `Research(combiner): add canonical execution adapter`.
- **Prior NEXT_HANDOFF decision:** `COMPLETE_COMBINER_ADAPTER_V2` (superseded by this parity pass for handoff clarity).
- **`simulator.py`:** **Mixed** — lazy `legacy_reference` Numba (`simulate_combiner_numba` / `simulate_combiner_legacy_numba`) plus execution-backed `simulate_combiner_canonical` / `simulate_combiner_execution_backed` (lazy import of `adapter.simulate_combiner_canonical`). Unknown `--engine` values raise `ValueError` via `normalize_combiner_engine_label`.
- **Docs stale vs code:** `docs/LAYER_FLOW.md` still implied Layer 3 blocked by a simulator stub; **fixed** in this task. NEXT_HANDOFF still used legacy-only decision labels; **aligned** to parity vocabulary (`execution_backed`, `legacy_reference`).

## Imports

See `import_status.md` (all listed modules **OK** at capture time).

## Tests

- **Before:** 125 collected (see prior handoff).
- **After (expected):** 133 with `tests/test_combiner_adapter_parity.py`.
