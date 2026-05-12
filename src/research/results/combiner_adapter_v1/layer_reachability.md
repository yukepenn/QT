# Layer reachability after combiner adapter v1

## Unblocked

- `simulate_combiner_numba` / `simulate_combiner_legacy_logs` no longer raise `NotImplementedError` (legacy restored).
- `simulate_combiner_canonical` provides execution-backed Layer2 path.
- `python -m src.combiner.run --engine canonical --dry-run ...` can run in-memory (requires real data + YAML for full path).

## Still blocked / not run

- Full Layer3 WFO / mini-WFO (explicit non-run).
- Exit overlay V3 alignment: still future work once canonical combiner outputs are stable vs panels.
- Production router / exit-management integration: not started.
