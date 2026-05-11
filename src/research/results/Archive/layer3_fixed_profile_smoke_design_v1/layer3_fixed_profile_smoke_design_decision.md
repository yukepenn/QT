# Layer3 fixed-profile smoke v1 — design decision (DESIGN ONLY — NOT RUN)

**Decision (exactly one):** **`RUN_LAYER3_FIXED_PROFILE_SMOKE`**

## Rationale (3–6 bullets)

- Profile selection is clear and grounded in fixed robust-profile OOW v1: **PA-only baseline** + **PA+GAP combined**.
- Gate design is explicit (window positivity, cost overlay sign, stability/DD flags, artifact quality gates).
- Run plan is fixed (no router, no YAML edits, no caches by default) with a defined core set (**8 runs**) and optional expansions.
- Output schema is defined to be **ChatGPT-reviewable** (bundle + source map + sanitized manifests + per-window summaries).

## Recommended next step (exactly one)

Implement the future runner (design-aligned) and execute the **CORE** smoke set only (2 profiles × 4 windows) under:

- `src/research/results/layer3_fixed_profile_smoke_v1/`

## Explicit non-runs (this task)

- No Layer3 execution
- No backtests / combiner runs
- No broad Layer2
- No WFO (mini or full)
- No live/paper
- No SPY
- No router
- No strategy / feature / YAML edits

