# Strategy Family Improvement — Gap / Failed ORB v2

## 1. What changed from v1

- Added **generic trade enrichment**: `src/research/trade_enrichment.py` (no-lookahead; ignores `*_LOOKAHEAD`).
- Upgraded diagnostics to **enriched v2/v3** outputs via `src/research/gap_failed_diagnostics.py`.
- Implemented **backward-compatible refined parameters**:
  - `gap_acceptance_failure`: optional `signal.min_gap_size_atr` / `signal.max_gap_size_atr`, alias `signal.require_vwap_context`.
  - `failed_orb`: alias `signal.require_vwap_confirmation` (overrides `require_vwap_reclaim` when set).
- Ran **mini-WFO v3** with refined Layer 1 testing grids and train-only selection.

## 2. Gap refined results

- mini-WFO v3 did **not** select a gap-only system; it selected `refined_failed_only` (`MINIWFO_FAILED_ORB_001`).
- Dec-2025 enriched diagnostics (`gap_failed_family_diagnostics_v3`) still show **gap_acceptance_failure** is the dominant loss driver in the legacy v1/v2A/v2B systems, but v3’s Dec-2025 drawdown is materially smaller than v1/v2A.

## 3. Failed ORB refined results

From mini-WFO v3:

- **Selected**: `refined_failed_only` / `MINIWFO_FAILED_ORB_001`
- **Test (0.01 slip)**: total_r ≈ **5.06**, PF_R ≈ **1.07**, maxDD_r ≈ **-17.78**
- **Cost stress**: 0.02 total_r ≈ **3.69** (survives), 0.03 total_r ≈ **0.77**

Interpretation: refined failed_orb can be **positive and cost-robust at 0.02** in this split, even if it has meaningful drawdown.

## 4. v1/v2/v3 comparison

See `src/walkforward/results/mini_wfo_comparison_v1_v2_v3.md`.

Key deltas:
- v1/v2A: positive at 0.01 but **fail at 0.02** (cost-fragile).
- v2B: **fails** outright.
- v3: **PASS** and **survives 0.02 slippage**.

## 5. Decision

**READY_FOR_REDUCED_FULL_WFO_DESIGN** (design doc only; no full WFO run yet).

Rationale:
- v3 meets the core gate: positive OOS, PF_R > 1.05, and survives 0.02 slippage.
- The gap family remains suspicious (Dec-2025 stop-out cluster in legacy runs), but v3 demonstrates a viable, more robust “core” within the same broader family area.

## 6. Next recommendation

- Write a **reduced full-WFO design doc** focused on:
  - only `failed_orb` + optionally a *refined* gap variant as a diagnostic track (not required to ship),
  - very small Layer 2 grids,
  - explicit cost-stress gates.
- Do **not** execute full rolling WFO yet in this phase.

