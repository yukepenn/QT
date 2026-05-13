# Active Layer1 execution-backed controlled candidates (runtime)

This directory holds **combiner-loadable** `*.yaml` files produced after Layer1 sweeps and **`run_layer1_execution_backed_controlled promote --write`**.

## Rules

- **Layer2 `candidate_root`** should point here when using this library.
- **Flat layout only:** `load_candidates` reads `*.yaml` in this directory — **no** per-strategy subfolders unless the loader is extended for recursion.
- **Do not** place non-candidate YAML here (no `INDEX.yaml`, no schema-only files).
- **CSV/MD** under `src/research/results/` are audit/design only — **not** runtime truth.
- **`L1_EXECUTION_BACKED_MINIMAL_PROOF`** promotions use candidate IDs **`*_L1M_*`** and `selection.candidate_kind: minimal_proof` — these are **not** full focused-grid champions; treat as **smoke / narrow-grid** inputs unless re-promoted from larger sweeps.
