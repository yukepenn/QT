# PA Batch B/C — tuned v3 plan (post–Layer 2 v2)

## 1. Why v2 Layer 2 failed the readiness gate

Reduced Layer 2 on tuned v2 strict candidates (`layer2_qqq_pa_batch_bc_tuned_v2_2023_2024/`) met fixed-run economics but **failed portfolio readiness**:

- **`behavior_unique` collapsed to 1** strong trade-sequence hash in the postprocess slice (climax-only detailed paths dominated `top_runs`).
- **Leaderboard skew:** `combiner_score` ranked compact **`pa_climax`** configs above **`pa_buy_sell_close_trend`** despite large **`total_r`** on close-trend / core portfolios.
- **Strict PF_R @ 0.02** for the representative detailed path was **borderline / below 1.05** while aggregate PF still looked OK.

## 2. Candidate duplication / behavior collapse

Layer 1 v2 exported **5×** `pa_climax_reversal` strict YAMLs whose **signal timestamps and counts matched** (parameter-only deltas → **identical `pure_signal_hash`** after first-signal-per-session thinning).

Close-trend top five shared **very similar** signal mass (high overlap); differences were often **risk/target / hold** rather than entry timing diversity.

## 3. Close-trend diagnosis

- **Strength:** high **`total_r`** at baseline slippage, healthy PF in fixed runs.
- **Risk:** **dense signals** → cost and **`max_hold`** sensitivity; Layer 2 interpretation flagged **max-hold / turnover** as the main fragility axis.

## 4. Climax diagnosis

- **Strength:** clean PF on small **n**; positive fixed top1.
- **Failure mode:** **grid axes in v2 did not move the boolean candidate mask** enough across the top five rows → **five “candidates”, one signal path**.

## 5. What tuned v3 will change

- **Climax `*_tuned_v3.yaml`:** emphasize **signal-changing** axes (`climax_score_min`, `bear_context_min`, `max_dist_below_vwap_atr`, entry window, `bar_range_expansion_min`, optional **`use_bar_range_expansion`**, `stop_mode`) with a **full grid ≤ 1500**.
- **Close-trend `*_tuned_v3.yaml`:** modest **entry window**, **body/trend** filters, **`require_vwap_side`**, **`target_r`**, **`max_hold_minutes`** grid to probe **hold/cost** vs **PF** without reverting to tuned v1 ultra-short holds.
- **Research tooling:** generic **`candidate_signal_diversity.py`** (+ optional **`select_diverse_candidates.py`**) so Layer 1 exports can be **verified for `pure_signal_hash` diversity** before Layer 2.

## 6. What tuned v3 will not change

- **No new strategies**, no new Brooks primitives, **no backtest engine** edits, **no silent signal-logic edits** in strategy plugins.
- **No** change to `select_candidates.py` contract; diversification helper is **opt-in post-processing**.

## 7. Candidate diversity objective

Per strategy among the top strict exports:

- **≥ 2 distinct `pure_signal_hash` values** (timestamp + side path) across the selected set when possible.
- If impossible after grid search, **document** the axis shortage and keep **≤5** best rows with explicit **duplicate_fill** flags in the diversity helper.

## 8. Layer 1 v3 plan

1. Author **`pa_*_tuned_v3.yaml`** grids (raw ≤ 1500 each).
2. **`pa_gate_diagnostics.py` preflight** (first combo) → `pa_batch_bc_gate_diagnostics_v3_preflight/`.
3. **`run_layer1_focused.py`** with `--testing-config-override` for both strategies, tag **`layer1_pa_batch_bc_tuned_qqq_2023_2024_v3`**, output root **`layer1_pa_batch_bc_tuned_qqq_2023_2024_v3/`**.
4. **`select_candidates.py --manifest`** with strict thresholds (see v2 `candidate_selection_config.md` pattern).
5. **`candidate_signal_diversity.py`** on **`selected_candidates/`**; if duplicates dominate, run **`select_diverse_candidates.py`** → `selected_candidates_diverse/`.

## 9. Conditional Layer 2 v3 plan

**Only if** Layer 1 v3 decision is **`PROCEED_TO_PA_BATCH_BC_REDUCED_LAYER2_V3`**:

- Narrow **96-combo** sweep (`layer2_sweep_qqq_pa_batch_bc_tuned_v3_2023_2024.yaml`) on **`selected_candidates_diverse`** if present and valid, else strict folder.
- Same style gates as v2: **behavior ≥ 2** preferred, **0.02** economics, no single-family overclaim.

## 10. Explicit non-runs

- **mini-WFO / full WFO / live / paper:** not in this phase.
