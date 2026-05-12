# Walkforward package status

**Date:** 2026-05-11

Orchestration for fixed-profile smoke, diagnosis, and mini-WFO tooling. **Trade accounting** inside combiner replays still follows **legacy Numba** until `src.combiner.run` is rewired to the execution-backed simulator described in `docs/CANONICAL_COMBINER_DESIGN.md`.

Do **not** treat historical `src/walkforward/results/**` aggregates as canonical execution truth after the reset without regeneration.

Machine-readable table: `docs/WALKFORWARD_STATUS.csv`.
