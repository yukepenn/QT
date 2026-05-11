# Future Layer3 fixed-profile smoke commands (DESIGN ONLY — NOT RUN)

This file defines the **command shape** for a future prompt that actually executes Layer3 smoke. It is intentionally **not executable in this task**.

## Assumptions

- Runner will be implemented as a new script (future task), likely mirroring `src/research/run_fixed_robust_profile_oow.py`.
- Inputs (profiles + windows) come from the fixed-profile OOW v1 artifacts and this design root.

## Proposed future output root

- `src/research/results/layer3_fixed_profile_smoke_v1/`

## Proposed command shape

### 1) Dry-run (plan + config materialization only)

```bash
python -m src.research.run_layer3_fixed_profile_smoke dry-run ^
  --input-fixed-root src/research/results/fixed_robust_profile_oow_v1 ^
  --design-root src/research/results/layer3_fixed_profile_smoke_design_v1 ^
  --output-root src/research/results/layer3_fixed_profile_smoke_v1 ^
  --include-class CORE
```

### 2) Run (execute)

```bash
python -m src.research.run_layer3_fixed_profile_smoke run ^
  --input-fixed-root src/research/results/fixed_robust_profile_oow_v1 ^
  --design-root src/research/results/layer3_fixed_profile_smoke_design_v1 ^
  --output-root src/research/results/layer3_fixed_profile_smoke_v1 ^
  --include-class CORE ^
  --skip-existing ^
  --stop-on-fail ^
  --no-signal-cache
```

### 3) Postprocess

```bash
python -m src.research.run_layer3_fixed_profile_smoke postprocess ^
  --output-root src/research/results/layer3_fixed_profile_smoke_v1
```

### 4) Curated artifact validation

```bash
python -m src.research.validate_research_artifacts ^
  --root src/research/results/layer3_fixed_profile_smoke_v1 ^
  --csv-only ^
  --exclude-subdirs local_runs,local_configs ^
  --output src/research/results/layer3_fixed_profile_smoke_v1/layer3_smoke_artifact_validation.csv
```

## Notes / constraints

- Keep raw `local_runs/**` local-only and uncommitted.
- Ensure manifests are sanitized for absolute paths (write `*_sanitized.csv`).
- Do not interpret overlapping window sums as independent economics.

