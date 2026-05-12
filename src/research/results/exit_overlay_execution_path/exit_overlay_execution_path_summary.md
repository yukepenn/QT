# Exit overlay on execution path — summary

**Decision:** `USE_EXECUTION_BACKED_FOR_RESEARCH_AND_REBUILD_LAYER1_2_3` (see `exit_overlay_execution_path_decision.md`).

**What ran:** Champion candidates from `Archive/.../selected_candidates`, QQQ, **`execution_backed`** baseline via `simulate_combiner_canonical`, overlays via per-trade **`simulate_trade_path`** only. **Smoke:** Jan 2024. **Repo coverage:** full QQQ span in `data/raw/ibkr` (~2020–2026 on this checkout).

**Supported overlays:** baseline, max-hold cap 60, NFT 5-bar / 0.05R, trend swing 2R. **Unsupported:** trail-after-1R, runner (documented in `overlay_unsupported.csv`).

**Outcome:** contract-valid overlays mostly **hurt** aggregate R / PF on this slice; no immediate promotion to `src/management/`. Next step is a **controlled Layer1/2/3 rebuild** with execution-backed accounting as default, before extending **`ExitPlan`** for richer management.
