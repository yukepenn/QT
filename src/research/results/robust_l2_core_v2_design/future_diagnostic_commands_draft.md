# Future diagnostic commands (DRAFT — DESIGN ONLY — NOT RUN)

These are **draft command shapes** for the next task. They are intentionally written as a plan, not executed here.

## 1) Validate artifacts (should already pass)

```bash
python -m src.research.validate_research_artifacts \
  --root src/research/results/robust_l2_core_v2_design \
  --csv-only \
  --output src/research/results/robust_l2_core_v2_design/design_artifact_validation.csv
```

## 2) Materialize candidate sets (if runner requires explicit `--candidates`)

Source-of-truth is:

- `src/research/results/robust_l2_core_v2_design/candidate_sets_design.csv`

If the Layer2 runner cannot accept a “candidate set name” directly, the next task should:

- load the CSV
- expand each `candidate_set` into a concrete candidate-id list
- invoke the runner with `--candidates <...>`

## 3) Run the small diagnostic (placeholder)

**IMPORTANT:** the exact runner entrypoint/flags depend on the repo’s combiner CLI used in the next task.

The intended shape is:

- candidate_set axis (7 sets)
- window axis (3 windows)
- tiny risk grid (2×2×2)

Output root:

- `src/research/results/robust_l2_core_v2_diagnostic_v1/`

## Explicit non-runs (this task)

Nothing in this file was executed.

