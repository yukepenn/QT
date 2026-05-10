# Research script organization audit (2026-05-10)

**Phase:** audit only — **no files moved.** Rationale: several scripts are referenced from tests, `PROGRESS.md`, `CHANGES.md`, `docs/ARTIFACT_POLICY.md`, and generated markdown headers. Relocating without a coordinated import/doc pass would risk broken reproducibility.

## Summary

| Category | Count | Action |
|----------|-------|--------|
| `gen_*` generators | 3 | Keep under `src/research/` |
| Diagnostics CLIs | 2+ (`gap_failed_diagnostics`, cost fragility) | Keep |
| Orchestration `run_*` | 4 | Keep (tests import `run_layer1_v2_completion`) |

## Per-script detail

Machine-readable table: `research_script_organization_audit.csv`.

### Generators (`gen_*`)

1. **`gen_batch1_audit.py`** — Builds `strategy_library_v2_batch1_audit.{csv,md}`. Documented in CHANGES/PROGRESS. **Keep** `src/research/`.
2. **`gen_batch1_cost_fragility_diagnostics.py`** — Builds `batch1_cost_fragility_diagnostics_v1/`. **Keep**.
3. **`gen_batch1_tuned_v1_cost_diagnostics.py`** — Builds `batch1_tuned_v1_cost_diagnostics/`. **Keep**.

### Diagnostics

- **`gap_failed_diagnostics.py`** — Imported by `tests/test_gap_failed_diagnostics.py`. **Do not move** without test + doc updates.
- **`check_selected_candidates_fast_context.py`** / **`check_strategy_fast_parity.py`** — Validation entrypoints. **Keep** top-level `src/research/` for discoverability.

### Orchestration

- **`run_layer1_v2_completion.py`** — Tested (`test_run_layer1_v2_completion.py`). **Keep**.
- **`run_batch1_layer1_sweeps.py`**, **`run_batch1_jan_smokes.py`**, **`run_layer1_focused.py`** — CLI orchestrators; optional future home `src/research/scripts/` only after grep for hard-coded paths and doc refresh.

### Hygiene

- **`curated_artifact_sanity.py`** — Small maintainer utility. **Keep** next to `results/`.

## Proposed future structure (not executed)

- `src/research/scripts/` — long-running sweep orchestrators (`run_*` not imported elsewhere).
- `src/research/diagnostics/` — one-off diagnostic writers not imported by tests.

**Default:** keep all current paths until a dedicated refactor task updates tests and documentation in one commit.
