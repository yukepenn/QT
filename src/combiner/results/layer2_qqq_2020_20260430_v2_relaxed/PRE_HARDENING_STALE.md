# Pre-hardening / stale results

This Layer 2 result root (`layer2_qqq_2020_20260430_v2_relaxed`) was produced **before** research platform hardening **Commits A–D** were complete on `main`.

- **Sweep results, config-level `top_unique_*`, cost stress, and any summaries** reflect the code and metrics of that era, not necessarily the hardened execution + feature + validation + behavior/cost diagnostics stack.
- **Behavior-unique** and **cost-as-R** postprocess tooling now exists on `main`, but trustworthy research should **rerun from a fresh Layer 1 candidate library** after post-hardening Layer 1.
- **Do not use these rankings to justify Layer 3** without a full post-hardening pipeline rerun.

See `src/research/results/rerun_plan_after_hardening.md` and `hardening_closeout_20260505.md`.
