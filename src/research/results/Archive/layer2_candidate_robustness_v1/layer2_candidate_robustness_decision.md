# Layer2 candidate robustness — decision (v1, full l2_core)

## Decision label (exactly one)

**`CREATE_ROBUST_L2_CORE_V2_DESIGN`**

## Rationale (3–6 bullets)

- **66 / 66** l2_core YAMLs now have singleton combiner replays on **early_oow**, **insample_ref**, and **late_oow** (**198** `candidate_oow_metrics.csv` rows, all `status=OK`).
- **Ten** candidates meet **`ROBUST_POSITIVE`** under the v1 heuristic, spread across **`indicator`** (CCI **002**–**003**), **`opening_trap`** (**GAP_ACCEPTANCE_FAILURE_001**–**004**), and **`pa`** (**PA_BUY_SELL_CLOSE_TREND_001**–**004**) — **three** audit families, not only VWAP/indicator.
- A **research-only** robust-core dry-run manifest passes the scripted gates (**≥6** KEEP_CORE, **≥2** families, no catastrophic OOW in KEEP_CORE, family share cap): see `robust_core_dry_run/`.
- **VWAP** and most **indicator** names remain weak or mixed; failures on those families are **not** representative of the entire l2_core — **gap acceptance** and **PA buy/sell close trend** carry cross-window strength in this audit.
- **Side-flip** remains a **non-executable sign proxy**; **`MULTI_DAY_LEVEL_TRAP_*`** joins **`MACD_MOMENTUM_TURN_003`** on the anti-predictive watchlist — **not** production shorts.
- **`REVISIT_LAYER1_SELECTION_CRITERIA`** is **not** the primary branch while a gated multi-family dry-run exists; Layer1 should still be reviewed later for **redundancy** (e.g. identical GAP metrics across four YAML stems) and **2023–2024 specificity**, but it is no longer blocking a **design-only** robust-core v2 narrative.

## Recommended next step (exactly one)

Author **`robust l2_core v2` design** (documentation + selection rules only): start from `robust_core_dry_run/selected_candidates_manifest.csv`, dedupe highly redundant YAMLs (GAP quadruplet), and define how v2 core coexists with watchlist/drop buckets — **still no** Layer2 sweep, **no** parameter tuning on OOW, **no** YAML edits in this step unless a separate explicitly scoped task.

## Explicit non-runs

mini-WFO; full WFO; live/paper; SPY; Global L1 rerun; broad Global L2 grid; new strategies; new feature primitives; edits to selected candidate YAMLs; combiner `regime_router`; hard regime filters; production short routing; OOW parameter optimization; `--use-signal-cache` on unsafe OneDrive roots; committing `local_runs/` or raw `trades.csv` / heavy artifacts; `git add .`
