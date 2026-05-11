# Global Layer 2 design — QQQ 2023–2024 v2 (post feature hardening)

## Purpose

Run combiner economics on the **Layer-2-ready core** (`selected_candidates_l2_core`) derived from Global Layer 1 v2, using buckets aligned with global strategy families (opening trap, VWAP, indicator completion, PA).

## Candidate root

- **YAML root:** `src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates`
- **Rationale:** Full Layer 1 strict selection again produced **81** YAMLs (one over the historical Layer 2 prerun cap of 80). The l2_core builder caps at **80**, prefers unique `pure_signal_hash` per strategy (up to 4), and preserves family coverage — **66** candidates for this run.

## Executable configs

- **Base:** `src/combiner/configs/layer2_qqq_global_2023_2024_v2.yaml`
- **Sweep:** `src/combiner/configs/layer2_sweep_qqq_global_2023_2024_v2.yaml`
- **Emitter:** `src/research/emit_global_layer2_v2_configs.py` (regenerates YAML from l2_core CSV + diversity)

### Candidate sets (dynamic)

- `opening_trap_core` — `failed_orb`, `gap_acceptance_failure`, `orb_continuation` (and other opening-trap names **only if** present in l2_core)
- `vwap_core` — `vwap_reclaim_reject`, `vwap_trend_pullback`, `vwap_reversal` if present
- `indicator_completion_core` — oscillator / MACD / SuperTrend / RSI / squeeze / exhaustion names if present
- `pa_core` — `pa_*` strategies in l2_core
- `all_strict_l2_core` — full capped universe
- `all_behavior_diverse` — `max_per_strategy: 1`
- `all_low_turnover` — optional `candidate_ids` list (trades ≤ 250 on 2023–2024 in-sample) when non-empty
- `long_short_mixed` — **omitted** unless strict short activity exists (`n_short_signals` > 0 in diversity merge). This v2 l2_core had **0** such rows.

### Sweep grid (representative)

- `candidate_set`: non-empty sets only (see YAML)
- `top_per_strategy`: 1, 2
- `system.max_trades_per_day`: 1, 2
- `system.daily_max_loss_r`: -1.5, -2.0, -3.0
- `system.cooldown_after_loss_minutes`: 0, 15
- `conflict.priority_policy`: `metadata_priority`, `score_adjusted_priority`

## Gates

| Gate | Full strict root | l2_core |
|------|------------------|---------|
| YAML count ≤ 80 | **NO** (81) | **YES** (66) |
| ≥3 families | YES (15) | YES (15) |
| Fast-context | YES | YES |
| Diversity script | YES | YES |

**Automated prerun gate** in `run_global_layer1.py` still evaluates the **full** strict export (81) and therefore reports **NO** for historical compatibility. Layer 2 work should use the **l2_core** row in `global_layer2_gate_decision_v2.md`.

## Diagnostics smoke (local)

- Command: `python -m src.combiner.run ... --diagnostics-only --candidate-set all_strict_l2_core` on **2023-01-01 → 2023-03-31**, output `src/combiner/results/layer2_qqq_global_2023_2024_v2/diagnostics/`.
- Summary (curated, committed separately): `layer2_global_diagnostics_smoke_q1_2023.md` under `src/research/results/`.
- **Full combiner sweep + cost stress** for v2 is **not** committed in this change set (time + artifact policy).

## Decision

- **Engineering:** `PROCEED_TO_GLOBAL_LAYER2_SWEEP` when ready (configs validate; l2_core gates satisfied).
- **This commit:** design + configs + Q1 diagnostics smoke summary only.
