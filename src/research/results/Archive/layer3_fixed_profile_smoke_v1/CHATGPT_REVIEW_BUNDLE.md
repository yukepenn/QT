# CHATGPT_REVIEW_BUNDLE — layer3_fixed_profile_smoke_v1 (CORE)

## 1. Git tip

- `7063b68 Research(layer3): design fixed smoke v1`

## 2. CORE execution

- Profiles: `pa_only_mtp1_meta`, `pa_gap_mtp2_meta`
- Windows: `early_oow`, `insample_ref`, `late_oow`, `full_available`
- Runs discovered: **8**

## 3. Per-window total_r (Layer3)

| profile_id | early_oow | insample_ref | late_oow | full_available |
|---||---||---||---||---|
| `pa_gap_mtp2_meta` | 60.95 | 52.27 | 18.77 | 131.99 |
| `pa_only_mtp1_meta` | 45.14 | 37.97 | 21.49 | 104.59 |

## 4. Fixed OOW comparison

See `fixed_oow_comparison.csv` (should match within float noise if same data/code).

## 5. Gates

See `gate_results.md` / `gate_results.csv`.

## 6. Cost overlay

See `exit_slip/layer3_exit_slip_scenarios.csv` — target_limit_stress must stay positive for full_available (gate).

## 7. Complementarity

See `complementarity/profile_candidate_contribution.csv` for PA+GAP.

## 8. Decision

**RUN_OPTIONAL_LAYER3_BASELINE_ABLATION**

## 9. Non-runs

No optional profiles; no broad L2/WFO/live/SPY.
