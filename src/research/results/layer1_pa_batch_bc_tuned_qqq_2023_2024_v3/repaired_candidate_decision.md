# Repaired candidate decision — PA Batch B/C tuned v3

## Inputs

- Raw audit: `src/research/results/pa_batch_bc_raw_signal_diversity_v3/raw_signal_diversity_summary.md`
- Repaired root: `selected_candidates_repaired/` (3× close-trend + 3× climax YAMLs, strict rows chosen for **distinct `pure_signal_hash`** where possible)
- Diversity re-check: `src/research/results/pa_batch_bc_candidate_signal_diversity_repaired_v3/strategy_diversity_summary.csv` → **3 / 3** unique hashes **per strategy**
- Fast context: `selected_candidates_repaired/candidate_fast_context_check.md` → **all `ok`**

## Decision

### **RUN_LAYER2_REPAIRED_V3**

Rationale:

1. **≥2** close-trend `pure_signal_hash` values in the repaired export (**3**).
2. **≥1** climax path required; repaired export has **3** distinct climax hashes (not capped).
3. Fast-context **passed**.
4. Raw audit proved **H1 (selector)** for climax; repair is evidence-backed, not a silent strategy change.

## Explicit non-runs

- **mini-WFO / full WFO / live:** still **not** executed.
