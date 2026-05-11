# Layer 2 global v2 — diagnostics-only smoke (QQQ 2023 Q1)

## Command (representative)

`python -m src.combiner.run` with:

- `--candidate-root` → `src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates`
- `--config` → `src/combiner/configs/layer2_qqq_global_2023_2024_v2.yaml`
- `--asset equity --symbol QQQ --start 2023-01-01 --end 2023-03-31`
- `--diagnostics-only --candidate-set all_strict_l2_core --top-per-strategy 4`
- `--output-root src/combiner/results/layer2_qqq_global_2023_2024_v2 --tag diag_smoke_q1`

## Key stdout metrics

- **Candidates in diagnostics:** 66  
- **Bars (N):** 24 180  
- **Total valid signals (union):** 2 072  
- **Wall time (diagnostics block):** ~0.78 s for overlap/conflict matrices after precompute  
- **Zero-signal candidates:** none reported  

## Artifacts (local / not committed)

- `src/combiner/results/layer2_qqq_global_2023_2024_v2/diagnostics/` — includes `candidate_precompute_profile.csv`, overlap/conflict CSVs, `feature_store_stats.json` (see `ARTIFACT_POLICY.md`).

## Interpretation

Precompute + overlap pipeline succeeds on the l2_core universe for a short window; suitable as a smoke before a full 2023–2024 sweep.
