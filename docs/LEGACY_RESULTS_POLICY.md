# Legacy results policy

**Date:** 2026-05-11

## Historical priors

Prior Layer 1 / Layer 2 / Layer 3 / Champion curated outputs under `src/research/results/**`, `src/combiner/results/**`, `src/walkforward/results/**`, and related markdown bundles are **historical priors** from earlier accounting stacks (including Numba fast paths and legacy combiner kernels).

They are **not** authoritative for the semantics of `src.execution.path.simulate_trade_path` after the architecture reset unless explicitly regenerated under the new stack.

## Comparison rules

- Do **not** compare old R or PnL directly to new canonical metrics without **labeling** the accounting version (e.g. `legacy_numba_fast` vs `execution_semantics: 1.0`).
- Future reports must record **`execution.semantics_version`** (or equivalent policy stamp), data window, and cost assumptions.

## Code vs results

- **Canonical code** lives under `src/execution/` and the thin adapters documented in `docs/MODULE_OWNERSHIP.md`.
- **Legacy Numba** may still be invoked for reference (`--legacy` sweep, combiner legacy simulator) until migrated.
- **Canonical sweep rows** (`run_canonical_sweep`, `--smoke`) must carry `engine=canonical_reference` and `canonical_or_legacy=canonical`. **Legacy sweep** rows must use `engine=legacy_numba_fast` and `canonical_or_legacy=legacy_prior` if exported.
- **Research** should remain thin runners + curated aggregates; do not mix large raw artifacts into `src/`.
