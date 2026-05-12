# Decision — exit overlay on execution path

## Label (exactly one)

**`USE_EXECUTION_BACKED_FOR_RESEARCH_AND_REBUILD_LAYER1_2_3`**

## Rationale (bullets)

- **No third PnL engine:** the runner only orchestrates **`simulate_combiner_canonical`** and **`simulate_trade_path`**; validation + tests enforce unsupported overlays are reported, not faked.
- **Contract-supported overlays did not improve** the champion slice in a consistent way: **max-hold tighten** and **no-followthrough** materially reduced **`total_r`** vs baseline on smoke and long-span repo coverage; **trend_swing_2r** is only mildly interesting on PA-only smoke.
- **Advanced management is blocked on the execution contract:** **trail-after-1R** and **runner** overlays are correctly classified **`unsupported_in_current_execution_contract`** — extending the contract should wait until Layer1/2/3 are rebuilt with execution-backed accounting as the default spine.
- **Execution-backed path is stable enough** to proceed with a **controlled Layer1/2/3 rebuild** under **`src/execution/`** as the single accounting truth, using this diagnostic folder as evidence for what *not* to bolt on prematurely.

## Recommended next step (exactly one)

**`USE_EXECUTION_BACKED_FOR_RESEARCH_AND_REBUILD_LAYER1_2_3`**

## Explicit non-runs

- No WFO / mini-WFO / live / paper.
- No SPY sweeps, broad Layer2 sweeps, Global Layer1, router integration, scalp/short research.
- No edits to Champion YAMLs; no deletion/archive of legacy trees.
- No promotion of overlays into **`src/management/`** in this task.
- **Optional** `primary_mtp2_meta` / **`CCI_EXTREME_SNAPBACK_003`** third-candidate run **skipped** (incremental diagnostic value vs runtime).
