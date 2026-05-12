# Active Layer1 execution-backed controlled candidates (runtime)

This directory holds **combiner-loadable** `*.yaml` files produced **after** a controlled Layer1 sweep and **`run_layer1_execution_backed_controlled promote --write`**.

## Rules

- **Layer2 `candidate_root`** should point here when using this library.
- **Flat layout only:** `load_candidates` reads `*.yaml` in this directory — **no** per-strategy subfolders unless the loader is extended for recursion.
- **Do not** place non-candidate YAML here (no `INDEX.yaml`, no schema-only files).
- **CSV/MD** under `src/research/results/` are audit/design only — **not** runtime truth.

Until a real promotion run, this folder may contain only this `README.md`.
