# Fixed robust-profile OOW v1 — decision (RUN)

**Decision (exactly one):** **`PROCEED_TO_LAYER3_FIXED_PROFILE_SMOKE_DESIGN`**

## Rationale (3–6 bullets)

- Locked profiles remain **positive across** `early_oow`, `insample_ref`, `late_oow`, and `full_available` for the main candidates (**PA-only**, **PA+GAP**, and **primary core**).
- **PA-only** is the cleanest baseline with the strongest late-OOW result in this fixed-profile validation.
- **PA+GAP (mtp2)** is a credible combined profile: it preserves late-OOW positivity while improving early/insample totals versus PA-only.
- Adding **CCI** (primary core) remains positive, but late-OOW is **weaker** than PA-only / PA+GAP, so it should be treated as an interpretability/breadth baseline rather than the default profile.
- Exit/slip overlay scenarios were produced for fixed profiles; stress reduces totals but does not overturn the headline conclusion.

## Recommended next step (exactly one)

Design (not execute) a **Layer3 fixed-profile smoke** around:

- `pa_only_mtp1_meta`
- `pa_gap_mtp2_meta`

Use the same windows and keep constraints unchanged (no broad grids, no router, no YAML edits).

## Explicit non-runs

- No broad Layer2
- No mini/full WFO
- No live/paper
- No SPY
- No strategy / feature / candidate-YAML edits
- No signal-cache usage (`--use-signal-cache`)

