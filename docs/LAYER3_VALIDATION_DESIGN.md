# Layer 3 validation design (walkforward)

**Status:** Harness code exists (`src/walkforward/`); **canonicality** of reported R/PnL depends on Layer 2 still using legacy Numba until the adapter lands.

## Principles

- Layer 3 consumes **frozen** system definitions (YAML / pinned candidate sets). It does **not** select or tune parameters inside OOW windows.
- Each run should record **provenance**: `execution.semantics_version` (or policy field), strategy/candidate versions, router/management config versions, data window, slippage/commission assumptions.
- Outputs are **historical priors** after an accounting reset unless regenerated under the new execution stack.

## Not in scope until upstream is ready

- Full rolling WFO as production gate.
- Comparing old Numba Layer 3 CSVs to new canonical metrics without explicit relabeling.

See also `docs/WALKFORWARD_STATUS.md`.
